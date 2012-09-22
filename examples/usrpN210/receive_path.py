'''
Created on Jul 18, 2011

@author: rafik
'''
from gnuradio import gr
from gnuradio import eng_notation
#from gnuradio import usrp
from gnuradio   import uhd  
from gnuradio import blks2
import copy
import sys

from gnuradio.wxgui import fftsink2
from gnuradio.wxgui import constsink_gl

import ieee_pkt_receiver

#in this version there are not use of pick_rx_bitrate
#from pick_bitrate import pick_rx_bitrate

from bpsk_demodulator import bpsk_demodulator

from gnuradio.wxgui import fftsink2
n2s = eng_notation.num_to_str 
    

class receive_path(gr.hier_block2):
    def __init__(self, principal_gui, rx_callback, options):
        gr.hier_block2.__init__(self, "receive_path",
                                gr.io_signature(0,0,0), # the 1,1 indicate the minimum, maximum  stream in input
                                gr.io_signature(0,0,0))                    # the 0,0 indicate the minimum, maximum  stream in output
        
        #local setup usrp source creat self.usrp source 
        self._setup_usrp_source(options)
        
        options = copy.copy(options) # Make copy of the received options
        
        self._verbose           = options.verbose
        self._bitrate           = options.data_rate            # The bit rate transmission
        self._samples_per_symbol= options.samples_per_symbol # samples/sample
        
        self._rx_callback   = rx_callback        #This callback is fired (declanche) when there's packet is available
        self.demodulator    = bpsk_demodulator(principal_gui, options)      #The demodulator used 
        
        #Designe filter to get actual channel we want
        sw_decim = 1
        
        #Create the low pass filter 
        chan_coeffs = gr.firdes.low_pass (1.0,                                  #gain
                                          sw_decim * self._samples_per_symbol,  #sampling rate
                                          1.0,                                  #midpoint of trans band
                                          0.5,                                  #width of trans band
                                          gr.firdes.WIN_HAMMING)                #filter type
        self.channel_filter = gr.fft_filter_ccc(sw_decim, chan_coeffs)
        

        self.packet_receiver = ieee_pkt_receiver.ieee_pkt_receiver_868_915(self, 
                                                                   gui = principal_gui,
                                                                   demodulator = self.demodulator,
                                                                   callback = rx_callback,
                                                                   sps = self._samples_per_symbol,
                                                                   symbol_rate = self._bitrate,
                                                                   threshold = -1) 
            
        #Carrier Sensing Block (ecoute du canal)
        alpha = 0.001
        # Carrier Sensing with dB, will have to adjust
        thresh = 30 
        #construct analyser of carrier (c'est un sink) 
#        self.probe = gr.probe_avg_mag_sqrd_c(thresh, alpha)
        
        #display information about the setup
        if self._verbose:
            self._print_verbage()
        
        #self.squelch = gr.pwr_squelch_cc(50, 1, 0, True)
        #connect the input block to channel filter
        #connect the blocks with usrp, the  self.usrp is created in _setup_usrp_source
        self.squelch = gr.pwr_squelch_cc(50, 1, 0, True)
        
#        self.wxgui_constellationsink2_0_0 = constsink_gl.const_sink_c(
#            principal_gui.GetWin(),
#            title="Constellation Plot",
#            sample_rate= options.samp_rate,
#            frame_rate=5,
#            const_size=2048,
#            M=2,
#            theta=0,
#            loop_bw=6.28/100.0,
#            fmax=0.05,
#            mu=0.5,
#            gain_mu=0.001,
#            symbol_rate=options.samp_rate/options.samples_per_symbol,
#            omega_limit=0.0001,
#        )
#        principal_gui.Add(self.wxgui_constellationsink2_0_0.win)
        '''For stream of bits'''
#        self.wxgui_fftsink2_0 = fftsink2.fft_sink_c(
#            principal_gui.GetWin(),
#            baseband_freq=options.freq,
#            y_per_div=10,
#            y_divs=10,
#            ref_level=10,
#            ref_scale=2.0,
#            sample_rate= 0.5e6,
#            fft_size=1024,
#            fft_rate=30,
#            average=False,
#            avg_alpha=None,
#            title="FFT Plot",
#            peak_hold=False,
#        )
#        principal_gui.Add(self.wxgui_fftsink2_0.win)
        #self.connect(self.u, self.demodulator, self.wxgui_fftsink2_0)
        '''End for stream of bits'''
        
        #Reception of packets 
        self.connect(self.u, self.packet_receiver)
                
        #self.connect(self.channel_filter, self.packet_receiver)
        #self.connect(self, self.packet_receiver)
        
    def bitrate(self):
        return self._bitrate

    def samples_per_symbol(self):
        return self._samples_per_symbol

    def carrier_sensed(self):
        """
        Return True if we think carrier is present.
        """
        #return self.probe.level() > X
        return self.probe.unmuted()

    def carrier_threshold(self):
        """
        Return current setting in dB.
        """
        return self.probe.threshold()

    def set_carrier_threshold(self, threshold_in_db):
        """
        Set carrier threshold.

        @param threshold_in_db: set detection threshold
        @type threshold_in_db:  float (dB)
        """
        self.probe.set_threshold(threshold_in_db)       
            
    
    def _setup_usrp_source(self, options):
        
        print "******************************************************Reception parameters***************************"
        print "USRP Adress: ", options.address
        print "Transmission Freqeuncy: ", eng_notation.num_to_str(options.freq)
        print "Sample rate or (Freqeuncy Sampling): ", eng_notation.num_to_str(options.samp_rate)
        print "Samples per symbol: ", options.samples_per_symbol
        print "Data rate : ", eng_notation.num_to_str(options.data_rate)
        print "Gain  : ", options.gain
        print "*******************************************************Reception parameters************************"
                        
        self.data_rate = options.data_rate
        self.samples_per_symbol = options.samples_per_symbol
        #self.usrp_decim = int (64e6 / self.samples_per_symbol / self.data_rate)
        #self.fs = self.data_rate * self.samples_per_symbol
        payload_size = 128  # bytes
        samp_rate= options.samp_rate
        
        u = uhd.usrp_source(
            device_addr=options.address, 
            stream_args=uhd.stream_args(
            cpu_format="fc32",
            channels=range(1),
            ),
        )
        u.set_subdev_spec("A:0", 0)
        u.set_samp_rate(samp_rate)
        u.set_center_freq(options.freq, 0)
        u.set_gain(options.gain, 0)
        
        self.u = u
        
        #the bitrate option is initialised to value
        self.rs_rate = options.data_rate
        
        #Hard initialisation of bits per symbol
        self.bits_per_symbol = 1
        
        
    
    def _print_verbage(self):
        """
        Prints informations about the receive path
        """
        print "\nReceive Path:"
        print "modulation:     %s"      % ("BPSK")
        print "bitrate:        %sb/s"   % (eng_notation.num_to_str(self._bitrate))
        print "sample/symbol:  %.4f"    % (self._samples_per_symbol)
        
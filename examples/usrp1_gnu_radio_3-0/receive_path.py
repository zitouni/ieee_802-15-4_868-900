'''
Created on Jul 18, 2011

@author: rafik
'''
from gnuradio import gr
from gnuradio import eng_notation
from gnuradio import usrp
from gnuradio import blks2
import copy
import sys

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
        self._bitrate           = options.rate            # The bit rate transmission
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
        self.probe = gr.probe_avg_mag_sqrd_c(thresh, alpha)
        
        #display information about the setup
        if self._verbose:
            self._print_verbage()
        
        #self.squelch = gr.pwr_squelch_cc(50, 1, 0, True)
        #connect the input block to channel filter
        #connect the blocks with usrp, the  self.usrp is created in _setup_usrp_source
        self.squelch = gr.pwr_squelch_cc(50, 1, 0, True)
        self.connect(self._usrp,  self.packet_receiver)
        
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
        #create USRP
        self._usrp = usrp.source_c(which= options.which, decim_rate = options.decim_rate)
        if options.rx_subdev_spec is None:
           options.rx_subdev_spec = usrp.pick_rx_subdevice(self._usrp)
               
        self._subdev = usrp.selected_subdev(self._usrp, options.rx_subdev_spec)
        
        adc_rate = self._usrp.adc_rate()
        
        mux = usrp.determine_rx_mux_value(self._usrp, options.rx_subdev_spec)
        self._usrp.set_mux(mux)
        tr = self._usrp.tune(0, self._subdev, options.freq)
        if not (tr):
            print "Failed to tune to center frequency!"
        else:
            print "Center frequency:", n2s(options.freq)
        if options.gain is None:
            g = self._subdev.gain_range();
            options.gain = float(g[0]+g[1])/2.0
        self._subdev.set_gain(options.gain)
        
        #the bitrate option is initialised to value
        self.rs_rate = options.rate
        
        #Hard initialisation of bits per symbol
        self.bits_per_symbol = 1
        
        
        if options.verbose:
            print "USRP source:", self._usrp
            print "Decimation:", options.decim_rate
        
        
    
    def _print_verbage(self):
        """
        Prints informations about the receive path
        """
        print "\nReceive Path:"
        print "modulation:     %s"      % ("BPSK")
        print "bitrate:        %sb/s"   % (eng_notation.num_to_str(self._bitrate))
        print "sample/symbol:  %.4f"    % (self._samples_per_symbol)
        
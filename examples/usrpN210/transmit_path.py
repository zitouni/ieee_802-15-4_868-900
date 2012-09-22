'''
Created on Jul 12, 2011

@author: rafik
'''
from gnuradio import gr, gru, blks2
#from gnuradio import usrp_options

from tools import pick_bitrate 
#from pick_bitrate import pick_tx_bitrate
from gnuradio import eng_notation
import struct

from bpsk_modulator import bpsk_modulator
from tools import crc16

#from gnuradio import usrp

from gnuradio import uhd

from gnuradio.wxgui import constsink_gl

import copy
import sys

MAX_PKT_SIZE = 128

_dac_rate = 128e6
n2s = eng_notation.num_to_str

###############################################################
###Transmit path with arguments modulator and options 
###############################################################

def make_ieee802_15_4_packet(FCF, seqNr, addressInfo, payload, pad_for_usrp=True, preambleLength=4, SFD=0xA7):
    """
    Build a 802_15_4 packet

    @param FCF: 2 bytes defining the type of frame.
    @type FCF: string
    @param seqNr: 1 byte sequence number.
    @type seqNr: byte
    @param addressInfo: 0 to 20 bytes of address information.
    @type addressInfo: string
    @param payload: The payload of the packet. The maximal size of the message
    can not be larger than 128.
    @type payload: string
    @param pad_for_usrp: If we should add 0s at the end to pad for the USRP.
    @type pad_for_usrp: boolean
    @param preambleLength: Length of the preambble. Currently ignored.
    @type preambleLength: int
    @param SFD: Start of frame describtor. This is by default set to the IEEE 802.15.4 standard,
    but can be changed if required.
    @type SFD: byte
    """

    if len(FCF) != 2:
        raise ValueError, "len(FCF) must be equal to 2"
    if seqNr > 255:
        raise ValueError, "seqNr must be smaller than 255"
    if len(addressInfo) > 20:
        raise ValueError, "len(addressInfo) must be in [0, 20]"
    
    a = len(payload)
    b = len(addressInfo)
    if len(payload) > MAX_PKT_SIZE - 5 - len(addressInfo):
        raise ValueError, "len(payload) must be in [0, %d]" %(MAX_PKT_SIZE)

    SHR = struct.pack("BBBBB", 0, 0, 0, 0, SFD)
    PHR = struct.pack("B", 3 + len(addressInfo) + len(payload) + 2)
    MPDU = FCF + struct.pack("B", seqNr) + addressInfo + payload
    crc = crc16.CRC16()
    crc.update(MPDU)

    FCS = struct.pack("H", crc.intchecksum())

    pkt = ''.join((SHR, PHR, MPDU, FCS))

    if pad_for_usrp:
        # note that we have 16 samples which go over the USB for each bit
        pkt = pkt + (_npadding_bytes(len(pkt), 8) * '\x00')+0*'\x00'

    return pkt

def _npadding_bytes(pkt_byte_len, spb):
    """
    Generate sufficient padding such that each packet ultimately ends
    up being a multiple of 512 bytes when sent across the USB.  We
    send 4-byte samples across the USB (16-bit I and 16-bit Q), thus
    we want to pad so that after modulation the resulting packet
    is a multiple of 128 samples.

    @param ptk_byte_len: len in bytes of packet, not including padding.
    @param spb: samples per baud == samples per bit (1 bit / baud with GMSK)
    @type spb: int

    @returns number of bytes of padding to append.
    """
    modulus = 128
    byte_modulus = gru.lcm(modulus/8, spb) / spb
    r = pkt_byte_len % byte_modulus
    if r == 0:
        return 0
    return byte_modulus - r

def make_FCF(frameType=1, securityEnabled=0, framePending=0, acknowledgeRequest=0, intraPAN=0, destinationAddressingMode=0, sourceAddressingMode=0):
    """
    Build the FCF for the 802_15_4 packet

    """
    if frameType >= 2**3:
        raise ValueError, "frametype must be < 8"
    if securityEnabled >= 2**1:
        raise ValueError, " must be < "
    if framePending >= 2**1:
        raise ValueError, " must be < "
    if acknowledgeRequest >= 2**1:
        raise ValueError, " must be < "
    if intraPAN >= 2**1:
        raise ValueError, " must be < "
    if destinationAddressingMode >= 2**2:
        raise ValueError, " must be < "
    if sourceAddressingMode >= 2**2:
        raise ValueError, " must be < "
  
    return struct.pack("H", frameType
                       + (securityEnabled << 3)
                       + (framePending << 4)
                       + (acknowledgeRequest << 5)
                       + (intraPAN << 6)
                       + (destinationAddressingMode << 10)
                       + (sourceAddressingMode << 14))
    

class transmit_path(gr.hier_block2):
    def __init__(self, principal_gui, options):
        '''
        See below for what options should hold
        '''
        gr.hier_block2.__init__(self, "transmit_path",
                gr.io_signature(0, 0, 0),                    # Input signature
                gr.io_signature(0, 0, 0)) # Output signature
        
        options = copy.copy(options)    # make a copy so we can destructively modify

        self._verbose            = options.verbose
        self._tx_amplitude       = options.tx_amplitude    # digital amplitude sent to USRP
        self._bitrate            = options.rate        # desired bit rate
        self._samples_per_symbol = options.sps  # desired samples/baud

        #setup usrp
        self._setup_usrp_sink(options)
        
        #create a BPSK modulator 
        self.modulator = bpsk_modulator(principal_gui, options)         # the modulator we are using
        
        #create packet input like in ieee 802.15.4
        #the size of the queue is 2 messages 
        #######################*************
        msgq_limit = 10
        self.pkt_input = gr.message_source(gr.sizeof_char, msgq_limit)
             
        #The same chain like in ieee transceiver
        #add gain like in ieee802.15.4
        #######################################*****************
        #self.normal_gain = 8000
        #self.gain = gr.multiply_const_cc (self.normal_gain)
    
        self.amp = gr.multiply_const_cc(options.amplitude)
        #self.set_tx_amplitude(self._tx_amplitude)

        # Display some information about the setup
        if self._verbose:
            self._print_verbage()

        # Connect components in the flowgraph
        #self.connect(self.packet_transmitter, self.amp, self)
#        self.wxgui_constellationsink2_0 = constsink_gl.const_sink_c(
#            principal_gui.GetWin(),
#            title="Constellation Plot",
#            sample_rate=options.samp_rate,
#            frame_rate=5,
#            const_size=2048,
#            M=2,
#            theta=0,
#            fmax=0.06,
#            mu=0.5,
#            gain_mu=0.005,
#            symbol_rate=options.samp_rate/self._samples_per_symbol,
#            omega_limit=0.005,
#        )
#        principal_gui.Add(self.wxgui_constellationsink2_0.win)
        
        '''For Stream of bits '''
        self.vector_source = gr.vector_source_b([1,], True)
        self.scrambler = gr.scrambler_bb(0x10,0x7F,7)
        #self.connect(self.vector_source,self.scrambler, self.modulator, self.amp, self.u)
        #self.connect(self.modulator,self.wxgui_constellationsink2_0)
        '''End For Stream of bits '''
        
        
        self.connect(self.pkt_input, self.modulator, self.amp, self.u)
        

    def set_tx_amplitude(self, gain):
        """
        Sets the transmit amplitude sent to the USRP in volts
        @param: ampl 0 <= ampl < 1.
        """
        self._tx_amplitude = max(0.0, min(gain, 1))
        self.gain.set_k(self._tx_amplitude)
        
    def bitrate(self):
        return self._bitrate

    def samples_per_symbol(self):
        return self._samples_per_symbol

    def _print_verbage(self):
        """
        Prints information about the transmit path
        """
        print "Tx amplitude     %s"    % (self._tx_amplitude)
        print "modulation:      %s"    % ("BPSK")
        print "bitrate:         %sb/s" % (eng_notation.num_to_str(self._bitrate))
        print "samples/symbol:  %.4f"    % (self._samples_per_symbol)
        
    def _setup_usrp_sink(self, options):
        """
        Creates a USRP sink, determines the settings for best bitrate,
        and attaches to the transmitter's subdevice.
        """
        #self.u = usrp_options.create_usrp_sink(options)
        self.rs_rate = options.rate    # Store requested bit rate
        
        #options.interp = self._interp
        self.fs = options.samp_rate
        self._samples_per_symbol = options.sps
        
        #self.u.set_interp_rate(self._interp)
        #print "interpolation : ",  self._interp
        print "*******************************************************Transmission Parameters************************"
        print "USRP Adress: ", options.address
        print "Transmission Freqeuncy: ", eng_notation.num_to_str(options.freq)
        print "Sample rate or (Freqeuncy Sampling): ", eng_notation.num_to_str(options.samp_rate)
        print "Samples per symbol: ", options.sps
        print "data rate : ",  eng_notation.num_to_str(options.rate)
        print "Gain  : ", options.gain
        print "Amplitude : ", options.amplitude
        print "*******************************************************Transmission Parameters************************"
        
        #Configuration of USRP by UHD Driver
        samp_rate=self.fs
        self.u = uhd.usrp_sink(
            device_addr=options.address,
            stream_args=uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        
        self.u.set_subdev_spec("A:0", 0)
        self.u.set_samp_rate(samp_rate)
        self.u.set_center_freq(options.freq, 0)
        self.u.set_gain(options.gain, 0)

        #End Configuration
        
        #initiate hardly the value of bits per symbol to 1
        self.bits_per_symbol = 1
            
#        (self._bitrate, self._samples_per_symbol, self._interp) = \
#                        pick_bitrate.pick_tx_bitrate(options.bitrate, self.bits_per_symbol,
#                                        options.samples_per_symbol, options.interp,
#                                        dac_rate, self.u.get_interp_rates())
    
        
       
    def send_pkt(self, seqNr, addressInfo, payload='', eof=False):
        """
        Send the payload.

        @param seqNr: sequence number of packet
        @type seqNr: byte
        @param addressInfo: address information for packet
        @type addressInfo: string
        @param payload: data to send
        @type payload: string
        """
        if eof:
            msg = gr.message(1) # tell self.pkt_input we're not sending any more packets
        else:
            FCF = make_FCF()
            
        self.pad_for_usrp = True
        pkt = make_ieee802_15_4_packet(FCF,
                                        seqNr,
                                        addressInfo,
                                        payload,
                                        self.pad_for_usrp)
        #print "pkt =", packet_utils.string_to_hex_list(pkt), len(pkt)
        msg = gr.message_from_string(pkt)
        self.pkt_input.msgq().insert_tail(msg)


def add_freq_option(parser):
    """
    Hackery that has the -f / --freq option set both tx_freq and rx_freq
    """
    def freq_callback(option, opt_str, value, parser):
        parser.values.rx_freq = value
        parser.values.tx_freq = value
            
    if not parser.has_option('--freq'):
        parser.add_option('-f', '--freq', type="eng_float",
                          action="callback", callback=freq_callback,
                          help="set Tx and/or Rx frequency to FREQ [default=%default]",
                          metavar="FREQ")
            
     

#!/usr/bin/env python
'''
Created on Jul 12, 2011

@author: rafik
'''
#BPSK Modulation with differential encoder and symbol to chips conversion

from gnuradio import gr, eng_notation, usrp
from gnuradio import modulation_utils

#ieee is imported to do the symbols to chips conversion
import ieee

from gnuradio.wxgui import constsink_gl

from tools import psk

from math import pi, log10
import cmath

import sys
_def_excess_bw = 0.35
_def_gray_code = True

_dac_rate = 128e6
n2s = eng_notation.num_to_str

class bpsk_modulator(gr.hier_block2):
    
    def __init__(self, gui, options):
        gr.hier_block2.__init__(self, "bpsk_mod",
                                gr.io_signature(1, 1, gr.sizeof_char),       # Input signature
                                gr.io_signature(1, 1, gr.sizeof_gr_complex)) # Output signature
        
        self._samples_per_symbol = options.sps
        self.amplitude = options.amplitude
        self.verbose = options.verbose
        
        self._excess_bw = _def_excess_bw
        self._gray_code = _def_gray_code

        if not isinstance(self._samples_per_symbol, int) or self._samples_per_symbol < 2:
            raise TypeError, ("sample per symbol must be an integer >= 2, is %d" % self._samples_per_symbol)
    

        arity = pow(2,self.bits_per_symbol())
        
        # turn bytes into k-bit vectors
        self.packed_to_unpacked_bb = \
            gr.packed_to_unpacked_bb(self.bits_per_symbol(), gr.GR_MSB_FIRST)

        if self._gray_code:
            self.symbol_mapper = gr.map_bb(psk.binary_to_gray[arity])
        else:
            self.symbol_mapper = gr.map_bb(psk.binary_to_ungray[arity])
        self.diff_encoder_bb = gr.diff_encoder_bb(arity)
            
        #This bloc allow to decode the stream
        #self.scrambler = gr.scrambler_bb(0x8A, 0x7F, 7)
        
        #Transform symbols to chips
        self.symbols_to_chips = ieee.symbols_to_chips_bs()

        #self.chunks2symbols = gr.chunks_to_symbols_ic(psk.constellation[arity])
        self.chunks2symbols = gr.chunks_to_symbols_sc([-1+0j, 1+0j])
        self.chunks2symbols_b = gr.chunks_to_symbols_bc([-1+0j, 1+0j])
        
        # transform chips to symbols
        print "bits_per_symbol", self.bits_per_symbol()
        self.packed_to_unpacked_ss = \
          gr.packed_to_unpacked_ss(self.bits_per_symbol(), gr.GR_MSB_FIRST)

        ntaps = 11 * self._samples_per_symbol
        # pulse shaping filter
        self.rrc_taps = gr.firdes.root_raised_cosine(
                                                     self._samples_per_symbol * self.amplitude,   # gain (samples_per_symbol since we're
                                                                                # interpolating by samples_per_symbol)
                                                     self._samples_per_symbol,   # sampling rate
                                                     1.0,                # symbol rate
                                                     self._excess_bw,            # excess bandwidth (roll-off factor)
                                                     ntaps)
        self.rrc_filter = gr.interp_fir_filter_ccf(self._samples_per_symbol,
                                                   self.rrc_taps)

        # Connect
        #self.connect(self, self.bytes2chunks, self.symbol_mapper,self.scrambler, self.chunks2symbols, self.rrc_filter, self)
        
#        self.wxgui_constellationsink2_0 = constsink_gl.const_sink_c(
#            gui.GetWin(),
#            title="Constellation Plot",
#            sample_rate=self._samples_per_symbol,
#            frame_rate=5,
#            const_size=2048,
#            M=2,
#            theta=0,
#            alpha=0.005,
#            fmax=0.06,
#            mu=0.5,
#            gain_mu=0.005,
#            symbol_rate=self._samples_per_symbol/2,
#            omega_limit=0.005,
#        )
#        gui.Add(self.wxgui_constellationsink2_0.win)
        
        #Modefied for IEEE 802.15.4
        #self.connect(self, self.packed_to_unpacked_bb, self.symbol_mapper, self.diff_encoder_bb, self.symbols_to_chips, self.packed_to_unpacked_ss,  self.chunks2symbols, self.rrc_filter, self)
        
        self.connect(self, self.packed_to_unpacked_bb, self.symbol_mapper, self.symbols_to_chips, self.packed_to_unpacked_ss,  self.chunks2symbols, self.rrc_filter, self)
        #self.connect(self, self.symbols_to_chips, self.packed_to_unpacked_ss,  self.chunks2symbols, self.rrc_filter, self)
        
        #self.connect(self, self.packed_to_unpacked_ss,  self.chunks2symbols, self.rrc_filter, self)

        #self.connect(self, self._scrambler, self.chunks2symbols_b, self.rrc_filter, self)
        
        #self.connect(self.rrc_filter, self.wxgui_constellationsink2_0)


        if self.verbose:
            self._print_verbage()
            
            

    def samples_per_symbol(self):
        return self._samples_per_symbol

    def bits_per_symbol(self=None):   # static method that's also callable on an instance
        return 1
    bits_per_symbol = staticmethod(bits_per_symbol)      # make it a static method.  RTFM

    def add_options(parser):
        """
        Adds BPSK modulation-specific options to the standard parser
        """
        parser.add_option("", "--excess-bw", type="float", default=_def_excess_bw,
                          help="set RRC excess bandwith factor [default=%default]")
        parser.add_option("", "--no-gray-code", dest="gray_code",
                          action="store_false", default=True,
                          help="disable gray coding on modulated bits (PSK)")
    add_options=staticmethod(add_options)



    def _print_verbage(self):
        print "\nModulator:"
        print "bits per symbol:     %d" % self.bits_per_symbol()
        print "Gray code:           %s" % self._gray_code
        print "RRC roll-off factor: %.2f" % self._excess_bw
           
    
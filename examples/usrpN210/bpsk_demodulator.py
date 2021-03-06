'''
Created on Jul 18, 2011

@author: rafik
'''
from gnuradio import eng_notation
from gnuradio import gr, digital
from gnuradio.gr import firdes
from optparse import OptionParser

from gnuradio.wxgui import fftsink2
from gnuradio.wxgui import constsink_gl
import wx

import math
from tools import psk

n2s = eng_notation.num_to_str
_adc_rate = 64e6

_def_samples_per_symbol = 2
_def_excess_bw = 0.35
_def_gray_code = False
_def_verbose = False
_def_log = False

_def_costas_alpha = 0.1
_def_gain_mu = None
_def_mu = 0.5
_def_omega_relative_limit = 0.005

class bpsk_demodulator(gr.hier_block2):
    
    def __init__(self, principal_gui, options):
    
        gr.hier_block2.__init__(self, "bpsk_demod",
                gr.io_signature(1, 1, gr.sizeof_gr_complex), # Input signature
                gr.io_signature(1, 1, gr.sizeof_gr_complex))       # Output signature
        
        #Enter the parameters of modulation         
        self._samples_per_symbol = options.samples_per_symbol
        
        self.verbose = options.verbose

        self._gray_code =_def_gray_code
        
        if self._samples_per_symbol < 2:
            raise TypeError, "samples_per_symbol must be >= 2, is %r" % (self._samples_per_symbol,)

        arity = pow(2,self.bits_per_symbol())

        # Automatic gain control
        
        #self.agc = gr.agc2_cc(0.6e-1, 1e-3, 1, 1, 100)
        self.agc = gr.agc_cc(1e-5, 1.0,1.0,1.0)
        #self.agc = gr.feedforward_agc_cc(16, 2.0)

        # RRC data filter
        ntaps = 11 * self._samples_per_symbol
        self.rrc_taps = gr.firdes.root_raised_cosine(
            1.0,                      # gain
            self._samples_per_symbol, # sampling rate
            1.0,                      # symbol rate
            0.35,                      # excess bandwidth (roll-off factor)
            ntaps)
        self.rrc_filter=gr.interp_fir_filter_ccf(1, self.rrc_taps)        
                
        self._costas = digital.costas_loop_cc(6.28/100.0, 2)
        self.gr_null_sink = gr.null_sink(gr.sizeof_float*1)
        self.connect((self._costas, 1), (self.gr_null_sink, 0))
        
        self._mm = digital.clock_recovery_mm_cc(self._samples_per_symbol,       # Initial samples/symbol
                                           1e-06,  # Second order gain
                                           0.5,          # Initial symbol phase
                                           0.001,     # First order gain
                                           0.0001) # Maximum timing offset
        
        if self.verbose:
            self._print_verbage()
        
        # Do differential decoding based on phase change of symbols
        #self.diffdec = gr.diff_phasor_cc()
 
        # Connect and Initialize base class
        self.connect(self, self.agc, self.rrc_filter, (self._costas,0), self._mm, self)


    def samples_per_symbol(self):
        return self._samples_per_symbol

    def bits_per_symbol(self=None):   # staticmethod that's also callable on an instance
        return 1
    bits_per_symbol = staticmethod(bits_per_symbol)      # make it a static method.  RTFM

    def _print_verbage(self):
        print "\nDemodulator:"
        print "bits per symbol:     %d"   % self.bits_per_symbol()
        print "Gray code:           %s"   % self._gray_code
        print "RRC roll-off factor: %.2f" % self._excess_bw
        print "Costas Loop alpha:   %.2e" % self._costas_alpha
        print "Costas Loop beta:    %.2e" % self._costas_beta
        print "M&M mu:              %.2f" % self._mm_mu
        print "M&M mu gain:         %.2e" % self._mm_gain_mu
        print "M&M omega:           %.2f" % self._mm_omega
        print "M&M omega gain:      %.2e" % self._mm_gain_omega
        print "M&M omega limit:     %.2f" % self._mm_omega_relative_limit


    def add_options(parser):
        """
        Adds BPSK demodulation-specific options to the standard parser
        """
        parser.add_option("", "--excess-bw", type="float", default=_def_excess_bw,
                          help="set RRC excess bandwith factor [default=%default] (PSK)")
        parser.add_option("", "--no-gray-code", dest="gray_code",
                          action="store_false", default=_def_gray_code,
                          help="disable gray coding on modulated bits (PSK)")
        parser.add_option("", "--costas-alpha", type="float", default=None,
                          help="set Costas loop alpha value [default=%default] (PSK)")
        parser.add_option("", "--gain-mu", type="float", default=_def_gain_mu,
                          help="set M&M symbol sync loop gain mu value [default=%default] (GMSK/PSK)")
        parser.add_option("", "--mu", type="float", default=_def_mu,
                          help="set M&M symbol sync loop mu value [default=%default] (GMSK/PSK)")
        parser.add_option("", "--omega-relative-limit", type="float", default=_def_omega_relative_limit,
                          help="M&M clock recovery omega relative limit [default=%default] (GMSK/PSK)")
    add_options=staticmethod(add_options)
    

#

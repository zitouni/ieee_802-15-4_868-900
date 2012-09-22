#!/usr/bin/env python
'''
Created on Jul 18, 2011

@author: rafik
'''
from gnuradio import gr, gru, modulation_utils
from gnuradio import usrp
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option
from optparse import OptionParser # analyseur

import random 
import struct 
import sys

from grc_gnuradio import wxgui as grc_wxgui
from gnuradio import window
import wx

import receive_path

class my_top_block(grc_wxgui.top_block_gui):
    def __init__(self, rx_callback, options):
        #gr.top_block.__init__(self)
        grc_wxgui.top_block_gui.__init__(self, title="Receiver")
        
        #Set up reveive path 
        self.rxpath = receive_path.receive_path(self,rx_callback, options)
        
        #the all blocs are connected
        self.connect(self.rxpath)

global n_rcvd, n_right


class stats(object):
    def __init__(self):
        self.npkts = 0
        self.nright = 0    
    
def get_options():
    parser = OptionParser(option_class=eng_option)
    parser.add_option("-w", "--which", type="int", default=0,
                      help="select which USRP (0, 1, ...) (default is %default)",
                      metavar="NUM")
    parser.add_option("-R", "--rx-subdev-spec", type="subdev", default=None,
                      help="select USRP Rx side A or B (default=first one with a daughterboard)")
    parser.add_option("-f", "--freq", type="eng_float", default=None,
                      help="set frequency to FREQ", metavar="FREQ")
    parser.add_option("-g", "--gain", type="eng_float", default=None,
                      help="set Rx gain (default is mid-point)")
    parser.add_option("-r", "--rate", type="eng_float", default=250e3,
                      help="Select modulation symbol rate (default=%default)")
    parser.add_option("-d", "--decim-rate", type="int", default=32,
                      help="Select USRP decimation rate (default=%default)")
    parser.add_option("", "--excess-bw", type="eng_float", default=0.35,
                      help="Select RRC excess bandwidth (default=%default)")
    parser.add_option("", "--costas-alpha", type="eng_float", default=0.05,
                      help="set Costas loop 1st order gain, (default=%default)")
    parser.add_option("", "--costas-beta", type="eng_float", default=0.00025,
                      help="set Costas loop 2nd order gain, (default=%default)")
    parser.add_option("", "--costas-max", type="eng_float", default=0.05,
                      help="set Costas loop max freq (rad/sample) (default=%default)")
    parser.add_option("", "--mm-gain-mu", type="eng_float", default=0.001,
                      help="set M&M loop 1st order gain, (default=%default)")
    parser.add_option("", "--mm-gain-omega", type="eng_float", default=0.000001,
                      help="set M&M loop 2nd order gain, (default=%default)")
    parser.add_option("", "--mm-omega-limit", type="eng_float", default=0.0001,
                      help="set M&M max timing error, (default=%default)")
    
    parser.add_option("-S", "--samples-per-symbol", type = "float", default=8,
                          help="set samples/symbol [default=%default]")
        
    parser.add_option("-v", "--verbose", action ="store_true", default=False)
        
    parser.add_option("","--log", action="store_true", default = False,
                          help = "Log all parts of flow graph to files (CAUTION: lots of data)")
    
    (options, args) = parser.parse_args()
    if len(args) != 0:
        parser.print_help()
        sys.exit(1)
    
    if options.freq == None:
        print "You must supply a frequency with -f or --freq"
        sys.exit(1)

    return (options, args)

def main():
    global n_rcvd, n_right
    
    n_rcvd = 0
    n_right = 0
    
    def rx_callback(ok, payload):
        st.npkts += 1
        if ok:
            st.nright += 1

        (pktno,) = struct.unpack('!H', payload[0:2])
        print "ok = %5r  pktno = %4d  len(payload) = %4d  %d/%d" % (ok, pktno, len(payload),
                                                                    st.nright, st.npkts)
        print "  payload: " + str(map(hex, map(ord, payload)))
        print " ------------------------"
        sys.stdout.flush()
           
    #get the options of the receiver
    (options, args) = get_options()
    #create the demodulator
        
#    bpsk_demod = bpsk_demodulator(options)    
#    #create a graph flow
    tb = my_top_block(rx_callback, options)
    
    # To enable the real time scheduling 
    r= gr.enable_realtime_scheduling()
    
    if r!=gr.RT_OK :
        print "Warning: Failed to enable realtime scheduling"
        
    st = stats()
    
    #Begin the flow graph
    #tb.start()
    tb.Run(True)
    
    
    print "The flow graph is runed. I am after start"
    #Wait for it to finish
    tb.wait()      
    

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt: 
        pass

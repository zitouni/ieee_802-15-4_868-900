#!/usr/bin/env python
'''
Created on Jul 18, 2011

@author: rafik
'''
from gnuradio import gr, gru

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
    
    parser.add_option("-a", "--address", type="string", default="addr=192.168.10.2", 
                       help="Address of UHD device, [default=%default]") 
        
    parser.add_option("-S", "--samples-per-symbol", type = "float", default=2,
                          help="set samples/symbol [default=%default]")
    
    parser.add_option("-s", "--samp-rate", type="eng_float", default=0.5e6,
                      help="Select modulation sample rate (default=%default)")
    
    parser.add_option("-r", "--data-rate", type="eng_float", default=250e3,
                      help="Select modulation symbol rate (default=%default)")

    parser.add_option("-f", "--freq", type="eng_float", default=2480000000,
                      help="set frequency to FREQ", metavar="FREQ")
    
    parser.add_option ("-g", "--gain", type="eng_float", default=40,
                       help="set Rx PGA gain in dB [0,20]")
        
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

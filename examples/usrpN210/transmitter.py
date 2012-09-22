#!/usr/bin/env python
'''
Created on Jul 12, 2011

@author: rafik
'''

from gnuradio import gr, gru
from gnuradio import uhd
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option
from optparse import OptionParser

import random, time, struct, sys
import binascii

from grc_gnuradio import wxgui as grc_wxgui
import wx

import transmit_path
import os


class my_top_block(grc_wxgui.top_block_gui):
    def __init__(self, options):
        grc_wxgui.top_block_gui.__init__(self, title="Top Block")
        #gr.top_block.__init__(self)

        #construction of the transmit path of the USRP
        self.txpath = transmit_path.transmit_path(self, options)
        
        self.connect(self.txpath)


def get_options():
    parser = OptionParser(option_class=eng_option, conflict_handler = "resolve")
    expert_grp = parser.add_option_group("Expert")
    
    parser.add_option("-A", "--address", type="string", default="addr=192.168.10.3", 
                       help="Address of UHD device, [default=%default]") 
    
    parser.add_option("-S", "--sps", type = "float", default=8,
                          help="set samples/symbol [default=%default]")
    
    parser.add_option("-s", "--samp-rate", type="eng_float", default=2e6,
                      help="Select modulation sample rate (default=%default)")
    
    parser.add_option("-r", "--rate", type="eng_float", default=250e3,
                      help="Select modulation symbol rate (default=%default)")
    
    parser.add_option("-f", "--freq", type="eng_float", default=2480000000,
                      help="set frequency to FREQ", metavar="FREQ")
    
    parser.add_option ("-g", "--gain", type="eng_float", default=40,
                       help="set Rx PGA gain in dB [0,20]")
    
    parser.add_option("-a", "--amplitude", type="eng_float", default=0.5,
                      help="set Tx amplitude (0-1) (default=%default)")
    
    parser.add_option("", "--excess-bw", type="eng_float", default=0.35,
                      help="Select RRC excess bandwidth (default=%default)")
    
    #Packet size, the header with size of 19 bytes to the packet 
    parser.add_option("-s", "--size", type="eng_float", default=114,
                      help="set packet size [default=%default]")
    
    parser.add_option("", "--tx-amplitude", type="eng_float", default=0.25, metavar="AMPL",
                      help="set transmitter digital amplitude: 0 <= AMPL < 1 [default=%default]")
    
    parser.add_option("-v", "--verbose", action="store_true", default=False)
    
    parser.add_option("", "--log", action="store_true", default=False,
                      help="Log all parts of flow graph to file (CAUTION: lots of data)")
    
    
#    transmit_path.add_options(parser, expert_grp)
    
    (options, args) = parser.parse_args()
    if len(args) != 0:
        parser.print_help()
        sys.exit(1)
    
    if options.freq is None:
        sys.stderr.write("You must specify -f FREQ or --freq FREQ\n")
        parser.print_help(sys.stderr)
        sys.exit(1)
    return (options, args)

def main():
    def send_pkt(payload='', eof=False):
        return tb.txpath.send_pkt(0xe5, struct.pack("HHHH", 0xFFFF,0xFFFF, 0x10, 0x10), payload, eof)
    
    def rx_callback(ok, payload):
        print "ok = %r, payload =%s "% (ok, payload)
    
    #construct options of modulation BPSK all transmission     
    (options, args) = get_options()
    
    #Begin construction of the flow graph
    tb = my_top_block(options)
    
    
    #Allow a real time scheduling. It's possible just with root session
    r = gr.enable_realtime_scheduling()
    if r != gr.RT_OK:
        print "Warning: failed to enable realtime scheduling" 
    
    # With the graphical Sink
    #tb.Run(True) 
    
    tb.start()  #Begin the execution of flot graph
    #like in iee802.15.4 construct and send packets    
    for i in range(100):
        print "envoi du message %d: "% (i+1,)
        send_pkt(struct.pack('9B', 0x1, 0x80, 0x80, 0xff, 0xff, 0x10, 0x0, 0x20, 0x0))
        time.sleep(1)
     #wait transmission to finish 
     
    tb.wait()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

    
        
        
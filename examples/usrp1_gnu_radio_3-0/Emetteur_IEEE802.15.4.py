#!/usr/bin/env python
'''
Created on Jul 12, 2011

@author: rafik
'''

from gnuradio import gr, gru, modulation_utils
from gnuradio import usrp
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
    
    parser.add_option("-w", "--which", type="int", default=0,
                      help="select which USRP (0, 1, ...) default is %default",
                      metavar="NUM")
    parser.add_option("-T", "--tx-subdev-spec", type="subdev", default=None,
                      help="select USRP Tx side A or B (default=first one with a daughterboard)")
    
    parser.add_option("-f", "--freq", type="eng_float", default=None,
                      help="set frequency to FREQ", metavar="FREQ")
    parser.add_option("-a", "--amplitude", type="eng_float", default=2000,
                      help="set Tx amplitude (0-32767) (default=%default)")   
    parser.add_option("-r", "--rate", type="eng_float", default=250e3,
                      help="Select modulation symbol rate (default=%default)")
    parser.add_option("", "--sps", type="int", default=2,
                      help="Select samples per symbol (default=%default)")
    parser.add_option("", "--excess-bw", type="eng_float", default=0.35,
                      help="Select RRC excess bandwidth (default=%default)")
    
    #Packet size, the header with size of 19 bytes to the packet 
    parser.add_option("-s", "--size", type="eng_float", default=114,
                      help="set packet size [default=%default]")
    
    
    transmit_path.add_options(parser, expert_grp)
    
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
    tb.start()  #Begin the execution of flot graph
    #tb.Run() # With the graphical Sink
    
    #like in iee802.15.4 construct and send packets    
    for i in range(10):
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

    
        
        
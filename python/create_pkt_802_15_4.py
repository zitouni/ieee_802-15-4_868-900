#!/usr/bin/env python

import Numeric

from gnuradio import gr, packet_utils, gru
import crc16
import gnuradio.gr.gr_threading as _threading

import struct

MAX_PKT_SIZE = 128

class create_pkt_802_15_4():
    def __init__(self, addressInfo, payload):
    
        FCF = self.make_FCF()
        
        self.pkt = self.make_pkt(adressInfo, payload, FCF)   
        
    def  make_pkt(self, adressInfo, payload, FCF, seqNr =1, FCS = 2, preambleLength = 4, SFD = 0XA7, frameLength =1, pad_for_usrp = True):      
        if len(addressInfo) > 20:
            raise ValueError, "len(addressInfo) must be in [0, 20]"

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
    
    def get_pkt(self):
        return self.pkt
    
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
        
        return struct.pack("H", frameType + (securityEnabled << 3)
                                          + (framePending << 4)
                                          + (acknowledgeRequest << 5)
                                          + (intraPAN << 6)
                                          + (destinationAddressingMode << 10)
                                          + (sourceAddressingMode << 14))
    
    
if __name__ == '__main__':
    pkt = create_pkt_802_15_4("0xAA", "0xBB")
    
    print pkt
    

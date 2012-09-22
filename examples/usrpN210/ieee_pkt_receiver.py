
from gnuradio import gr, gru
import gnuradio.gr.gr_threading as _threading
import struct

# ieee is imported to do the sink of packet received 
import ieee
from tools import crc16

from gnuradio.wxgui import constsink_gl

class ieee_pkt_receiver_868_915(gr.hier_block2):
    """
    802_15_4 demodulator that is a GNU Radio sink.

    The input is complex baseband.  When packets are demodulated, they are passed to the
    app via the callback.
    """

    def __init__(self, *args, **kwargs):
        """
    Hierarchical block for BPSK demodulation.

    The input is the complex modulated signal at baseband.
        Demodulated packets are sent to the handler.

        @param callback:  function of two args: ok, payload
        @type callback: ok: bool; payload: string
        @param threshold: detect access_code with up to threshold bits wrong (-1 -> use default)
        @type threshold: int

        See ieee802_15_4_demod for remaining parameters.
    """
        try:
            self.callback = kwargs.pop('callback')
            self.threshold = kwargs.pop('threshold')    
            #Return the demodulator
            self.demodulator = kwargs.pop('demodulator')
            self.gui = kwargs.pop('gui')
            self._samples_per_symbol = kwargs.pop('sps')
        except KeyError:
            pass
        gr.hier_block2.__init__(self, "ieee_pkt_receiver",
                        gr.io_signature(1, 1, gr.sizeof_gr_complex),  # Input
                        gr.io_signature(0, 0, 0))  # Output
        
        self._rcvd_pktq = gr.msg_queue()          # holds packets from the PHY
        
        #Create the sink of packets
        self._packet_sink = ieee.ieee802_15_4_packet_sink(self._rcvd_pktq, self.threshold)
        
        #self.complex_to_float = gr.complex_to_float(1)
        self.complex_to_real = gr.complex_to_real()
        
        self.connect(self, self.demodulator, self.complex_to_real, self._packet_sink)
      
        self._watcher = _queue_watcher_thread(self._rcvd_pktq, self.callback)

    def carrier_sensed(self):
        """
        Return True if we detect carrier.
        """
        return self._packet_sink.carrier_sensed()


class _queue_watcher_thread(_threading.Thread):
    def __init__(self, rcvd_pktq, callback):
        _threading.Thread.__init__(self)
        self.setDaemon(1)
        self.rcvd_pktq = rcvd_pktq
        self.callback = callback
        self.keep_running = True
        self.start()

    def run(self):
        while self.keep_running:
            print "802_15_4_pkt: waiting for packet"
            msg = self.rcvd_pktq.delete_head()
            ok = 0
            payload = msg.to_string()
            
            print "received packet "
            
            if len(payload) > 2:
                crc = crc16.CRC16()
                crc.update(payload[:-2])

                crc_check = crc.intchecksum()
                print "checksum: %s, received: %s"%(crc_check, str(ord(payload[-2]) + ord(payload[-1])*256))

                ok = (crc_check == ord(payload[-2]) + ord(payload[-1])*256)
                msg_payload = payload
                
                if self.callback:
                    self.callback(ok, msg_payload)

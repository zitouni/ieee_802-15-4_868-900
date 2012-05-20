/*
 * First arg is the package prefix.
 * Second arg is the name of the class minus the prefix.
 *
 * This does some behind-the-scenes magic so we can
 * access ieee802_15_4_packet_sink from python as ieee802_15_4_packet_sink
 */
GR_SWIG_BLOCK_MAGIC(ieee,ieee802_15_4_packet_sink);

ieee_ieee802_15_4_packet_sink_sptr ieee_make_ieee802_15_4_packet_sink (gr_msg_queue_sptr target_queue,
								       int threshold);

class ieee_ieee802_15_4_packet_sink : public gr_block
{
private:
  ieee_ieee802_15_4_packet_sink ();
};

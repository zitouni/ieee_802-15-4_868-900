/*
 * First arg is the package prefix.
 * Second arg is the name of the class minus the prefix.
 *
 * This does some behind-the-scenes magic so we can
 * access ieee_symbols_to_chips_bs from python as ieee.symbols_to_chips_bs
 */
GR_SWIG_BLOCK_MAGIC(ieee,symbols_to_chips_bs);

ieee_symbols_to_chips_bs_sptr ieee_make_symbols_to_chips_bs ();

class ieee_symbols_to_chips_bs : public gr_block
{
private:
  ieee_symbols_to_chips_bs ();
};

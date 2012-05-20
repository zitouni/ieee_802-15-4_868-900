/* -*- c++ -*- */
/*
 * Copyright 2004 Free Software Foundation, Inc.
 * 
 * This file is part of GNU Radio
 * 
 * GNU Radio is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2, or (at your option)
 * any later version.
 * 
 * GNU Radio is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with GNU Radio; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#ifndef INCLUDED_UCLA_SYMBOLS_TO_CHIPS_BI_H
#define INCLUDED_UCLA_SYMBOLS_TO_CHIPS_BI_H

#include <gr_sync_interpolator.h>

class ieee_symbols_to_chips_bs;
typedef boost::shared_ptr<ieee_symbols_to_chips_bs> ieee_symbols_to_chips_bs_sptr;

ieee_symbols_to_chips_bs_sptr ieee_make_symbols_to_chips_bs ();

/*!
 * \brief Map a stream of symbol indexes (unpacked bytes) to stream of unsigned integers
 * \ingroup ieee
 *
 * input: stream of unsigned char; output: stream of int
 *
 */

class ieee_symbols_to_chips_bs : public gr_sync_interpolator
{
  friend ieee_symbols_to_chips_bs_sptr ieee_make_symbols_to_chips_bs ();

  ieee_symbols_to_chips_bs ();

 public:
  int work (int noutput_items,
	    gr_vector_const_void_star &input_items,
	    gr_vector_void_star &output_items);

  bool check_topology(int ninputs, int noutputs) { return ninputs == noutputs; }
};

#endif

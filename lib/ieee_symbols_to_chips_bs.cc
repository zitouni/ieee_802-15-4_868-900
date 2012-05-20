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

// WARNING: this file is machine generated.  Edits will be over written

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <ieee_symbols_to_chips_bs.h>
#include <gr_io_signature.h>
#include <assert.h>
#include <iostream>
#include <cstring>
#include <stdio.h>

//decimal coding of the squence chips of bits
static const unsigned int d_symbol_table[] = {31432,  //for sequence number 111101011001000
											  1335};  //for sequence number 000010100110111

static const int TABLE_SIZE = 2;


ieee_symbols_to_chips_bs_sptr
ieee_make_symbols_to_chips_bs ()
{
  return ieee_symbols_to_chips_bs_sptr (new ieee_symbols_to_chips_bs ());
}

ieee_symbols_to_chips_bs::ieee_symbols_to_chips_bs ()
  : gr_sync_interpolator ("symbols_to_chips_bs",
			  gr_make_io_signature (1, -1, sizeof (unsigned char)),
			  gr_make_io_signature (1, -1, sizeof (unsigned short)),
			  2)
{
}

int
ieee_symbols_to_chips_bs::work (int noutput_items,
			gr_vector_const_void_star &input_items,
			gr_vector_void_star &output_items)
{
  assert (input_items.size() == output_items.size());
  int nstreams = input_items.size();
  //printf("la taille de out_items est %d, de input_items %d \n", output_items.size(), input_items.size());

  for (int m=0;m<nstreams;m++) {
    const unsigned char *in = (unsigned char *) input_items[m];
    unsigned short *out = (unsigned short *) output_items[m];

    // per stream processing
    //printf("pour un in[%d] : %x\n", m, in[m]);
    //printf ("noutput_items %d\n", noutput_items);
    for (int i = 0; i < noutput_items; i+=1){
      //fprintf(stderr, "%x %x, \n", in[i/8]&0xf, (in[i/8])&0x1), fflush(stderr);

      // The LSBlock is sent first (802.15.4 standard)
      //For 1 bits of the stream, the most significant bit
      //printf("la première valeur dans la table avec l'indice %d \n", (unsigned int)(in[i]&0x1));
      //printf("la valeur dans le tableaux qui correspond à l'indice est : %d \n", d_symbol_table[in[i]&0x1]);

      // The LSBlock is sent first (802.15.4 standard)
      //printf("la valeur de i %d\n", i);
      //printf("la valeur de i %d\n",i);
      //memcpy(&out[i+1], &d_symbol_table[(unsigned int)((in[i/2]>>2)&0xf)], sizeof(unsigned int));
      //printf("in[%d] %x\n", i, in[i]);
      //memcpy(&out[i], &d_symbol_table[(unsigned short)((in[i/2])&0x1)], sizeof(unsigned short));

      memcpy(&out[i], &d_symbol_table[(unsigned short)(in[i]&0x1)], sizeof(unsigned short));

      //out[i] = d_symbol_table[(unsigned short)((in[i])&0x1)];

      //printf("out[%d] %x\n", i, out[i]);
      // The LSBlock is sent first (802.15.4 standard)
      //memcpy(&out[i+1], &d_symbol_table[(unsigned int)((in[i/2]>>4)&0xF)], sizeof(unsigned int));
      //memcpy(&out[i], &d_symbol_table[(unsigned int)(in[i/2]&0xF)], sizeof(unsigned int));
      //printf("la première valeur dans la table avec l'indice %d ", (unsigned int)((in[i/2]>>4)&0xF));
      //memcpy(&out[i], &d_symbol_table[(unsigned int)((in[i/2])&0x1)], sizeof(unsigned int));

      // The LSBlock is sent first (802.15.4 standard)
      //printf("i %d, out[i] : %x \n", i, out[i]);

    }
    // end of per stream processing

  }
  return noutput_items;
}

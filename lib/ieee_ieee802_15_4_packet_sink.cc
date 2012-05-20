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

/*
 * ucla_ieee802_15_4_packet_sink.cc has been derived from gr_packet_sink.cc
 *
 * Modified by: ZITOUNI RAFIK
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <ieee_ieee802_15_4_packet_sink.h>
#include <gr_io_signature.h>
#include <cstdio>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdexcept>
#include <cstring>
#include <gr_count_bits.h>

#include <stdlib.h>
// very verbose output for almost each sample
#define VERBOSE 0
// less verbose output for higher level debugging
#define VERBOSE2 1

static const int DEFAULT_THRESHOLD = 1;  // detect access code with up to DEFAULT_THRESHOLD bits wrong

  // this is the mapping between chips and symbols if
  // With standard specification for frequency band of 868-915
  //

static const unsigned int CHIP_MAPPING[] = {31432,  //for sequence number 111101011001000
											1335};  //for sequence number 000010100110111


inline void
ieee_ieee802_15_4_packet_sink::enter_search()
{
  if (VERBOSE)
    fprintf(stderr, "@ enter_search\n");

  d_state = STATE_SYNC_SEARCH;
  d_shift_reg = 0;

  d_preamble_cnt = 0;
  d_chip_cnt = 0;
  d_packet_byte = 0;

  bit_0 =0;
  bit_1 =0;
  bit_breamble =0;
  nbr_bit_sfd = 0;
  bit_sfd =0;
  inc = 0;
  find_preamble = false;
  search_sfd = false;
  first_found = false;
}
    
inline void
ieee_ieee802_15_4_packet_sink::enter_have_sync()
{
  if (VERBOSE)
    fprintf(stderr, "@ enter_have_sync\n");

  bit_0 =0;
  bit_1 =0;

  nbr_bits =0;
  byte =0;
  d_chip_cnt =0;
  d_shift_reg =0;

  d_state = STATE_HAVE_SYNC;
  d_packetlen_cnt = 0;
  d_packet_byte = 0;
  d_packet_byte_index = 0;
}

inline void
ieee_ieee802_15_4_packet_sink::enter_have_header(int payload_len)
{
  if (VERBOSE)
    fprintf(stderr, "@ enter_have_header (payload_len = %d)\n", payload_len);
  
  d_state = STATE_HAVE_HEADER;
  d_packetlen  = payload_len;
  d_payload_cnt = 0;
  d_packet_byte = 0;

  d_packet_byte_index = 0;

  d_byte = 0;
  nbr_bits = 0;
}


/*inline int
ieee_ieee802_15_4_packet_sink::decode_chips(unsigned int chips, int stream){
	int bit_0 = 0;
	int bit_1 = 0;
	//construct the byte by using the chips
	//return 0
	bit_0 = gr_count_bits16((d_shift_reg&0xffff)^(CHIP_MAPPING[0]& 0x7fff));
	//return 1
	bit_1 = gr_count_bits16((d_shift_reg&0xffff)^(CHIP_MAPPING[1]& 0x7fff));
    //construct the stream of the 1 bits
    if ((bit_0 == 0)&&(bit_1 != 0)){
   		  stream = stream << 1;
    }
    //construct the stream of the 0 bits
    if ((bit_1 == 0)&&(bit_0 != 0)){
   		  stream = stream << 1 | 1;
    }

    return stream;
}*/
inline unsigned char
ieee_ieee802_15_4_packet_sink::decode_chips(unsigned int chips){
  int i;
  int best_match = 0xFF;
  int min_threshold = 16; // Matching to 15 chips, could never have a error of 16 chips

  for(i=0; i<2; i++) {
    // FIXME: we can store the last chip
    // ignore the first and last chip since it depends on the last chip.
    unsigned int threshold = gr_count_bits16((chips&0x7FFF) ^ (CHIP_MAPPING[i]&0x7FFF));

    if (threshold < min_threshold) {
        best_match = i;
        min_threshold = threshold;
    }
  }

  if (min_threshold < d_threshold) {
    if (VERBOSE)
	  fprintf(stderr, "Found sequence with %d errors at 0x%x\n", min_threshold, (chips&0x7FFFFFFE) ^ (CHIP_MAPPING[best_match]&0x7FFFFFFE)), fflush(stderr);

    return (char)best_match&0xF;
  }

  return 0xFF;
}

ieee_ieee802_15_4_packet_sink_sptr
ieee_make_ieee802_15_4_packet_sink (gr_msg_queue_sptr target_queue,
			   int threshold)
{
  return ieee_ieee802_15_4_packet_sink_sptr (new ieee_ieee802_15_4_packet_sink (target_queue, threshold));
}


ieee_ieee802_15_4_packet_sink::ieee_ieee802_15_4_packet_sink (gr_msg_queue_sptr target_queue, int threshold)
  : gr_sync_block ("sos_packet_sink",
		   gr_make_io_signature (1, 1, sizeof(float)),
		   gr_make_io_signature (0, 0, 0)),
    d_target_queue(target_queue), 
    d_threshold(threshold == -1 ? DEFAULT_THRESHOLD : threshold)
{
  d_sync_vector = 0xA7;
  d_processed = 0;

  if ( VERBOSE )
    fprintf(stderr, "syncvec: %x, threshold: %d\n", d_sync_vector, d_threshold),fflush(stderr);
  enter_search();
}

ieee_ieee802_15_4_packet_sink::~ieee_ieee802_15_4_packet_sink ()
{
}


int ieee_ieee802_15_4_packet_sink::work (int noutput_items,
		      gr_vector_const_void_star &input_items,
		      gr_vector_void_star &output_items)
{
  float *inbuf = (float *) input_items[0];
  int count=0;

  
  if (VERBOSE)
    fprintf(stderr,">>> Entering state machine\n"),fflush(stderr);
  d_processed += noutput_items;

  //For the case of search the STATE_SYNC_SEARCH
  //is the bits sequence constructed by the ships passed

  while (count<noutput_items) {
    switch(d_state) {
      
    case STATE_SYNC_SEARCH:    // Look for sync vector

      if (VERBOSE)
    	  fprintf(stderr,"SYNC Search, noutput=%d syncvec=%x\n",noutput_items, d_sync_vector),fflush(stderr);

      while ((count < noutput_items)) {
	
    	  //if(inbuf[count++] == 0.0)
    	  //  continue;

    	  //printf("la sortie inbuf %f\n", inbuf[count]);
    	  if(slice(inbuf[count]))
    		  d_shift_reg = (d_shift_reg << 1) | 1;
    	  else
    		  d_shift_reg = d_shift_reg << 1;
    	  count++;
    	  d_chip_cnt ++;

    	  //if(d_preamble_cnt > 0){
    	  //	  d_chip_cnt = d_chip_cnt+1;
    	  //}

    	  //construction of chips
    	  //if (d_chip_cnt == 15)
    		//  printf("Le chips num %d la sortie %d est d_shift_reg %x\n", d_chip_cnt, count, d_shift_reg&0x7FFF);

    	  //return 0
    	  bit_0 = gr_count_bits16((d_shift_reg&0xffff)^(CHIP_MAPPING[0]& 0x7fff));
    	  //return 1
    	  bit_1 = gr_count_bits16((d_shift_reg&0xffff)^(CHIP_MAPPING[1]& 0x7fff));

    	  if ((bit_0 ==0) || (bit_1 ==0)){
    		  //printf("la valeur de d_shift_reg est : %x\n", d_shift_reg&0xffff);
    		  d_shift_reg = 0;

    		   if (not find_preamble){
    		     	search_sfd = false;
    		     	if ((bit_0 == 0)&&(bit_1 != 0)){
    		     		//count the number of 0, the 0 is like 1
    		     		 bit_breamble = bit_breamble <<1 | 1;
    		     		 //printf("nbr de 0 %d Le chips num %d la sortie %d est d_shift_reg %x\n", inc, d_chip_cnt, count, d_shift_reg&0x7FFF);
    		     		 inc++;
    		     		 if (bit_breamble == 0xffffffff){
    		     			 if (VERBOSE)
    		     				 fprintf(stderr,"Find all preamble, %d\n", inc), fflush(stderr);
    		     		     find_preamble = true;
    		     		     search_sfd = true;
    		     		     bit_breamble = 0;
    		     			 bit_sfd = 0;
    		     			 inc =0;
    		     			 //exit(0);
    		     		}
    		     	}else{
  		     		  if (bit_1 == 0){
    		    	  	 enter_search();
    		    	  	 break;
  		     		  }
    		     	}
    		    } //Construct the successive bits of the SFD
    		   	//If it's the begin of the SFD search and the preamble is found
    		    if ((search_sfd)&&(find_preamble)){
    		    	//construct the stream of the 1 bits
    		       if ((bit_1 == 0)&&(bit_0 != 0)&&(nbr_bit_sfd==0))
    		    	   first_found = true;

    		       if ((bit_0 == 0)&&(bit_1 != 0)&& (first_found)){
    		     		  bit_sfd = bit_sfd << 1;
    		     		  nbr_bit_sfd++;
    		       }
    		        //construct the stream of the 0 bits
    		       if ((bit_1 == 0)&&(bit_0 != 0)&&(first_found)){
    		     		  bit_sfd = bit_sfd << 1 | 1;
    		     		  nbr_bit_sfd++;
    		       }
    		       //Test if the SFD is found
    		      if ((bit_sfd == 0xa7)&&(nbr_bit_sfd ==8)){
    		     		  //printf("The value of SFD is : %x \n", bit_sfd&0xff);
    		    	  	  nbr_bit_sfd = 0;
    		    	  	  if (VERBOSE)
    		    	  		  fprintf(stderr,"Start Frame Delimeter is found \n"), fflush(stderr);
    		     		  //enter_search();
    		     		  //exit(0);
    		     		  //Found SFD
    		     		  //Setup for Header decode
    		     		  enter_have_sync();
    		     		  break;
    		      }else{
    		    	  //the SFD field is not found
    		    	  if ((bit_sfd != 0xa7)&&(nbr_bit_sfd ==8)){
    		    		  if (VERBOSE)
    		    			  fprintf(stderr,"The value of SFD is Wrong*********** : %x\n",bit_sfd&0xff), fflush(stderr);
    		    	  	  //printf("Start Frame Delimeter is not found \n");
    		    	  	  //Run the new search
    		    	  	  enter_search();
    		    	  	  break;
    		    	  }
    		      }
    		      //number of the sfd bits is 8
    		      if (nbr_bit_sfd == 8){
    		     		  nbr_bit_sfd =0;
    		     		  bit_sfd =0;
    		     		  find_preamble = false;
    		       }
    		    }
    	  }

      } //End of While loop
      break;

    case STATE_HAVE_SYNC:
      if (VERBOSE2)
    	  //fprintf(stderr,"Header Search bitcnt=%d, header=0x%08x\n", d_headerbitlen_cnt, d_header), fflush(stderr);

     // fprintf(stderr,"I am in the PHR field \n"), fflush(stderr);
      while (count < noutput_items) {		// Decode the bytes one after another.

    	  if(slice(inbuf[count]))
    		  d_shift_reg = (d_shift_reg << 1) | 1;
    	  else
    		  d_shift_reg = d_shift_reg << 1;

    	  d_chip_cnt = d_chip_cnt+1;
    	  count ++;

    	  //construct the byte by using the chips
          //return 0
          bit_0 = gr_count_bits16((d_shift_reg&0xffff)^(CHIP_MAPPING[0]& 0x7fff));
          //return 1
          bit_1 = gr_count_bits16((d_shift_reg&0xffff)^(CHIP_MAPPING[1]& 0x7fff));

          if ((bit_0 ==0) || (bit_1 ==0)){
        	      d_chip_cnt = 0;
        	      //fprintf(stderr,"The sequence of d_shift_reg %x \n", d_shift_reg&0xffff), fflush(stderr);
        		  //construct the stream of the 1 bits
        		  if ((bit_0 == 0)&&(bit_1 != 0)){
        			  byte = byte << 1;
		     		  nbr_bits++;
        		  }
        		  //construct the stream of the 0 bits
        		  if ((bit_1 == 0)&&(bit_0 != 0)){
		     		  byte = byte << 1 | 1;
		     		  nbr_bits++;
        		  }

        		  if (nbr_bits == 8){
        			  //found the Byte
        			  nbr_bits = 0;
        			  //fprintf(stderr,"The value of PHR is %x\n", byte), fflush(stderr);
        			  // we have a complete byte which repr      esents the frame length.
        			  int frame_len = byte;
        			  if(frame_len <= MAX_PKT_LEN){
        				  enter_have_header(frame_len);
        				  if (VERBOSE)
        					  fprintf(stderr,"The value of PHR is %x and is good \n", byte), fflush(stderr);
        			      //enter_search();
        			      //exit(0);
        			  } else {
        				  //exit(0);
        			      enter_search();
        			      break;
        			  }
        			  break;
        		  }
          }else{
        	  if (d_chip_cnt == 16){
        		  fprintf(stderr,"The sequence of d_shift_reg %x \n", d_shift_reg&0xffff), fflush(stderr);
        		  fprintf(stderr,"The chips are not equale to that of the table \n"), fflush(stderr);
        		  //exit(0);
        		  enter_search();
        	  }
          }
      	}
      break;
      
    case STATE_HAVE_HEADER:
      if (VERBOSE2)
    	  //fprintf(stderr,"Packet Build count=%d, noutput_items=%d, packet_len=%d\n", count, noutput_items, d_packetlen),fflush(stderr);

      while (count < noutput_items) {   // shift bits into bytes of packet one at a time
    	  if(slice(inbuf[count]))
    		  d_shift_reg = (d_shift_reg << 1) | 1;
    	  else
    		  d_shift_reg = d_shift_reg << 1;

    	  d_chip_cnt = d_chip_cnt+1;
    	  count ++;

    	  //construct the byte by using the chips
          //return 0
          bit_0 = gr_count_bits16((d_shift_reg&0xffff)^(CHIP_MAPPING[0]& 0x7fff));
          //return 1
          bit_1 = gr_count_bits16((d_shift_reg&0xffff)^(CHIP_MAPPING[1]& 0x7fff));

          if ((bit_0 ==0) || (bit_1 ==0)){
    		  // the first symbol represents the first part of the byte.
    	      d_chip_cnt = 0;
    	      //fprintf(stderr,"The sequence of d_shift_reg %x \n", d_shift_reg&0xffff), fflush(stderr);
    		  //construct the stream of the 1 bits
    		  if ((bit_0 == 0)&&(bit_1 != 0)){
    			  d_byte = d_byte << 1;
	     		  nbr_bits++;
    		  }
    		  //construct the stream of the 0 bits
    		  if ((bit_1 == 0)&&(bit_0 != 0)){
	     		  d_byte = d_byte << 1 | 1;
	     		  nbr_bits++;
    		  }
    		  //fprintf(stderr, "%d: 0x%x\n", d_packet_byte_index, c);
    		  if (nbr_bits == 8){
    			  // we have a complete byte
    			  if (VERBOSE2)
    				  //fprintf(stderr, "packetcnt: %d, payloadcnt: %d, payload 0x%x\n", d_packetlen_cnt, d_payload_cnt, d_packet_byte), fflush(stderr);
    			  //Assambeled bytes
    			  d_packet[d_packetlen_cnt++] = d_byte;
    			  d_payload_cnt++;
    			  d_byte = 0;
    			  nbr_bits = 0;

    			  if (d_payload_cnt >= d_packetlen){	// packet is filled (rempli), including CRC. might do check later in here
    				  // build a message
    				  gr_message_sptr msg = gr_make_message(0, 0, 0, d_packetlen_cnt);
    				  //Load the packet in the memory space
    				  memcpy(msg->msg(), d_packet, d_packetlen_cnt);

    				  d_target_queue->insert_tail(msg);		// send it
    				  msg.reset();  						// free it up
    				  if(VERBOSE)
    					  fprintf(stderr, "Adding message of size %d to queue\n", d_packetlen_cnt);
    				  enter_search();
    				  break;
    			  }
    		  }
    	  }else{
        	  if (d_chip_cnt == 16){
        		  fprintf(stderr,"The sequence of d_shift_reg %x \n", d_shift_reg&0xffff), fflush(stderr);
        		  fprintf(stderr,"The chips are not equale to that of the table \n"), fflush(stderr);
        		  //exit(0);
        		  enter_search();
        	  }
    	  }
      }
      break;

    default:
      assert(0); // when there are no case is found--generate the error messages

    } // switch

  }   // while

  if(VERBOSE2)
    //fprintf(stderr, "Samples Processed: %d\n", d_processed), fflush(stderr);

  return noutput_items;
}
  

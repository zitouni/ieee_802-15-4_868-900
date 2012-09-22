'''
Created on Jul 25, 2011

@author: rafik
'''
from math import pi, sqrt, log10
import math, cmath

# The following algorithm generates Gray coded constellations for M-PSK for M=[2,4,8]
def make_gray_constellation(m):
    # number of bits/symbol (log2(M))
    k = int(log10(m) / log10(2.0))

    coeff = 1
    const_map = []
    bits = [0]*3
    for i in range(m):
        # get a vector of the k bits to use in this mapping
        bits[3-k:3] = [((i&(0x01 << k-j-1)) >> k-j-1) for j in range(k)]

        theta = -(2*bits[0]-1)*(2*pi/m)*(bits[0]+abs(bits[1]-bits[2])+2*bits[1])
        re = math.cos(theta)
        im = math.sin(theta)
        const_map.append(complex(re, im))   # plug it into the constellation
    
    # return the constellation; by default, it is normalized
    return const_map

# This makes a constellation that increments around the unit circle
def make_constellation(m):
    return [cmath.exp(i * 2 * pi / m * 1j) for i in range(m)]

# Common definition of constellations for Tx and Rx
constellation = {
    2 : make_constellation(2),           # BPSK
    4 : make_constellation(4),           # QPSK
    8 : make_constellation(8)            # 8PSK
    }

gray_constellation = {
    2 : make_gray_constellation(2),           # BPSK
    4 : make_gray_constellation(4),           # QPSK
    8 : make_gray_constellation(8)            # 8PSK
    }

# -----------------------
# Do Gray code
# -----------------------
# binary to gray coding -- constellation does Gray coding
binary_to_gray = {
    2 : range(2),
    4 : [0,1,3,2],
    8 : [0, 1, 3, 2, 7, 6, 4, 5]
    }

# gray to binary
gray_to_binary = {
    2 : range(2),
    4 : [0,1,3,2],
    8 : [0, 1, 3, 2, 6, 7, 5, 4]
    }

# -----------------------
# Don't Gray code
# -----------------------
# identity mapping
binary_to_ungray = {
    2 : range(2),
    4 : range(4),
    8 : range(8)
    }

# identity mapping
ungray_to_binary = {
    2 : range(2),
    4 : range(4),
    8 : range(8)
    }

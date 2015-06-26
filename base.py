#!/usr/bin/env python
#-*- coding:utf-8 -*-

HOST = "127.0.0.1"
PORT = 46977


# 1 position for 2bit
#     (first bit 0: blank
#                1: placed
#      second bint 0: BLACK
#                  1: WHITE )
# 1 tower for (2*4=)8bit = 1byte
#     (first two bits are for the tip position
#      last two bits are for the bottom etc..)
# eg. 11|10|00|00 (2) 
# 
#board = 
# [A1, A2, A3, A4,
#  B1, B2, B3, B4,
#  C1, C2, C3, C4,
#  D1, D2, D3, D4]

#COLOR
BLANK = 0b00
BLACK = 0b10
WHITE = 0b11

def is_same_non0(l):
    # 0 means BLANK
    if l[0] != 0 and l.count(l[0]) == len(l):
        return True
    else:
        return False

def has0_and_same(l):
    if l.count(0) == 1:
        non0 = (l0 for l0 in l if l0 != 0).next()
        if l.count(non0) == len(l)-1:
            #there is one 0 in l and all the non-0 are the same number
            return non0, l.index(0)#COLOR and index of different one
    
    return False,False

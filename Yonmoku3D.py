#!/usr/bin/env python
#-*- coding:utf-8 -*-

from array import array
import socket

HOST = "127.0.0.1"
PORT = 46977

# 0120(3)
#[[[], [], [], []],
# [[], [], [], []],
# [[], [], [], []],
# [[], [], [], []]]]

#COLOR
BLANK = 0
BLACK = 1
WHITE = 2

# base3str(0) == "0000"
# base3str(3) == "0010"
# base3str(80) == "2222"
def int_to_base3(num):
    assert 0 <= num < 81
    s = array("B") #unsigned char
    for i in xrange(3,-1,-1):
        s.append(num / 3**i)
        num %= 3**i
    assert s.count(0) == 4 or s[-1] != 0

    return s

def base3_to_int(ar):
    assert len(ar) == 4
    n = 0
    for i in xrange(4):
        n+= ar[i] * 3**(3-i)
    return n

def is_same_non0(l):
    if l[0] != 0 and l.count(l[0]) == len(l):
        return True
    else:
        return False

def has0_and_same(l):
    if l.count(0) == 1 and l.count(l[0]) == len(l)-1:
        return l[0], l.index(0)#COLOR and pos
    else:
        return False,False
    
class Board(object):
    def __init__(self):
        self.board = [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]
        self.s = None
        self.conn = None
        self.addr = None

    def put(self, x,y,color):
        s = int_to_base3(self.board[y][x])
        if s.count(0) == 0:
            raise ValueError("This Tower is full!")
        else:
            s[s.count(0)-1] = color
            self.board[y][x] = base3_to_int(s)
            return
    
    def get(self, x,y,z=None):
        if z == None:
            return int_to_base3(self.board[y][x])
        if 0 <= z < 4:
            return int_to_base3(self.board[y][x])[z]

    def is_finished(self):
        # call this method every time the board is changed in order not to miss the finish
        r = [self._is_finished_x(),
             self._is_finished_y(),
             self._is_finished_z(),
             self._is_finished_xy(),
             self._is_finished_yz(),
             self._is_finished_zx(),
            self._is_finished_diag()]
        if BLACK in r:
            return BLACK
        elif WHITE in r:
            return WHITE
        else:
            return False

    def _is_finished_x(self):
        for y in xrange(4):
            for z in xrange(4):
                if is_same_non0([self.get(x,y,z) for x in xrange(4)]):
                    return self.get(0,y,z) # winner's color
        return False

    def _is_finished_y(self):
        for z in xrange(4):
            for x in xrange(4):
                if is_same_non0([self.get(x,y,z) for y in xrange(4)]):
                    return self.get(x,0,z)
        return False

    def _is_finished_z(self):
        for x in xrange(4):
            for y in xrange(4):
                if is_same_non0([self.get(x,y,z) for z in xrange(4)]):
                    return self.get(x,y,0)
        return False

    def _is_finished_xy(self):
        for z in xrange(4):
            if is_same_non0([self.get(x,y,z) for x,y in [(0,0), (1,1), (2,2), (3,3)]]):
                return self.get(0,0,z)
            if is_same_non0([self.get(x,y,z) for x,y in [(0,3), (1,2), (2,1), (3,0)]]):
                return self.get(0,3,z)
        return False

    def _is_finished_yz(self):
        for x in xrange(4):
            if is_same_non0([self.get(x,y,z) for y,z in [(0,0), (1,1), (2,2), (3,3)]]):
                return self.get(x,0,0)
            if is_same_non0([self.get(x,y,z) for y,z in [(0,3), (1,2), (2,1), (3,0)]]):
                return self.get(x,0,3)
        return False

    def _is_finished_zx(self):
        for y in xrange(4):
            if is_same_non0([self.get(x,y,z) for z,x in [(0,0), (1,1), (2,2), (3,3)]]):
                return self.get(0,y,0)
            if is_same_non0([self.get(x,y,z) for z,x in [(0,3), (1,2), (2,1), (3,0)]]):
                return self.get(0,y,3)
        return False
        
    def _is_finished_diag(self):
        if is_same_non0([self.get(x,y,z) for x,y,z in [(0,0,0), (1,1,1), (2,2,2), (3,3,3)]]):
            return self.get(0,0,0)
        if is_same_non0([self.get(x,y,z) for x,y,z in [(0,0,3), (1,1,2), (2,2,1), (3,3,0)]]):
            return self.get(0,0,0)
        if is_same_non0([self.get(x,y,z) for x,y,z in [(0,3,0), (1,2,1), (2,1,2), (3,0,3)]]):
            return self.get(0,0,0)
        if is_same_non0([self.get(x,y,z) for x,y,z in [(3,0,0), (2,1,1), (1,2,2), (0,3,3)]]):
            return self.get(0,0,0)
        return False

    def is_lizhi(self):
        r = [self._is_lizhi_x(),
             self._is_lizhi_y(),
             self._is_lizhi_z(),
             self._is_lizhi_xy(),
             self._is_lizhi_yz(),
             self._is_lizhi_zx(),
            self._is_lizhi_diag()]
        for lizhis in r:
            for color,pos in lizhis:
                yield color,pos

    def _is_lizhi_x(self):
        for y in xrange(4):
            for z in xrange(4):
                color,pos = has0_and_same([self.get(x,y,z) for x in xrange(4)])
                if color:
                    yield (color, (pos,y,z))

    def _is_lizhi_y(self):
        for z in xrange(4):
            for x in xrange(4):
                color,pos = has0_and_same([self.get(x,y,z) for y in xrange(4)])
                if color:
                    yield (color, (x,pos,z))


    def _is_lizhi_z(self):
        for x in xrange(4):
            for y in xrange(4):
                color,pos = has0_and_same([self.get(x,y,z) for z in xrange(4)])
                if color:
                    yield (color, (x,y,pos))

    def _is_lizhi_xy(self):
        for z in xrange(4):
            color,pos = has0_and_same([self.get(x,y,z) for x,y in [(0,0), (1,1), (2,2), (3,3)]])
            if color:
                yield (color, [(0,0,z), (1,1,z), (2,2,z), (3,3,z)][pos])
            color,pos = has0_and_same([self.get(x,y,z) for x,y in [(0,3), (1,2), (2,1), (3,0)]])
            if color:
                yield (color, [(0,3,z), (1,2,z), (2,1,z), (3,0,z)][pos])


    def _is_lizhi_yz(self):
        for x in xrange(4):
            color,pos = has0_and_same([self.get(x,y,z) for y,z in [(0,0), (1,1), (2,2), (3,3)]])
            if color:
                yield (color, [(x,0,0), (x,1,1), (x,2,2), (x,3,3)][pos])
            color,pos = has0_and_same([self.get(x,y,z) for y,z in [(0,3), (1,2), (2,1), (3,0)]])
            if color:
                yield (color, [(x,0,3), (x,1,2), (x,2,1), (x,3,0)][pos])


    def _is_lizhi_zx(self):
        for y in xrange(4):
            color,pos = has0_and_same([self.get(x,y,z) for z,x in [(0,0), (1,1), (2,2), (3,3)]])
            if color:
                yield (color, [(0,y,0), (1,y,1), (2,y,2), (3,y,3)][pos])
            color,pos = has0_and_same([self.get(x,y,z) for z,x in [(0,3), (1,2), (2,1), (3,0)]])
            if color:
                yield (color, [(0,y,3), (1,y,2), (2,y,1), (3,y,0)][pos])

        
    def _is_lizhi_diag(self):
        color,pos = has0_and_same([self.get(x,y,z) for x,y,z in [(0,0,0), (1,1,1), (2,2,2), (3,3,3)]])
        if color:
            yield (color, [(0,0,0), (1,1,1), (2,2,2), (3,3,3)][pos])
        color,pos = has0_and_same([self.get(x,y,z) for x,y,z in [(0,0,3), (1,1,2), (2,2,1), (3,3,0)]])
        if color:
            yield (color, [(0,0,3), (1,1,2), (2,2,1), (3,3,0)][pos])
        color,pos = has0_and_same([self.get(x,y,z) for x,y,z in [(0,3,0), (1,2,1), (2,1,2), (3,0,3)]])
        if color:
            yield (color, [(0,3,0), (1,2,1), (2,1,2), (3,0,3)][pos])
        color,pos = has0_and_same([self.get(x,y,z) for x,y,z in [(3,0,0), (2,1,1), (1,2,2), (0,3,3)]])
        if color:
            yield (color, [(3,0,0), (2,1,1), (1,2,2), (0,3,3)][pos])

    def show(self):
        self.output(""" BOARD:
          %c    %c    %c    %c
          %c    %c    %c    %c
          %c    %c    %c    %c
          %c    %c    %c    %c

          %c    %c    %c    %c
          %c    %c    %c    %c
          %c    %c    %c    %c
          %c    %c    %c    %c

          %c    %c    %c    %c
          %c    %c    %c    %c
          %c    %c    %c    %c
          %c    %c    %c    %c

          %c    %c    %c    %c
          %c    %c    %c    %c
          %c    %c    %c    %c
          %c    %c    %c    %c
        """ % tuple([["|","B","W"][self.get(x,y,z)] for y in xrange(4) for z in xrange(4) for x in xrange(4)]))
        return

    def output(self, mes, rt=True):
        print mes
        if self.s and self.conn:
            if rt:
                self.conn.send(mes+"\n")
            else:
                self.conn.send(mes)
        return

    def get_input(self, mes, is_online):
        if is_online and self.s and self.conn:
            self.output(mes, rt=False)
            data = self.conn.recv(1024)
        else:
            data = raw_input(mes)
        return data
        
    def game_online(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((HOST, PORT))
        self.s.listen(1)
        self.conn, self.addr = self.s.accept()
        print 'Connected by', self.addr
        print "Starting game...."
        self.game()
        self.conn.close()
        return

    def game(self):
        self.output("")
        self.output("<<  Yonmoku3D  >>")
        self.show()
        while True:
            self.output("[ BLACK's turn ]")
            x,y = [int(i) for i in self.get_input("X,Y >", is_online=False).split(",")]
            self.put(x,y,BLACK)
            if self.is_finished():
                self.output("BLACK win!!")
                return
            self.show()

            self.output("[WHITE's turn ]")
            x,y = [int(i) for i in self.get_input("X,Y >", is_online=True).split(",")]
            self.put(x,y,WHITE)
            if self.is_finished():
                self.output("WHITE win!!")
                return
            self.show()

class Player(object):
    def __init__(self, board):
        self.board = board
        self.s = None
        self.conn = None
        self.addr = None

    def connect(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((HOST,PORT))
        data = self.recv(1024)
        print data
        return


if __name__ == "__main__":
    b = Board()
    b.game_online()
    

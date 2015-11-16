#!/usr/bin/env python
#-*- coding:utf-8 -*-

from array import array
import socket
import os.path
from base import *

class Board(object):
    def __init__(self, history_file=None):
        self.board = array("B", (0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0))
        self.history = array("B")
        self.history_file = history_file
        self.sock = None
        self.conn = None
        self.addr = None
        self.nextColor = BLACK
        self.winner = None


    def get_height(self, x,y):
        # return the bottom blank in (x,y)
        for i in xrange(4):
            if not (self.board[y*4+x] & (0b10 << 2*i)):
                # index i (from the bottom) is first blank position
                return i
        raise ValueError("This tower is full!")

    def remove_last_put(self, color):
        if color == WHITE:
            x = (self.history[-1] & 0b00001100) >> 2
            y = (self.history[-1] & 0b00000011)
            self.history[-1] &= 0b11110000
        else:
            x = (self.history[-1] & 0b11000000) >> 6
            y = (self.history[-1] & 0b00110000) >> 4
            self.history.pop(-1)
        try:
            i = self.get_height(x,y) - 1
        except ValueError:
            i = 3
        assert i >= 0
        self.board[y*4+x] &= ~(color << 2*i) #bit clear
        return

    def put(self, x,y,color):
        # color = BLACK(0b10) or WHITE(0b11)        
        try:
            i = self.get_height(x,y)
        except ValueError:
            raise ValueError("This tower is full!")
        # put black or white one
        self.board[y*4+x] |= (color << 2*i)
        # suppose BLACK and WHITE put alternately (BLACK must be first!)
        # each char(1byte) in self.history is filled with every two moves
        if color == WHITE:# (took the second move)
            self.history[-1] += ((x<<2)+y)
        else: #color == BLACK(took the first move)
            self.history.append( ((x<<2)+y) << 4)
            return


    
    def get(self, x,y,z):
        # z is index from the bottom
        if not self.board[y*4+x] & (0b11 << 2*z):
            return BLANK
        elif (self.board[y*4+x] & (0b11 << 2*z))>>2*z == BLACK:
              return BLACK
        elif (self.board[y*4+x] & (0b11 << 2*z))>>2*z == WHITE:
              return WHITE

    def user_put(self, pos,color):
        # eg. pos = "A1" -> y=0,x=0
        if pos[0] == "A":
            y = 0
        elif pos[0] == "B":
            y = 1
        elif pos[0] == "C":
            y = 2
        elif pos[0] == "D":
            y = 3
        else:
            raise ValueError("Invalid board position!")
        if pos[1] == "1":
            x = 0
        elif pos[1] == "2":
            x = 1
        elif pos[1] == "3":
            x = 2
        elif pos[1] == "4":
            x = 3
        else:
            raise ValueError("Invalid board position!")
        return self.put(x,y,color)

    def user_get(self, pos):
        # eg. pos = "A1" -> y=0,x=0
        if pos[0] == "A":
            y = 0
        elif pos[0] == "B":
            y = 1
        elif pos[0] == "C":
            y = 2
        elif pos[0] == "D":
            y = 3
        else:
            raise ValueError("Invalid board position!")
        if pos[1] == "1":
            x = 0
        elif pos[1] == "2":
            x = 1
        elif pos[1] == "3":
            x = 2
        elif pos[1] == "4":
            x = 3
        else:
            raise ValueError("Invalid board position!")
        return self.get(x,y)
            
    def dump_history(self):
        if not self.history_file: return
        if os.path.getsize(self.history_file) > 1000000000:
            # if history file is over 1GB, drop the current data
            return
        else:
            # three bytes of zero in a row means the end of the game
            self.history.append(0)
            self.history.append(0)
            self.history.append(0)
            f = open(self.history_file, "ab")
            self.history.tofile(f)
            f.close()
            return
        
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
            self.dump_history()
            return BLACK
        elif WHITE in r:
            self.dump_history()
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
                color,x = has0_and_same([self.get(x,y,z) for x in xrange(4)])
                if color:
                    yield (color, (x,y,z))

    def _is_lizhi_y(self):
        for z in xrange(4):
            for x in xrange(4):
                color,y = has0_and_same([self.get(x,y,z) for y in xrange(4)])
                if color:
                    yield (color, (x,y,z))


    def _is_lizhi_z(self):
        for x in xrange(4):
            for y in xrange(4):
                color,z = has0_and_same([self.get(x,y,z) for z in xrange(4)])
                if color:
                    yield (color, (x,y,z))

    def _is_lizhi_xy(self):
        for z in xrange(4):
            color,i = has0_and_same([self.get(x,y,z) for x,y in ((0,0), (1,1), (2,2), (3,3))])
            if color:
                yield (color, ((0,0,z), (1,1,z), (2,2,z), (3,3,z))[i])
            color,i = has0_and_same([self.get(x,y,z) for x,y in ((0,3), (1,2), (2,1), (3,0))])
            if color:
                yield (color, ((0,3,z), (1,2,z), (2,1,z), (3,0,z))[i])


    def _is_lizhi_yz(self):
        for x in xrange(4):
            color,i = has0_and_same([self.get(x,y,z) for y,z in ((0,0), (1,1), (2,2), (3,3))])
            if color:
                yield (color, ((x,0,0), (x,1,1), (x,2,2), (x,3,3))[i])
            color,i = has0_and_same([self.get(x,y,z) for y,z in ((0,3), (1,2), (2,1), (3,0))])
            if color:
                yield (color, ((x,0,3), (x,1,2), (x,2,1), (x,3,0))[i])


    def _is_lizhi_zx(self):
        for y in xrange(4):
            color,i = has0_and_same([self.get(x,y,z) for z,x in ((0,0), (1,1), (2,2), (3,3))])
            if color:
                yield (color, ((0,y,0), (1,y,1), (2,y,2), (3,y,3))[i])
            color,i = has0_and_same([self.get(x,y,z) for z,x in ((0,3), (1,2), (2,1), (3,0))])
            if color:
                yield (color, ((3,y,0), (2,y,1), (1,y,2), (0,y,3))[i])

        
    def _is_lizhi_diag(self):
        color,i = has0_and_same([self.get(x,y,z) for x,y,z in ((0,0,0), (1,1,1), (2,2,2), (3,3,3))])
        if color:
            yield (color, ((0,0,0), (1,1,1), (2,2,2), (3,3,3))[i])
        color,i = has0_and_same([self.get(x,y,z) for x,y,z in ((0,0,3), (1,1,2), (2,2,1), (3,3,0))])
        if color:
            yield (color, ((0,0,3), (1,1,2), (2,2,1), (3,3,0))[i])
        color,i = has0_and_same([self.get(x,y,z) for x,y,z in ((0,3,0), (1,2,1), (2,1,2), (3,0,3))])
        if color:
            yield (color, ((0,3,0), (1,2,1), (2,1,2), (3,0,3))[i])
        color,i = has0_and_same([self.get(x,y,z) for x,y,z in ((3,0,0), (2,1,1), (1,2,2), (0,3,3))])
        if color:
            yield (color, ((3,0,0), (2,1,1), (1,2,2), (0,3,3))[i])
    def get_number_of_lizhis(self, ):
        return sum((sum(1 for _ in self._is_lizhi_x()),
                    sum(1 for _ in self._is_lizhi_y()),
                    sum(1 for _ in self._is_lizhi_z()),
                    sum(1 for _ in self._is_lizhi_xy()),
                    sum(1 for _ in self._is_lizhi_yz()),
                    sum(1 for _ in self._is_lizhi_zx()),
                    sum(1 for _ in self._is_lizhi_diag())))
        
    def get_lizhis(self, x,y,z, color):
        # return number of lizhis if mycolor is put on (x,y,z)
        numBefore = self.get_number_of_lizhis()
        self.put(x,y,color)
        numAfter = self.get_number_of_lizhis()
        self.remove_last_put(color)
        return numAfter - numBefore

    def get_clearlines(self, x,y,z, opponent_color):
        count = 3
        #x
        if opponent_color in [self.get(x_,y,z) for x_ in xrange(4)]:
            count -= 1
        #y
        if opponent_color in [self.get(x,y_,z) for y_ in xrange(4)]:
            count -= 1
        #z
        if opponent_color in [self.get(x,y,z_) for z_ in xrange(4)]:
            count -= 1
        #xy
        if (x,y) in ((0,0),(1,1),(2,2),(3,3)):
            count += 1
            if opponent_color in [self.get(x_,y_,z) for x_,y_ in ((0,0),(1,1),(2,2),(3,3))]:
                count -= 1
        elif (x,y) in ((0,3), (1,2), (2,1), (3,0)):
            count += 1
            if opponent_color in [self.get(x_,y_,z) for x_,y_ in ((0,3), (1,2), (2,1), (3,0))]:
                count -= 1
        #yz
        if (y,z) in ((0,0),(1,1),(2,2),(3,3)):
            count += 1
            if opponent_color in [self.get(x,y_,z_) for y_,z_ in ((0,0),(1,1),(2,2),(3,3))]:
                count -= 1
        elif (y,z) in ((0,3), (1,2), (2,1), (3,0)):
            count += 1
            if opponent_color in [self.get(x,y_,z_) for y_,z_ in ((0,3), (1,2), (2,1), (3,0))]:
                count -= 1
        #zx
        if (z,x) in ((0,0),(1,1),(2,2),(3,3)):
            count += 1
            if opponent_color in [self.get(x_,y,z_) for z_,x_ in ((0,0),(1,1),(2,2),(3,3))]:
                count -= 1
        elif (z,x) in ((0,3), (1,2), (2,1), (3,0)):
            count += 1
            if opponent_color in [self.get(x_,y,z_) for z_,x_ in ((0,3), (1,2), (2,1), (3,0))]:
                count -= 1
        #diag
        if (x,y,z) in ((0,0,0), (1,1,1), (2,2,2), (3,3,3)):
            count += 1
            if opponent_color in [self.get(x_,y_,z_) for x_,y_,z_ in ((0,0,0), (1,1,1), (2,2,2), (3,3,3))]:
                count -= 1
        elif (x,y,z) in ((0,0,3), (1,1,2), (2,2,1), (3,3,0)):
            count += 1
            if opponent_color in [self.get(x_,y_,z_) for x_,y_,z_ in ((0,0,3), (1,1,2), (2,2,1), (3,3,0))]:
                count -= 1
        elif (x,y,z) in ((0,3,0), (1,2,1), (2,1,2), (3,0,3)):
            count += 1
            if opponent_color in [self.get(x_,y_,z_) for x_,y_,z_ in ((0,3,0), (1,2,1), (2,1,2), (3,0,3))]:
                count -= 1
        elif (x,y,z) in ((3,0,0), (2,1,1), (1,2,2), (0,3,3)):
            count += 1
            if opponent_color in [self.get(x_,y_,z_) for x_,y_,z_ in ((3,0,0), (2,1,1), (1,2,2), (0,3,3))]:
                count -= 1
        return count

    def get_scene_dict(self):
        """ BOARD:
              1    2    3    4
              %c    %c    %c    %c
              %c    %c    %c    %c
              %c    %c    %c    %c
          A:  %c    %c    %c    %c

              %c    %c    %c    %c
              %c    %c    %c    %c
              %c    %c    %c    %c
          B:  %c    %c    %c    %c

              %c    %c    %c    %c
              %c    %c    %c    %c
              %c    %c    %c    %c
          C:  %c    %c    %c    %c

              %c    %c    %c    %c
              %c    %c    %c    %c
              %c    %c    %c    %c
          D:  %c    %c    %c    %c
        """
        return [("A",[[["|","","B","W"][self.get(x,0,z)] for x in xrange(4)] for z in (3,2,1,0)]),
                ("B",[[["|","","B","W"][self.get(x,1,z)] for x in xrange(4)] for z in (3,2,1,0)]),
                ("C",[[["|","","B","W"][self.get(x,2,z)] for x in xrange(4)] for z in (3,2,1,0)]),
                ("D",[[["|","","B","W"][self.get(x,3,z)] for x in xrange(4)] for z in (3,2,1,0)]),
                ]
    def get_scene_list(self):
        return [
            [
                [["|","","B","W"][self.get(x,y,z)] for z in xrange(4)
             ] for y in xrange(4)
            ] for x in xrange(4)]


    def show(self):
        self.output(""" BOARD:
              1    2    3    4
              %c    %c    %c    %c
              %c    %c    %c    %c
              %c    %c    %c    %c
          A:  %c    %c    %c    %c

              %c    %c    %c    %c
              %c    %c    %c    %c
              %c    %c    %c    %c
          B:  %c    %c    %c    %c

              %c    %c    %c    %c
              %c    %c    %c    %c
              %c    %c    %c    %c
          C:  %c    %c    %c    %c

              %c    %c    %c    %c
              %c    %c    %c    %c
              %c    %c    %c    %c
          D:  %c    %c    %c    %c
        """ % tuple([["|","","B","W"][self.get(x,y,z)] for y in xrange(4) for z in (3,2,1,0) for x in xrange(4)]))
        return

    def output(self, mes, rt=True):
        print mes
        if self.sock and self.conn:
            if rt:
                self.conn.send(mes+"\n")
            else:
                self.conn.send(mes)
        return

    def get_input(self, mes, is_online):
        if is_online and self.sock and self.conn:
            self.output(mes, rt=False)
            data = self.conn.recv(1024)
        else:
            data = raw_input(mes)
        return data
        
    def game_online(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((HOST, PORT))
        self.sock.listen(1)
        self.conn, self.addr = self.sock.accept()
        print 'Connected by', self.addr
        mode = self.get_input("mode:", is_online=True)
        if mode == "machine":
            self.machine_mode = True
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
            while True:
                pos = self.get_input("Where to put? >", is_online=False)
                try:
                    self.user_put(pos,BLACK)
                except ValueError,message:
                    self.output(message)
                    continue
                else:
                    break
            if self.is_finished():
                self.show()
                self.output("BLACK win!!")
                return
            self.show()

            self.output("[WHITE's turn ]")
            while True:
                pos = self.get_input("Where to put? >", is_online=True)
                try:
                    self.user_put(pos,WHITE)
                except ValueError, message:
                    self.output(message)
                    continue
                else:
                    break
            if self.is_finished():
                self.show()
                self.output("WHITE win!!")
                return
            self.show()


if __name__ == "__main__":
    b = Board()
    b.game()
    

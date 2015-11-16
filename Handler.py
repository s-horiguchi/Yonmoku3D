#!/usr/bin/env python
#-*- coding:utf-8 -*-

import logging
import tornado.escape
import tornado.web
import tornado.websocket

from tornado.httputil import HTTPServerRequest

from tornado.options import options


from base import *
from Board import Board

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", board=SocketHandler.board.get_scene_dict())

class SocketHandler(tornado.websocket.WebSocketHandler):
    board = Board(options.history)

    waiters = set()
    players = [None,None] #Black player, White player

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        SocketHandler.waiters.add(self)
        # first two waiters become players
        if SocketHandler.players[0] == None:
            SocketHandler.players[0] = self
        elif SocketHandler.players[1] == None:
            SocketHandler.players[1] = self
        else:
            pass
        #print "open", SocketHandler.players
        self.update_board()

        
    def on_close(self):
        SocketHandler.waiters.remove(self)
        if self in SocketHandler.players:
            SocketHandler.players[SocketHandler.players.index(self)] = None
            #if SocketHandler.board.winner:
            #    SocketHandler.board = Board(options.history)
        #print "close", SocketHandler.players

    def winnerCOLOR(self, opponent=False, string=False):
        # this can be called by non-player
        if string:
            b = "BLACK"
            w = "WHITE"
        else:
            b = BLACK
            w = WHITE
        if not opponent:
            if SocketHandler.board.winner == BLACK:
                return b # BLACK is player1
            elif SocketHandler.board.winner == WHITE:
                return w # WHITE is player2
            else:
                raise
        else:
            if SocketHandler.board.winner == BLACK:
                return w
            elif SocketHandler.board.winner == WHITE:
                return b
            else:
                raise

        
    def COLOR(self, opponent=False, string=False):
        # this will fail when self is not in players[]
        if string:
            b = "BLACK"
            w = "WHITE"
        else:
            b = BLACK
            w = WHITE
        if not opponent:
            if SocketHandler.players.index(self) == 0:
                return b # BLACK is player1
            elif SocketHandler.players.index(self) == 1:
                return w # WHITE is player2
            else:
                raise
        else:
            if SocketHandler.players.index(self) == 0:
                return w
            elif SocketHandler.players.index(self) == 1:
                return b
            else:
                raise

    def opponent_player(self):
        # this will fail when self is not in players[]
        if SocketHandler.players.index(self) == 0:
            return SocketHandler.players[1]
        elif SocketHandler.players.index(self) == 1:
            return SocketHandler.players[0]
        else:
            raise

    def update_board(self):
        logging.info("called update_board from "+str(self))
        SocketHandler.board.show()

        if SocketHandler.board.winner:
            self.gameover()
            return
        json = {}
        json["type"] = "SUCCESS"
        if SocketHandler.board.nextColor == BLACK:
            json["turn"] = "BLACK"
        else:
            json["turn"] = "WHITE"
        json["html"] = tornado.escape.to_basestring(self.render_string("board.html", board=SocketHandler.board.get_scene_dict()))
        json["scene"] = SocketHandler.board.get_scene_list()

        # in order to send message in a correct order,
        # updates need to be sent to caller first, then audience, lastly opponent.
        # if sent opponent first, AI will think of new move and send new update while you call write_message() of AI
        # ,which makes player receive AI's new move first, and his own move next!
        # if sent audience last, audience will receive the all moves in a reverse order(when it is AI vs AI)
        #TODO: make the AI thinking function asynchronous
        
        if self in SocketHandler.players: #may always be true(except called from open())
            #caller
            json["connection"] = "<font color='red'>A.I.</font> vs. <b>YOU</b><br>AUDIENCE:%d" % (len(SocketHandler.waiters)-2)
            json["you"] = self.COLOR(string=True)
            self.write_message(json)
            #audience
            for waiter in SocketHandler.waiters:
                if waiter not in SocketHandler.players:
                    json["connection"] = "<font color='red'>A.I.</font> vs. PLAYER<br>AUDIENCE:%d" % (len(SocketHandler.waiters)-2)
                    json["you"] = "AUDIENCE"
                    try:
                        waiter.write_message(json)
                    except:
                        logging.error("Error sending message", exc_info=True)
            #opponent
            if self.opponent_player():
                json["connection"] = "<font color='red'>A.I.</font> vs. <b>YOU</b><br>AUDIENCE:%d" % (len(SocketHandler.waiters)-2)
                json["you"] = self.COLOR(opponent=True, string=True)
                self.opponent_player().write_message(json)
            
        else:
            #audience
            for waiter in SocketHandler.waiters:
                if waiter not in SocketHandler.players:
                    json["connection"] = "<font color='red'>A.I.</font> vs. PLAYER<br>AUDIENCE:%d" % (len(SocketHandler.waiters)-2)
                    json["you"] = "AUDIENCE"
                    try:
                        waiter.write_message(json)
                    except:
                        logging.error("Error sending message", exc_info=True)
            #second player, first
            json["connection"] = "<font color='red'>A.I.</font> vs. <b>YOU</b><br>AUDIENCE:%d" % (len(SocketHandler.waiters)-2)
            json["you"] = SocketHandler.players[1].COLOR(string=True)
            SocketHandler.players[1].write_message(json)
            #first player, next
            json["connection"] = "<font color='red'>A.I.</font> vs. <b>YOU</b><br>AUDIENCE:%d" % (len(SocketHandler.waiters)-2)
            json["you"] = SocketHandler.players[0].COLOR(string=True)
            SocketHandler.players[0].write_message(json)
            

    def reset_board(self):
        SocketHandler.board = Board(options.history)
        json = {}
        json["type"] = "RESET"
        for waiter in SocketHandler.waiters:
            if waiter in SocketHandler.players:
                json["you"] = waiter.COLOR(string=True)
                json["connection"] = "<font color='red'>A.I.</font> vs. <b>YOU</b><br>AUDIENCE:%d" % (len(SocketHandler.waiters)-2)

            else:
                json["connection"] = "<font color='red'>A.I.</font> vs. PLAYER<br>AUDIENCE:%d" % (len(SocketHandler.waiters)-2)
                json["you"] = "AUDIENCE"

            try:
                waiter.write_message(json)
            except:
                logging.error("Error sending message", exc_info=True)
        self.update_board()

    def gameover(self):
        # this is called someone requested for update after gameover
        # this method is called by anyone (not only winner)
        if not SocketHandler.board.winner:
            raise
        json = {}
        json["type"] = "GAMEOVER"
        
        json["html"] = tornado.escape.to_basestring(self.render_string("board.html", board=SocketHandler.board.get_scene_dict()))
        json["scene"] = SocketHandler.board.get_scene_list()
        if self in SocketHandler.players:
            json["connection"] = "<font color='red'>A.I.</font> vs. <b>YOU</b><br>AUDIENCE:%d" % (len(SocketHandler.waiters)-2)
            if self.COLOR() == self.winnerCOLOR(): # for winner
                json["info"] = "YOU WIN!!"
                json["you"] = self.winnerCOLOR(string=True)
                self.write_message(json)
            else: # for looser
                json["info"] = "YOU LOSE..."
                json["you"] = self.winnerCOLOR(opponent=True, string=True)
                self.write_message(json)
        else:
            # for audience
            json["info"] = "%s WIN!!" % self.winnerCOLOR(string=True)
            json["you"] = "AUDIENCE"
            json["connection"] = "<font color='red'>A.I.</font> vs. PLAYER<br>AUDIENCE:%d" % (len(SocketHandler.waiters)-2)
            self.write_message(json)

        
    def win_gameover(self):
        logging.info(self.winnerCOLOR(string=True)+" win!!")
        # this method should be called once just after the game is over
        # this is designed to be called by winner
        if not SocketHandler.board.winner:
            raise

        json = {}
        json["type"] = "GAMEOVER"
        
        json["html"] = tornado.escape.to_basestring(self.render_string("board.html", board=SocketHandler.board.get_scene_dict()))
        json["scene"] = SocketHandler.board.get_scene_list()
        json["connection"] = "<font color='red'>A.I.</font> vs. <b>YOU</b><br>AUDIENCE:%d" % (len(SocketHandler.waiters)-2)
        # for winner
        json["info"] = "YOU WIN!!"
        json["you"] = self.winnerCOLOR(string=True)
        self.write_message(json)
        # for looser
        json["info"] = "YOU LOSE..."
        json["you"] = self.winnerCOLOR(opponent=True, string=True)
        self.opponent_player().write_message(json)
        # for audience
        json["info"] = "%s WIN!!" % self.winnerCOLOR(string=True)
        json["you"] = "AUDIENCE"
        json["connection"] = "<font color='red'>A.I.</font> vs. PLAYER<br>AUDIENCE:%d" % (len(SocketHandler.waiters)-2)
        for waiter in SocketHandler.waiters:
            if not waiter in SocketHandler.players:
                try:
                    waiter.write_message(json)
                except:
                    logging.error("Error sending message", exc_info=True)

        
    def on_message(self, message):
        logging.info("got message %r", message)
        parsed = tornado.escape.json_decode(message)
        json = {}

        if self in SocketHandler.players:
            json["connection"] = "<font color='red'>A.I.</font> vs. <b>YOU</b><br>AUDIENCE:%d" % (len(SocketHandler.waiters)-2)
        else:
            json["connection"] = "<font color='red'>A.I.</font> vs. PLAYER<br>AUDIENCE:%d" % (len(SocketHandler.waiters)-2)

        if parsed["type"] == "MOVE":
            if SocketHandler.board.winner:
                json["type"] = "ERROR"
                json["html"] = "Game Is Over!"
                self.write_message(json)
                return
            if self in SocketHandler.players and SocketHandler.board.nextColor==self.COLOR():
                try:
                    SocketHandler.board.user_put(parsed["body"], self.COLOR())
                except (ValueError, IndexError),mes:
                    json["type"] = "ERROR"
                    json["html"] = str(mes)
                    self.write_message(json)
                else:
                    if SocketHandler.board.is_finished():
                        SocketHandler.board.winner = self.COLOR()
                        self.win_gameover()
                    else:
                        SocketHandler.board.nextColor = self.COLOR(opponent=True)
                        self.update_board()
            else:
                json["type"] = "ERROR"
                json["html"] = "Not your turn!"
                self.write_message(json)
        elif parsed["type"] == "RESET":
            #if self in SocketHandler.players:
            #    self.reset_board()
            self.reset_board()


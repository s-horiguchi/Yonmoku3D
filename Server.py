#!/usr/bin/env python
#-*- coding:utf-8 -*-

from base import *
from Board import Board

import logging
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
import os.path
import uuid

#from tornado.concurrent import Future
#from tornado import gen
from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/socket", SocketHandler),
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            debug=options.debug,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class BoardWeb(Board):
    def __init__(self):
        super(BoardWeb, self).__init__()
        self.nextColor = BLACK
        self.winner = None

    def get_scene(self):
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
        
        

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", board=SocketHandler.board.get_scene())

class SocketHandler(tornado.websocket.WebSocketHandler):
    board = BoardWeb()
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
        print "open", SocketHandler.players
        self.update_board()

        
    def on_close(self):
        SocketHandler.waiters.remove(self)
        if self in SocketHandler.players:
            SocketHandler.players[SocketHandler.players.index(self)] = None
            #if SocketHandler.board.winner:
            #    SocketHandler.board = BoardWeb()
        print "close", SocketHandler.players

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
        if SocketHandler.board.winner:
            self.gameover()
            return
        json = {}
        json["type"] = "SUCCESS"
        if SocketHandler.board.nextColor == BLACK:
            json["turn"] = "BLACK"
        else:
            json["turn"] = "WHITE"
        json["html"] = tornado.escape.to_basestring(self.render_string("board.html", board=SocketHandler.board.get_scene()))
        for waiter in SocketHandler.waiters:
            if waiter in SocketHandler.players:
                json["you"] = waiter.COLOR(string=True)
            else:
                json["you"] = "AUDIENCE"

            try:
                waiter.write_message(json)
            except:
                logging.error("Error sending message", exc_info=True)
    
    def gameover(self):
        # this is called someone requested for update after gameover
        # this method is called by anyone (not only winner)
        if not SocketHandler.board.winner:
            raise
        json = {}
        json["type"] = "GAMEOVER"
        
        json["html"] = tornado.escape.to_basestring(self.render_string("board.html", board=SocketHandler.board.get_scene()))
        if self in SocketHandler.players:
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
            self.write_message(json)

        
    def win_gameover(self):
        # this method should be called once just after the game is over
        # this is designed to be called by winner
        if not SocketHandler.board.winner:
            raise

        json = {}
        json["type"] = "GAMEOVER"
        
        json["html"] = tornado.escape.to_basestring(self.render_string("board.html", board=SocketHandler.board.get_scene()))
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
            if self in SocketHandler.players:
                SocketHandler.board = BoardWeb()
                self.update_board()
                
            
def main():
    parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

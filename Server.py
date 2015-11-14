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
import random

from tornado.util import ObjectDict
from tornado.httputil import HTTPServerRequest

from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")
define("history", default="records.dump", help="save records of game to the given file")

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
        super(BoardWeb, self).__init__(options.history)
        self.nextColor = BLACK
        self.winner = None

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

        

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", board=SocketHandler.board.get_scene_dict())

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
        #print "open", SocketHandler.players
        self.update_board()

        
    def on_close(self):
        SocketHandler.waiters.remove(self)
        if self in SocketHandler.players:
            SocketHandler.players[SocketHandler.players.index(self)] = None
            #if SocketHandler.board.winner:
            #    SocketHandler.board = BoardWeb()
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
        ai = None

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

        for waiter in SocketHandler.waiters:
            if isinstance(waiter, AIPlayer):
                ai = waiter
                continue
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

        if ai:
            ai.moveAI2()
    
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
            if self in SocketHandler.players:
                SocketHandler.board = BoardWeb()
                self.update_board()

class AIPlayer(SocketHandler):
    def __init__(self, application, request=None, **kwargs):
        #super(AIPlayer,self).__init__(application, request, **kwargs)
        # to avoid error in self.render_string
        self.application = application
        self.request = HTTPServerRequest(method="POST",
                                         uri="/socket",
                                         headers={"Accept-Language":"ja,en-US;q=0.8,en;q=0.6"})
        self.ui = ObjectDict((n, self._ui_method(m)) for n, m in
                             application.ui_methods.items())

        #add myself to the waiters
        self.open()
        

    def is_urgent(self,x,y,z):
        if z == 0 or SocketHandler.board.get(x,y,z-1) != BLANK:
            return True
        else:
            return False

    def random_valid_pos(self):
        while True:
            x = random.randint(0,3)
            y = random.randint(0,3)
            if SocketHandler.board.get(x,y,3) == BLANK:
                return x,y

    def moveAI1(self):
        if not self in SocketHandler.players or SocketHandler.board.nextColor != self.COLOR():
            #if it's not my turn, do nothing!
            return
        urgents = [(color,(pos[0],pos[1])) for color,pos in SocketHandler.board.is_lizhi() if self.is_urgent(pos[0],pos[1],pos[2])]
        print "urgents", urgents
        pos = None
        if len(urgents) == 1:
            pos = urgents[0][1]
            logging.info("AI decided one urgent move %s", str(pos))
        elif len(urgents) > 1:
            # winning the game is higher priority than preventing the oponent's winning
            for u in urgents:
                if u[0] == self.COLOR():
                    pos = u[1]
                    logging.info("AI selected one urgent move %s", str(pos))
            if not pos:
                pos = random.choice(urgents)[1]
                logging.info("AI randomly selected one urgent  move %s", str(pos))
        else:
            pos = self.random_valid_pos()
            logging.info("AI randomly decided new move %s", str(pos))


        SocketHandler.board.put(pos[0],pos[1], self.COLOR())
        #SocketHandler.board.show()
        if SocketHandler.board.is_finished():
            SocketHandler.board.winner = self.COLOR()
            self.win_gameover()
        else:
            SocketHandler.board.nextColor = self.COLOR(opponent=True)
            self.update_board()

    def moveAI2(self):
        if not self in SocketHandler.players or SocketHandler.board.nextColor != self.COLOR():
            #if it's not my turn, do nothing!
            return
        urgents = [(color,(pos[0],pos[1])) for color,pos in SocketHandler.board.is_lizhi() if self.is_urgent(pos[0],pos[1],pos[2])]
        print "urgents", urgents
        pos = None
        if len(urgents) == 1:
            pos = urgents[0][1]
            logging.info("AI decided one urgent move %s", str(pos))
        elif len(urgents) > 1:
            # winning the game is higher priority than preventing the oponent's winning
            for u in urgents:
                if u[0] == self.COLOR():
                    pos = u[1]
                    logging.info("AI selected one urgent move %s", str(pos))
            if not pos:
                pos = random.choice(urgents)[1]
                logging.info("AI randomly selected one urgent  move %s", str(pos))
        else:
            # no urgents
            nearlizhis = []
            for x in xrange(4):
                for y in xrange(4):
                    try:
                        z = SocketHandler.board.get_height(x,y)
                    except ValueError:
                        continue
                    else:
                        nearlizhis.append(((x,y),SocketHandler.board.get_lizhis(x,y,z,self.COLOR())))
            print "nearlizhi:",nearlizhis
            maxlizhi = max(nearlizhis,key=lambda c: c[1])[1]
            if maxlizhi > 0:
                # there are some positions where you will be lizhi if you put
                max_lizhi_cands = filter(lambda c: c[1] == maxlizhi, nearlizhis)
                logging.info("There are %d max lizhis" % len(max_lizhi_cands))
                print "max:",max_lizhi_cands
                pos = random.choice(max_lizhi_cands)[0]
                logging.info("AI randomly selected best move %s!" % str(pos))
            else:
                # no near lizhi positions
                cands = []
                for x in xrange(4):
                    for y in xrange(4):
                        try:
                            z = SocketHandler.board.get_height(x,y)
                        except ValueError:
                            continue
                        else:
                            cands.append(((x,y),SocketHandler.board.get_clearlines(x,y,z, self.COLOR(opponent=True))))
                print "cands:",cands
                best_cands = filter(lambda c: c[1] == max(cands,key=lambda c: c[1])[1], cands)
                logging.info("There are %d best candidates" % len(best_cands))
                print "best:",best_cands
                pos = random.choice(best_cands)[0]
                logging.info("AI randomly selected best move %s!" % str(pos))
            

        SocketHandler.board.put(pos[0], pos[1], self.COLOR())
        #SocketHandler.board.show()
        if SocketHandler.board.is_finished():
            SocketHandler.board.winner = self.COLOR()
            self.win_gameover()
        else:
            SocketHandler.board.nextColor = self.COLOR(opponent=True)
            self.update_board()

    def write_message(self, message, binary=False):
        #called by other players' SocketHandler instances
        #to notice updates (originally notice for connected browsers)
        if isinstance(message,dict):
            if message["type"] == "ERROR":
                #if something goes wrong, just run away
                self.on_close()
                return

            elif message["type"] == "GAMEOVER":
                if message["info"] == "YOU WIN!!":
                    pass
                elif message["info"] == "YOU LOSE...":
                    pass

            elif message["type"] == "SUCCESS":
                # won't called
                raise
        
                
            
def main():
    parse_command_line()
    app = Application()
    app.listen(options.port)
    ai = AIPlayer(app,None)

    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

#!/usr/bin/env python
#-*- coding:utf-8 -*-

import logging
from tornado.httputil import HTTPServerRequest
from tornado.util import ObjectDict
import random
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
import tornado.ioloop
import tornado.web

from base import *
from Handler import SocketHandler


EXECUTOR = ThreadPoolExecutor(max_workers=2)

def unblock(f):
    @tornado.web.asynchronous
    @wraps(f)
    def wrapper(*args, **kwargs):
        self = args[0]

        def callback(future):
            logging.info("called back!")
            self.thinking = False
            #SocketHandler.board.show()
            if SocketHandler.board.is_finished():
                SocketHandler.board.winner = self.COLOR()
                self.win_gameover()
            else:
                SocketHandler.board.nextColor = self.COLOR(opponent=True)
                self.update_board()

        EXECUTOR.submit(
            partial(f, *args, **kwargs)
        ).add_done_callback(
            lambda future: tornado.ioloop.IOLoop.instance().add_callback(
                partial(callback, future)))

    return wrapper


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
        # a flag to prevent double run on move()
        self.thinking = False
        #add myself to the waiters
        self.open()
        
    def is_urgent(self,x,y,z):
        if z == 0 or SocketHandler.board.get(x,y,z-1) != BLANK:
            return True
        else:
            return False

    @unblock
    def move(self):
        if not self in SocketHandler.players or SocketHandler.board.nextColor != self.COLOR():
            #if it's not my turn, do nothing!
            return
        urgents = [(color,(pos[0],pos[1])) for color,pos in SocketHandler.board.is_lizhi() if self.is_urgent(pos[0],pos[1],pos[2])]
        #print "urgents", urgents
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
            #print "nearlizhi:",nearlizhis
            maxlizhi = max(nearlizhis,key=lambda c: c[1])[1]
            if maxlizhi > 0:
                # there are some positions where you will be lizhi if you put
                max_lizhi_cands = filter(lambda c: c[1] == maxlizhi, nearlizhis)
                #logging.info("There are %d max lizhis" % len(max_lizhi_cands))
                #print "max:",max_lizhi_cands
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
                #print "cands:",cands
                best_cands = filter(lambda c: c[1] == max(cands,key=lambda c: c[1])[1], cands)
                #logging.info("There are %d best candidates" % len(best_cands))
                #print "best:",best_cands
                pos = random.choice(best_cands)[0]
                logging.info("AI randomly selected best move %s!" % str(pos))

        SocketHandler.board.put(pos[0], pos[1], self.COLOR())            
        time.sleep(0.5)
        

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
                if message["you"] == message["turn"]:
                    if not self.thinking:
                        self.thinking = True
                        self.move()
                    else:
                        logging.info("thinking now! prevented double move.")

            elif message["type"] == "RESET":
                logging.info("RESETTED @ai")
        
                
class RandomAIPlayer(AIPlayer):
    def __init__(self, application, request=None, **kwargs):
        super(RandomAIPlayer,self).__init__(application, request, **kwargs)

    def random_valid_pos(self):
        while True:
            x = random.randint(0,3)
            y = random.randint(0,3)
            if SocketHandler.board.get(x,y,3) == BLANK:
                return x,y

    @unblock
    def move(self):
        if not self in SocketHandler.players or SocketHandler.board.nextColor != self.COLOR():
            #if it's not my turn, do nothing!
            return
        urgents = [(color,(pos[0],pos[1])) for color,pos in SocketHandler.board.is_lizhi() if self.is_urgent(pos[0],pos[1],pos[2])]
        #print "urgents", urgents
        pos = None
        if len(urgents) == 1:
            pos = urgents[0][1]
            logging.info("[RandomAI]AI decided one urgent move %s", str(pos))
        elif len(urgents) > 1:
            # winning the game is higher priority than preventing the oponent's winning
            for u in urgents:
                if u[0] == self.COLOR():
                    pos = u[1]
                    logging.info("[RandomAI]AI selected one urgent move %s", str(pos))
            if not pos:
                pos = random.choice(urgents)[1]
                logging.info("[RandomAI]AI randomly selected one urgent  move %s", str(pos))
        else:
            pos = self.random_valid_pos()
            logging.info("[RandomAI]AI randomly decided new move %s", str(pos))

        SocketHandler.board.put(pos[0],pos[1], self.COLOR())
        time.sleep(0.5)



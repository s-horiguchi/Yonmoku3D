#!/usr/bin/env python
#-*- coding:utf-8 -*-

from base import *
from Board import Board

import logging
import tornado.escape
import tornado.ioloop
import tornado.web
import os.path
import uuid

from tornado.concurrent import Future
from tornado import gen
from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")


class BoardWeb(Board):
    def __init__(self):
        super(BoardWeb, self).__init__()
        self.waiters = set()

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
        return [("A",[[["|","","B","W"][self.get(0,y,z)] for y in xrange(4)] for z in (3,2,1,0)]),
                ("B",[[["|","","B","W"][self.get(1,y,z)] for y in xrange(4)] for z in (3,2,1,0)]),
                ("C",[[["|","","B","W"][self.get(2,y,z)] for y in xrange(4)] for z in (3,2,1,0)]),
                ("D",[[["|","","B","W"][self.get(3,y,z)] for y in xrange(4)] for z in (3,2,1,0)]),
                ]
        

    def wait_for_moves(self):
        result_future = Future()
        self.waiters.add(result_future)
        return result_future
        
    def cancel_wait(self, future):
        self.waiters.remove(future)
        future.set_result([])

    def new_moves(self):
        logging.info("Sending new move to %r listeners", len(self.waiters))
        
        for future in self.waiters:
            future.set_result(self.get_scene())
        self.waiters = set()
        
global_board = BoardWeb()

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        print global_board.get_scene()
        self.render("index.html", board=global_board.get_scene())

class MoveNewHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        self.set_header('Content-Type', 'application/json; charset="utf-8"')
        self.finish(kwargs.get("message"))

    def post(self):
        try:
            global_board.user_put(self.get_argument("button"),BLACK)
        except (ValueError, IndexError),mes:
            #self.set_status(418, reason=str(mes))
            #self.write_error(status_code=418, message=str(mes))
            self.send_error(501, message=str(mes))
            
        else:
            global_board.new_moves()
            self.render("board.html", board=global_board.get_scene())
            
class MoveUpdateHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def post(self):
        self.future = global_board.wait_for_moves()
        latest_scene = yield self.future
        if self.request.connection.stream.closed():
            return
        self.render("board.html", board=latest_scene)
        
    def on_connection_close(self):
        global_board.cancel_wait(self.future)
        
class BoardRestartHandler(tornado.web.RequestHandler):
    def post(self):
        global_board = BoardWeb()
        self.render("board.html", board=global_board.get_scene())

def main():
    parse_command_line()
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/a/move/new", MoveNewHandler),
            (r"/a/move/updates", MoveUpdateHandler),
            (r"/a/board/restart", BoardRestartHandler),
            ],
        cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=True,
        debug=options.debug,
        )
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

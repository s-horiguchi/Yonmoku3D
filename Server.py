#!/usr/bin/env python
#-*- coding:utf-8 -*-

import logging
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
import os.path

from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")
define("history", default="records.dump", help="save records of game to the given file")
define("AIvsAI", default=True, help="clients just watch A.I. vs. A.I.")

from base import *
from Board import Board
from Handler import MainHandler, SocketHandler
from AI import AIPlayer,RandomAIPlayer


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

            
def main():
    parse_command_line()
    app = Application()
    app.listen(options.port)
    ai = AIPlayer(app)
    if options.AIvsAI:
        ai2 = RandomAIPlayer(app)

    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

#TODO: ログの再生用インターフェース
#TODO: 機械学習のAI
#TODO: ニアリーチが出てきたら、ランダムチョイスじゃなくて、各場合の探索を行い始めるとか

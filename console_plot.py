#!/usr/bin/env python

import numpy as np
from datetime import timedelta
import os.path
import re
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata
import tornado.websocket
import json
import hashlib, uuid

import zmq
from zmq.eventloop import ioloop, zmqstream
ioloop.install()

from tornado.options import define, options

define("port", default=8080, help="run on the given port", type=int)

def rand_walk(n):
    return np.cumsum(np.random.randn(n))

plot_ids = []

# zmq interface
context = zmq.Context()

#socket_out = context.socket(zmq.PUB)
#socket_out.bind("tcp://0.0.0.0:6123")

# tornado hook
#def echo(msg):
#    for s in msg:
#        print 'Received: ' + s
#stream = zmqstream.ZMQStream(socket_in)
#stream.on_recv(echo)

# tornado content handlers
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", RootHandler),
            (r"/test/(.*)", TestHandler),
            (r"/mec", DataHandler)
        ]
        settings = dict(
            app_name=u"Websockets test",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )
        tornado.web.Application.__init__(self, handlers, debug=True,**settings)

class DataHandler(tornado.websocket.WebSocketHandler):
    def allow_draft76(self):
        return True

    def open(self):
        print "connection received"

        socket_in = context.socket(zmq.SUB)
        socket_in.connect("tcp://0.0.0.0:6124")
        socket_in.setsockopt(zmq.SUBSCRIBE,"")

        stream = zmqstream.ZMQStream(socket_in)
        stream.on_recv(self.on_recv)

    def on_close(self):
        print "connection closing"
        self.do_update = False

    def error_msg(self, error_code):
        if not error_code is None:
            json_string=json.dumps({"type":"error","code":error_code})
            print "sending error to client"
            self.write_message("{0}".format(json_string))
        else:
            print "Eror code not found"

    def on_message(self, message):
        print "received message: {0}".format(message)
        socket_out.send_unicode(message)

    def on_recv(self,msg):
        for s in msg:
            print 'Received: ' + s


class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("root_plot.html")


class TestHandler(tornado.web.RequestHandler):
    def get(self,path):
        self.render(path,field_names=field_names,plot_names=plot_names)


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()


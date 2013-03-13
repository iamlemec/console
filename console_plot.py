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
from collections import OrderedDict

import zmq
from zmq.eventloop import ioloop, zmqstream
ioloop.install()

from tornado.options import define, options

define("port", default=8080, help="run on the given port", type=int)

# websocket connections
clients = []

# zmq interface
context = zmq.Context()

socket_in = context.socket(zmq.SUB)
socket_in.connect("tcp://0.0.0.0:6124")
socket_in.setsockopt(zmq.SUBSCRIBE,"")

# plot data
plot_vals = OrderedDict()

# receiver code
def on_recv(msg):
    for s in msg:
        # store internally
        json_data = json.loads(s)
        name = json_data['name']
        cmd = json_data['cmd']
        if cmd == 'update_plot':
            plot_vals[name] = (json_data['x_values'],json_data['y_values'],json_data['options'])

        # broadcast to clients
        for c in clients:
            c.send_message(s)

# attach to zmq socket
stream = zmqstream.ZMQStream(socket_in)
stream.on_recv(on_recv)

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
        clients.append(self)

        # initiate client
        for (name,(xvals,yvals,opts)) in plot_vals.items():
            self.send_message(json.dumps({'cmd':'update_plot','name':name,'x_values':xvals,'y_values':yvals,'options':opts}))

    def on_close(self):
        print "connection closing"
        clients.remove(self)

    def error_msg(self, error_code):
        if not error_code is None:
            json_string=json.dumps({"type":"error","code":error_code})
            print "sending error to client"
            self.write_message("{0}".format(json_string))
        else:
            print "Eror code not found"

    def on_message(self, message):
        print "received message: {0}".format(message)

    def send_message(self,msg):
        self.write_message(msg)

class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("root_plot.html")

class TestHandler(tornado.web.RequestHandler):
    def get(self,path):
        self.render(path)

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()


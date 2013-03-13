#!/usr/bin/env python

import os.path
import tornado.options
import tornado.web
import tornado.websocket
import json
from collections import OrderedDict
import threading
import logging

# logging facilities
LOG_FORMAT = logging.Formatter(fmt='%(asctime)s {%(name)-4s: %(lineno)d} %(levelname)-8s  %(message)s', datefmt='%m-%d %H:%M:%S')
LOG_LEVEL = logging.DEBUG

def getLogger(name):
    logger = logging.getLogger(name)
    sh = logging.FileHandler('server.log')
    sh.setFormatter(LOG_FORMAT)
    logger.addHandler(sh)
    logger.setLevel(LOG_LEVEL)

    return logger

logger = getLogger(__name__)

# tornado options
SERVER_PORT = 8080

# tornado content handlers
class Application(tornado.web.Application):
    def __init__(self,io_loop=None):
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
        tornado.web.Application.__init__(self, handlers, debug=True, io_loop=io_loop, **settings)

class DataHandler(tornado.websocket.WebSocketHandler):
    def initialize(self):
        self._server = self.application._server

    def allow_draft76(self):
        return True

    def open(self):
        print "connection received"
        self._server = self.application._server
        self._server.clients.add(self)

        # initiate client
        for (name,(xvals,yvals,opts)) in self._server.plot_vals.items():
            self.send_message(json.dumps({'cmd':'update_plot','name':name,'x_values':xvals,'y_values':yvals,'options':opts}))

    def on_close(self):
        print "connection closing"
        self._server.clients.remove(self)

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

class ConsoleServer(threading.Thread):
    def __init__(self):
        from tornado.ioloop import IOLoop
        from zmq.eventloop.ioloop import ZMQPoller

        super(ConsoleServer,self).__init__()

        logger.debug("initializing")

        self.name = "ConsoleServer Thread"
        self.daemon = True

        # data storage
        self.clients = set()
        self.plot_vals = OrderedDict()

        # tornado and zmq place nice?
        self.ioloop = IOLoop(ZMQPoller())

    def run(self):
        try:
            logger.debug("in thread")

            from tornado.httpserver import HTTPServer
            import zmq
            from zmq.eventloop import zmqstream

            # zmq
            self.context = zmq.Context()
            self.socket_in = context.socket(zmq.SUB)
            self.socket_in.connect("tcp://0.0.0.0:6124")
            self.socket_in.setsockopt(zmq.SUBSCRIBE,"")

            # input handler
            self.stream = zmqstream.ZMQStream(self.socket_in,io_loop=self.ioloop)
            self.stream.on_recv(self.on_recv)

            # tornado
            self.application = Application(io_loop=self.ioloop)
            self.application._server = self
            server = HTTPServer(self.application,io_loop=self.ioloop)
            server.listen(SERVER_PORT)

            logger.debug("starting IOLoop")
            self.ioloop.start()
            logger.debug("done thread")

        except Exception as e: # capture exceptions from daemonic thread to log file
            import traceback as tb

            logger.error("Exception in server thread:\n" + str(e) + str(tb.format_exc()))

    # receiver code
    def on_recv(self,msg):
        for s in msg:
            # store internally
            json_data = json.loads(s)
            name = json_data['name']
            cmd = json_data['cmd']
            if cmd == 'update_plot':
                self.plot_vals[name] = (json_data['x_values'],json_data['y_values'],json_data['options'])

            # broadcast to clients
            for c in self.clients:
                c.send_message(s)

# run the thread
thread = ConsoleServer()
thread.start()

# zmq interface
import zmq
context = zmq.Context()
socket_out = context.socket(zmq.PUB)
socket_out.bind("tcp://0.0.0.0:6124")

# plot tool
def update_plot(name,x_vals,y_vals,**kwargs):
    json_out = {'cmd':'update_plot','name':name,'x_values':map(unicode,x_vals),'y_values':map(unicode,y_vals),'options':kwargs}
    socket_out.send(json.dumps(json_out))


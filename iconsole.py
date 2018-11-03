#!/usr/bin/env python3

import os
import json
from collections import OrderedDict
import threading
import logging
import random

import tornado.options
import tornado.web
import tornado.websocket
from tornado.httpserver import HTTPServer

import zmq
from zmq.eventloop.ioloop import ZMQIOLoop
from zmq.eventloop import zmqstream

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

# defaults
HTTP_PORT = 9010
ZMQ_PORT = 6124

# tornado content handlers
class Application(tornado.web.Application):
    def __init__(self, io_loop=None):
        if os.path.islink(__file__):
            server_file = os.readlink(__file__)
        else:
            server_file = __file__
        server_dir = os.path.dirname(server_file)

        handlers = [
            (r"/", RootHandler),
            (r"/mec", DataHandler)
        ]
        settings = dict(
            app_name=u"Websockets test",
            template_path=os.path.join(server_dir, "templates"),
            static_path=os.path.join(server_dir, "static"),
            xsrf_cookies=True,
        )
        tornado.web.Application.__init__(self, handlers, debug=True, io_loop=io_loop, **settings)

class DataHandler(tornado.websocket.WebSocketHandler):
    def initialize(self):
        self._server = self.application._server

    def allow_draft76(self):
        return True

    def open(self):
        self._server = self.application._server
        self._server.clients.add(self)

    def on_close(self):
        self._server.clients.remove(self)

    def error_msg(self, error_code):
        if not error_code is None:
            self.send_message({"type": "error", "code": error_code})

    def send_message(self, d):
        self.write_message(json.dumps(d))

    def on_message(self, msg):
        json_data = json.loads(msg)
        cmd = json_data.get('cmd', '')
        if cmd == 'init':
            for label, info in self._server.plots.items():
                self.send_message({'cmd': 'create_plot', 'label': label})
                if 'title' in info:
                    self.send_message({'cmd': 'set_title', 'label': label, 'title': info['title']})
                if 'spec' in info:
                    self.send_message({'cmd': 'set_vega', 'label': label, 'spec': info['spec']})
                if 'svg' in info:
                    self.send_message({'cmd': 'set_svg', 'label': label, 'svg': info['svg']})


class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("root.html")

class ConsoleServer(threading.Thread):
    def __init__(self, zmq_port, http_port, killable=False):
        super(ConsoleServer,self).__init__()

        self.name = "ConsoleServer Thread"
        self.daemon = True
        self.http_port = http_port
        self.zmq_port = zmq_port
        self.killable = killable

    def run(self):
        try:
            logger.debug("in thread")

            # data storage
            self.clients = set()
            self.plots = OrderedDict()

            # tornado and zmq play nice?
            self.ioloop = ZMQIOLoop()

            # zmq
            self.context = zmq.Context()
            self.socket_in = self.context.socket(zmq.SUB)
            self.socket_in.connect("tcp://0.0.0.0:"+str(self.zmq_port))
            self.socket_in.setsockopt_string(zmq.SUBSCRIBE, "")

            # input handler
            self.stream = zmqstream.ZMQStream(self.socket_in, io_loop=self.ioloop)
            self.stream.on_recv(self.on_recv)

            # tornado
            self.application = Application(io_loop=self.ioloop)
            self.application._server = self
            self.server = HTTPServer(self.application)
            self.server.listen(self.http_port)

            logger.debug("starting IOLoop")
            self.ioloop.start()
            logger.debug("done thread")

        except Exception as e: # capture exceptions from daemonic thread to log file
            import traceback as tb

            logger.error("Exception in server thread:\n" + str(e) + str(tb.format_exc()))

    # receiver code
    def on_recv(self, msg):
        for s in msg:
            # logger.debug("msg: %s" % s)

            json_data = json.loads(s.decode())
            label = json_data.get('label', '')
            cmd = json_data.get('cmd', '')

            if cmd == 'create_plot':
                self.plots[label] = {}
            elif cmd == 'remove_plot':
                self.plots.pop(label)
            elif cmd == 'clear_plots':
                self.plots.clear()
            elif cmd == 'set_title':
                self.plots[label]['title'] = json_data['title']
            elif cmd == 'set_vega':
                self.plots[label]['spec'] = json_data['spec']
            elif cmd == 'set_svg':
                self.plots[label]['svg'] = json_data['svg']

            # broadcast to clients
            for c in self.clients:
                c.write_message(s)

            if self.killable and cmd == 'die':
                self.server.stop()
                self.ioloop.stop()

class Console(object):
    def __init__(self, http_port=None, zmq_port=None, server=False):
        self.http_port = http_port if http_port else HTTP_PORT
        self.zmq_port = zmq_port if zmq_port else ZMQ_PORT
        self.server = server
        self.started = False
        self.start()

    def __del__(self):
        self.stop()

    # server tools
    def start(self):
        if self.started:
            return

        # run the server
        if self.server:
            self.thread = ConsoleServer(zmq_port=self.zmq_port, http_port=self.http_port, killable=True)
            self.thread.start()

        # zmq interface
        self.context = zmq.Context()
        self.socket_out = self.context.socket(zmq.PUB)
        self.socket_out.bind("tcp://0.0.0.0:"+str(self.zmq_port))

        self.started = True

    def stop(self):
        if not self.started:
            return

        # kill server
        if self.server:
            self.send_message({'cmd': 'die'})

        # disconnect socket
        self.socket_out.unbind("tcp://0.0.0.0:"+str(self.zmq_port))
        self.context.destroy()

        self.started = False

    def send_message(self, d):
        self.socket_out.send_string(json.dumps(d))

    # figure management
    def create_plot(self, label=None):
        if label is None:
            label = 'figure_%016x' % random.getrandbits(64)
        self.send_message({'cmd': 'create_plot', 'label': label})
        return Figure(self, label)

    def remove_plot(self, label):
        self.send_message({'cmd': 'remove_plot', 'label': label})

    def clear_plots(self):
        self.send_message({'cmd': 'clear_plots'})

    # plot tools
    def set_title(self, label, title):
        self.send_message({'cmd': 'set_title', 'label': label, 'title': title})

    def set_vega(self, label, spec):
        self.send_message({'cmd': 'set_vega', 'label': label, 'spec': spec})

    def set_svg(self, label, svg):
        self.send_message({'cmd': 'set_svg', 'label': label, 'svg': svg})

# this is just a wrapper that allows chaining
class Figure(object):
    def __init__(self, ic, label, title=None):
        self.ic = ic
        self.label = label
        self.active = True

        if not title is None:
            self.ic.set_title(self.label, title)

    # plot tools
    def title(self, title):
        if self.active:
            self.ic.set_title(self.label, title)
        return self

    def vega(self, spec):
        if self.active:
            self.ic.set_vega(self.label, spec)
        return self

    def altair(self, chart):
        if self.active:
            spec = chart.to_dict()
            self.ic.set_vega(self.label, spec)
        return self

    def svg(self, svg):
        if self.active:
            self.ic.set_svg(self.label, svg)
        return self

    def remove(self):
        if self.active:
            self.ic.remove_plot(self.label)
            self.active = False

# default is start a server
if __name__ == '__main__':
    serv = ConsoleServer(zmq_port=ZMQ_PORT, http_port=HTTP_PORT)
    serv.start()
    serv.join()
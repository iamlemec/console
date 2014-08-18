#!/usr/bin/env python

import os
from time import sleep
import json
from collections import OrderedDict
import threading
import logging
import random
import numpy as np

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

# tornado options
SERVER_PATH = "/media/Liquid/work/console"
SERVER_FILE = "root.html"

# tornado defaults
HTTP_PORT = 8080

# zmq defaults
ZMQ_PORT = 6124

# tornado content handlers
class Application(tornado.web.Application):
    def __init__(self,io_loop=None):
        handlers = [
            (r"/", RootHandler),
            (r"/mec", DataHandler)
        ]
        settings = dict(
            app_name=u"Websockets test",
            template_path=os.path.join(SERVER_PATH, "templates"),
            static_path=os.path.join(SERVER_PATH, "static"),
            xsrf_cookies=True,
        )
        tornado.web.Application.__init__(self, handlers, debug=True, io_loop=io_loop, **settings)

class DataHandler(tornado.websocket.WebSocketHandler):
    def initialize(self):
        self._server = self.application._server

    def allow_draft76(self):
        return True

    def open(self):
        #print "connection received"
        self._server = self.application._server
        self._server.clients.add(self)

        # initiate client
        for (label,info) in self._server.plot_vals.items():
            self.send_message(json.dumps({'cmd':'create_plot','label':label}))
            if 'title' in info:
                self.send_message(json.dumps({'cmd':'set_title','label':label,'title':info['title']}))
            if 'data' in info:
                data = info['data']
                self.send_message(json.dumps({'cmd':'set_data','label':label,'x_values':data[0],'y_values':data[1]}))
            if 'xrange' in info:
                xrange = info['xrange']
                self.send_message(json.dumps({'cmd':'set_xrange','label':label,'xmin':xrange[0],'xmax':xrange[1]}))
            if 'yrange' in info:
                yrange = info['yrange']
                self.send_message(json.dumps({'cmd':'set_yrange','label':label,'ymin':yrange[0],'ymax':yrange[1]}))
            if 'options' in info:
                self.send_message(json.dumps({'cmd':'set_options','label':label,'options':info['options']}))

    def on_close(self):
        #print "connection closing"
        self._server.clients.remove(self)

    def error_msg(self, error_code):
        if not error_code is None:
            json_string=json.dumps({"type":"error","code":error_code})
            print "sending error to client"
            self.write_message("{0}".format(json_string))
        else:
            print "Eror code not found"

    def on_message(self, message):
        #print "received message: {0}".format(message)
        pass

    def send_message(self,msg):
        self.write_message(msg)

class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.render(SERVER_FILE)

class ConsoleServer(threading.Thread):
    def __init__(self,zmq_port,http_port):
        super(ConsoleServer,self).__init__()

        self.name = "ConsoleServer Thread"
        self.daemon = True
        self.http_port = http_port
        self.zmq_port = zmq_port

    def run(self):
        try:
            logger.debug("in thread")

            # data storage
            self.clients = set()
            self.plot_vals = OrderedDict()

            # tornado and zmq play nice?
            self.ioloop = ZMQIOLoop()

            # zmq
            self.context = zmq.Context()
            self.socket_in = self.context.socket(zmq.SUB)
            self.socket_in.connect("tcp://0.0.0.0:"+str(self.zmq_port))
            self.socket_in.setsockopt(zmq.SUBSCRIBE,"")

            # input handler
            self.stream = zmqstream.ZMQStream(self.socket_in,io_loop=self.ioloop)
            self.stream.on_recv(self.on_recv)

            # tornado
            self.application = Application(io_loop=self.ioloop)
            self.application._server = self
            self.server = HTTPServer(self.application,io_loop=self.ioloop)
            self.server.listen(self.http_port)

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
            label = json_data.get('label','')
            cmd = json_data.get('cmd','')
            if cmd == 'create_plot':
                self.plot_vals[label] = {}
            elif cmd == 'remove_plot':
                self.plot_vals.pop(label)
            elif cmd == 'set_title':
                self.plot_vals[label]['title'] = json_data['title']
            elif cmd == 'set_xrange':
                self.plot_vals[label]['xrange'] = (json_data['xmin'],json_data['xmax'])
            elif cmd == 'set_yrange':
                self.plot_vals[label]['yrange'] = (json_data['ymin'],json_data['ymax'])
            elif cmd == 'set_options':
                self.plot_vals[label]['options'] = json_data['options']
            elif cmd == 'set_data':
                self.plot_vals[label]['data'] = (json_data['x_values'],json_data['y_values'])

            # broadcast to clients
            for c in self.clients:
                c.send_message(s)

            if cmd == 'die':
                self.server.stop()
                self.ioloop.stop()

# do dataframe stuff
def dataframe(xv,yv):
    df = np.vstack(map(np.ravel,[xv,yv]))
    return tuple(map(list,df[:,~np.isnan(df).any(axis=0)]))

class IConsole(object):
    def __init__(self,http_port=None,zmq_port=None):
        self.http_port = http_port if http_port else HTTP_PORT
        self.zmq_port = zmq_port if zmq_port else ZMQ_PORT
        self.start()

    def __del__(self):
        self.stop()

    # server tools
    def start(self):
        # run the thread
        self.thread = ConsoleServer(zmq_port=self.zmq_port,http_port=self.http_port)
        self.thread.start()

        # zmq interface
        self.context = zmq.Context()
        self.socket_out = self.context.socket(zmq.PUB)
        self.socket_out.bind("tcp://0.0.0.0:"+str(self.zmq_port))

        # this is a hack - should have a ready signal
        sleep(1.0)

    def stop(self):
        json_out = {'cmd':'die'}
        self.socket_out.send(json.dumps(json_out))
        self.socket_out.unbind("tcp://0.0.0.0:"+str(self.zmq_port))
        self.context.destroy()
        del self.thread
        del self.socket_out
        del self.context

    # plot tools
    def set_title(self,label,title):
        json_out = {'cmd':'set_title','label':label,'title':title}
        self.socket_out.send(json.dumps(json_out))

    def set_xrange(self,label,xmin,xmax):
        json_out = {'cmd':'set_xrange','label':label,'xmin':xmin,'xmax':xmax}
        self.socket_out.send(json.dumps(json_out))

    def set_yrange(self,label,ymin,ymax):
        json_out = {'cmd':'set_yrange','label':label,'ymin':ymin,'ymax':ymax}
        self.socket_out.send(json.dumps(json_out))

    def set_options(self,label,options):
        json_out = {'cmd':'set_options','label':label,'options':options}
        self.socket_out.send(json.dumps(json_out))

    def set_data(self,label,x_vals,y_vals=None):
        if y_vals is None:
            y_vals = x_vals
            x_vals = range(len(x_vals))
        if len(x_vals) != len(y_vals):
            print 'Input vectors must be same length.'
            return

        (x_fix,y_fix) = dataframe(x_vals,y_vals)
        json_out = {'cmd':'set_data','label':label,'x_values':x_fix,'y_values':y_fix}
        self.socket_out.send(json.dumps(json_out))

    def create_plot(self,label=None):
        if label is None:
            label = 'figure_%016x'%(random.getrandbits(64))
        logger.debug('Create plot: ' + label)
        json_out = {'cmd':'create_plot','label':label}
        self.socket_out.send(json.dumps(json_out))
        return IFigure(self,label)

    def remove_plot(self,label):
        json_out = {'cmd':'remove_plot','label':label}
        self.socket_out.send(json.dumps(json_out))

# this is just a wrapper that allows chaining
class IFigure(object):
    def __init__(self,ic,label):
        self.ic = ic
        self.label = label
        self.active = True

    # plot tools
    def title(self,title):
        if self.active:
            self.ic.set_title(self.label,title)
        return self

    def xrange(self,xmin,xmax):
        if self.active:
            self.ic.set_xrange(self.label,xmin,xmax)
        return self

    def yrange(self,ymin,ymax):
        if self.active:
            self.ic.set_yrange(self.label,ymin,ymax)
        return self

    def options(self,options):
        if self.active:
            self.ic.set_options(self.label,options)
        return self

    def data(self,x_vals,y_vals=None):
        if self.active:
            self.ic.set_data(self.label,x_vals,y_vals)
        return self

    def remove(self):
        if self.active:
            self.ic.remove_plot(self.label)
            self.active = False

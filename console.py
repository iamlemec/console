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

from tornado.options import define, options

define("port", default=8080, help="run on the given port", type=int)

def rand_walk(n):
    return np.cumsum(np.random.randn(n))

n_base = 1024
theta = np.linspace(0.0,2.0*np.pi,n_base)
upd_speed = 0.01

field_types = {'position':float,'velocity':float}
field_vals = dict([(f,t()) for (f,t) in field_types.items()])
field_names = field_types.keys()

plot_types = {'data1':n_base,'data2':n_base}
plot_names = plot_types.keys()
plot_xvals = dict([(pname,np.linspace(0.0,2.0*np.pi,n)) for (pname,n) in plot_types.items()])
plot_yvals = dict([(pname,np.zeros(n)) for (pname,n) in plot_types.items()])

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://0.0.0.0:6123")

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
    global theta

    def allow_draft76(self):
        return True

    def open(self):
        print "connection received"
        ioloop = tornado.ioloop.IOLoop.instance()
        ioloop.add_timeout(timedelta(seconds=0.1),self.update_plots)

    def on_close(self):
        print "connection closing"

    def error_msg(self, error_code):
        if not error_code is None:
            json_string=json.dumps({"type":"error","code":error_code})
            print "sending error to client"
            self.write_message("{0}".format(json_string))
        else:
            print "Eror code not found"

    def on_message(self, message):
        print "received message: {0}".format(message)
        socket.send_unicode(message)

        json_data = json.loads(message)
        cmd = json_data.get('cmd','')
        name = json_data.get('name','')

        if cmd == 'store_field':
            value = json_data.get('value','')
            if name in vals:
                print 'Storing %s in %s' % (value,field)
                try:
                    value = types[name](value) 
                    field_vals[name] = value
                    json_out = {'cmd':'update_field','name':name,'value':str(value)}
                    self.write_message(json.dumps(json_out))
                except Exception, e:
                    print 'Invalid value \'%s\' for field %s' % (value,name)
            else:
                print 'Invalid field %s' % (name,)
        elif cmd == 'fetch_field':
            if name in field_names:
                value = field_vals[name]
                json_out = {'cmd':'update_field','name':name,'value':str(value)}
                self.write_message(json.dumps(json_out))
            else:
                print 'Invalid field %s' % (name,)
        elif cmd == 'fetch_plot':
            if name in plot_names:
                self.send_plot(name)
            else:
                print 'Invalid plot %s' % (name,)

    def update_plots(self):
        global theta

        theta = theta + 0.1
        theta[theta>2.0*np.pi] -= 2.0*np.pi

        plot_yvals['data1'] = np.sin(theta)
        plot_yvals['data2'] = np.cos(2.0*theta)
        self.send_plot('data1')
        self.send_plot('data2')

        ioloop = tornado.ioloop.IOLoop.instance()
        ioloop.add_timeout(timedelta(seconds=upd_speed),self.update_plots)

    def send_plot(self,pname):
        x_values = plot_xvals[pname]
        y_values = plot_yvals[pname]
        json_out = {'cmd':'update_plot','name':pname,'x_values':map(unicode,x_values),'y_values':map(unicode,y_values)}
        self.write_message(json.dumps(json_out))


class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("root.html",field_names=field_names,plot_names=plot_names)

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


import zmq
import json
import numpy as np
from time import sleep

# constants
def rand_walk(n):
    return np.cumsum(np.random.randn(n))

pname = 'random_walk'
velocity = 0.1
n_base = 1024
theta = np.linspace(0.0,2.0*np.pi,n_base)
randw = rand_walk(n_base)
upd_speed = 1.0

# zmq setup
context = zmq.Context()

socket_in = context.socket(zmq.SUB)
socket_in.connect("tcp://0.0.0.0:6123")
socket_in.setsockopt(zmq.SUBSCRIBE, "")

socket_out = context.socket(zmq.PUB)
socket_out.bind("tcp://0.0.0.0:6124")

# plot tool
def update_plot(name,x_vals,y_vals):
    json_out = {'cmd':'update_plot','name':name,'x_values':map(unicode,x_vals),'y_values':map(unicode,y_vals)}
    socket_out.send(json.dumps(json_out))

# create plot
#update_plot(pname,theta,randw)

# main loop
while True:
    sleep(upd_speed)

    theta += velocity
    theta[theta>2.0*np.pi] -= 2.0*np.pi

    randw[:-10] = randw[10:]
    randw[-10:] = rand_walk(10) + randw[-10]

    #update_plot(pname,theta,randw)

    socket_out.send('testing')


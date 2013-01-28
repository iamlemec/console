import zmq
import json
import numpy as np
from time import sleep
import scipy.signal as sig

# constants
ar_var = 0.05
pval = 0.9
pname = 'random_walk1'
n_base = 256
randx = np.linspace(0.0,n_base,n_base)
randw = ar_var*np.random.randn(n_base)
randy = np.zeros(n_base)
randy[0] = randw[0]
for i in range(1,n_base):
  randy[i] = pval*randy[i-1] + randw[i]
upd_speed = 0.1

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

# main loop
while True:
    sleep(upd_speed)

    randw = ar_var*np.random.randn(10)
    randy[:-10] = randy[10:]
    for i in range(10,0,-1):
      randy[n_base-i] = pval*randy[n_base-i-1] + randw[i-1]

    #print randw
    update_plot(pname,randx,np.exp(randy))

    #json_out = {'cmd':'testing'}
    #socket_out.send(json.dumps(json_out))


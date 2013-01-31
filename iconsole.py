import zmq
import json

# zmq setup
context = zmq.Context()
socket_out = context.socket(zmq.PUB)
socket_out.bind("tcp://0.0.0.0:6124")

# plot tool
def update_plot(name,x_vals,y_vals):
    json_out = {'cmd':'update_plot','name':name,'x_values':map(unicode,x_vals),'y_values':map(unicode,y_vals)}
    socket_out.send(json.dumps(json_out))


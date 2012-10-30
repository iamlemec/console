import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://0.0.0.0:6123")
socket.setsockopt(zmq.SUBSCRIBE, "")

while True:
    print socket.recv()


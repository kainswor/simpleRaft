import zmq
import threading
import pickle
import Queue
import time

class Server(threading.Thread):

    def __init__(self, name, state, log, messageBoard, neighbors):
        super(Server, self).__init__()
        self.daemon = True
        self._run = True

        self._name = name
        self._state = state
        self._log = log
        self._messageBoard = messageBoard
        self._messagelock = threading.Lock()
        self._neighbors = neighbors
        self._total_nodes = 0

        self._commitIndex = 0
        self._currentTerm = 0

        self._lastApplied = 0

        self._lastLogIndex = 0
        self._lastLogTerm = None

        self._state.set_server(self)
        if self._messageBoard:
            self._messageBoard.set_owner(self)

    def send_message(self, message):
        for n in self._neighbors:
            message._receiver = n._name
            n.post_message(message)

    def send_message_response(self, message):
        n = [n for n in self._neighbors if n._name == message.receiver]
        if(len(n) > 0):
            n[0].post_message(message)

    def post_message(self, message):
        self._messageBoard.post_message(message)

    def on_message(self, message):
        with self._messagelock:
            try:
                state, response = self._state.on_message(message)

                #print self._state.__dict__, state.__dict__, message.__dict__
                self._state = state
            except Exception as exc:
                print repr(exc)
                print self._state, message, message.__dict__

    def run(self):
        while self._run:
            ts = time.time()
            time.sleep(self._state.timeout)
            if self._state._last_heartbeat < ts:
                with self._messagelock:
                    state, response = self._state.on_leader_timeout()
                    print state, response
                    self._state = state

    def stop(self):
        self._run = False

class ZeroMQPeer(Server):
    '''
    Simple mock up for creating cluster definitions of remote nodes
    (We don't want to actually set up a server)
    '''
    def __init__(self, name, host='127.0.0.1', port=6666):
        self._name = name
        self._host = host
        self._port = port

class ZeroMQServer(Server):

    def __init__(self, name, state, log, neighbors, host='127.0.0.1', port=6666):
        # Modified super args to prevent starting the beast!
        super(ZeroMQServer, self).__init__(name, state, log, None, neighbors)
        self._host = host
        self._port = port
        self._context = zmq.Context()
        self._context.setsockopt(zmq.LINGER, 0)
        self._pub_queue = Queue.Queue()

        class SubscribeThread(threading.Thread):
            def run(thread):
                socket = self._context.socket(zmq.SUB)
                socket.connect("tcp://%s:%d" % (self._host, self._port))
                for n in neighbors:
                    socket.connect("tcp://%s:%d" % (n._host, n._port))
                socket.setsockopt(zmq.SUBSCRIBE, '')

                while self._run:
                    try:
                        message = socket.recv(zmq.NOBLOCK)
                        message = pickle.loads(message)
                        #print '%s RECEIVED: %s' % (self._name, repr(message.__dict__))
                        # assert issubclass(message, BaseMessage)
                        if message.receiver == self._name or message.receiver == '*':
                            self.on_message(message)
                    except zmq.ZMQError:
                        import time
                        time.sleep(0.1)

        class PublishThread(threading.Thread):
            def run(thread):
                socket = self._context.socket(zmq.PUB)
                socket.bind("tcp://*:%d" % self._port)

                while self._run:
                    message = self._pub_queue.get()
                    #print '%s PUBLISHING: %s' % (self._name, repr(message.__dict__))
                    socket.send(pickle.dumps(message))
        

        self.subscribeThread = SubscribeThread()
        self.publishThread = PublishThread()

        self.subscribeThread.daemon = True
        self.subscribeThread.start()
        self.publishThread.daemon = True
        self.publishThread.start()

    def send_message(self, message):
        '''
        Enqueues message for broadcast, overwriting receiver field to '*'
        '''
        message._receiver = '*'
        self._pub_queue.put(message)


    def send_message_response(self, message):
        '''
        Enqueues for a broadcast, without overwriting receiver field
        '''
        self._pub_queue.put(message)

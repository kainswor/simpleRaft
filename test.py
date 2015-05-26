#!/usr/bin/python
from simpleRaft.servers.server import ZeroMQPeer, ZeroMQServer
from simpleRaft.states.follower import Follower
from simpleRaft.states.leader import Leader

import time

# Peer mocks for server init'ing
peer1 = ZeroMQPeer(1, host='127.0.0.1', port=6666)
peer2 = ZeroMQPeer(2, host='127.0.0.1', port=6667)
peer3 = ZeroMQPeer(3, host='127.0.0.1', port=6668)

# ZeroMQServers for 3 candidates
server1 = ZeroMQServer(1, Follower(), [], [peer2, peer3], host=peer1._host, port=peer1._port)
server2 = ZeroMQServer(2, Follower(), [], [peer1, peer3], host=peer2._host, port=peer2._port)
server3 = ZeroMQServer(3, Follower(), [], [peer1, peer2], host=peer3._host, port=peer3._port)

print 'Starting servers...'
server1.start()
server2.start()
server3.start()

# Follow and watch a candidate become leader?
if __name__ == '__main__':
    while True:
        time.sleep(5)
        if server1:
            print 1, server1.publishThread.is_alive(), server1.subscribeThread.is_alive(), server1._state
        print 2, server2.publishThread.is_alive(), server2.subscribeThread.is_alive(), server2._state
        print 3, server3.publishThread.is_alive(), server3.subscribeThread.is_alive(), server3._state

        if server1 and issubclass(type(server1._state), Leader):
            print 'Halting 1'
            server1.stop()
            server1 = None
# ... Profit?

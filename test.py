#!/usr/bin/python
from simpleRaft.servers.server import ZeroMQPeer, ZeroMQClient, ZeroMQServer
from simpleRaft.states.follower import Follower
from simpleRaft.states.leader import Leader

import time

# Peer mocks for server init'ing
peer1 = ZeroMQPeer(1, host='127.0.0.1', port=6666, client_port=5000)
peer2 = ZeroMQPeer(2, host='127.0.0.1', port=6667, client_port=5001)
peer3 = ZeroMQPeer(3, host='127.0.0.1', port=6668, client_port=5002)

client = ZeroMQClient([peer1, peer2, peer3])

# ZeroMQServers for 3 candidates
server1 = ZeroMQServer(1, Follower(), [], [peer2, peer3], host=peer1._host, port=peer1._port, client_port=peer1._client_port)
server2 = ZeroMQServer(2, Follower(), [], [peer1, peer3], host=peer2._host, port=peer2._port, client_port=peer2._client_port)
server3 = ZeroMQServer(3, Follower(), [], [peer1, peer2], host=peer3._host, port=peer3._port, client_port=peer3._client_port)

print 'Starting servers...'
server1.start()
server2.start()
server3.start()

# Follow and watch a candidate become leader?
if __name__ == '__main__':
    while True:
        time.sleep(5)
        print client.leader

        if server1:
            print 1, server1.publishThread.is_alive(), server1.subscribeThread.is_alive(), server1._state
        print 2, server2.publishThread.is_alive(), server2.subscribeThread.is_alive(), server2._state
        print 3, server3.publishThread.is_alive(), server3.subscribeThread.is_alive(), server3._state
        print server3.is_leader, server3.leader

        if server1 and issubclass(type(server1._state), Leader):
            print 'Halting 1'
            server1.stop()
            server1 = None
# ... Profit?

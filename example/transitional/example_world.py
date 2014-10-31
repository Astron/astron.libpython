#!/usr/bin/env python

from time import sleep

from astron.object_repository import InternalRepository

if __name__ == '__main__':
    repo = InternalRepository('SimpleExample v0.2', 'simple_example.dc', stateserver=402000, ai_channel=500001)

    def connected():
        print('Connection established.')
        repo.send_CONTROL_ADD_CHANNEL(1000)
        repo.send_CONTROL_ADD_CHANNEL(10000)
        repo.send_CONTROL_ADD_CHANNEL(1000 * 2**32 | 0)
        repo.send_CONTROL_ADD_CHANNEL(10000 * 2**32 | 0)
        repo.send_STATESERVER_OBJECT_SET_AI(10000)
        repo.create_distobj('GameRootAI', 1000, 0, 0)
        repo.create_distobj('DistributedMaproot', 10000, 1000, 0)
        # maproot.enter()

    def failed():
        print('Connection attempt failed.')

    repo.connect(connected, failed, host = '127.0.0.1', port = 7199)

    while True:
        print("Polling...")
        repo.poll_till_empty()
        sleep(2)

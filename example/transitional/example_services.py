#!/usr/bin/env python

from time import sleep

from astron.object_repository import InternalRepository

if __name__ == '__main__':
    repo = InternalRepository('SimpleExample v0.2', 'simple_example.dc', stateserver=402000, ai_channel=500000)

    def connected():
        print('Connection established.')
        # FIXME: Does this object also need to be announced to astrond?
        login_manager = repo.create_view_by_classname('LoginManagerUD', 1234, 0, 0)
        repo.send_STATESERVER_OBJECT_SET_AI(1234)

    def failed():
        print('Connection attempt failed.')

    repo.connect(connected, failed, host = '127.0.0.1', port = 7199)

    while True:
        repo.poll_till_empty()
        #print(repo.poll_datagram())
        sleep(0.1)

#!/usr/bin/env python

from time import sleep

from astron.object_repository import InternalRepository

if __name__ == '__main__':
    repo = InternalRepository('SimpleExample v0.2', 'simple_example.dc')

    def connected():
        print('Connection established.')
        # FIXME: Create maproot object and view only instead
        login_manager = repo.create_view_by_classname('LoginManagerAI', 1234, 0, 0)

    def ejected(error_code, reason):
        print('Got ejected (%i): %s' % (error_code, reason))

    def failed():
        print('Connection attempt failed.')

    repo.connect(connected, failed, ejected, host = '127.0.0.1', port = 7199)

    while True:
        repo.poll_till_empty()
        #print(repo.poll_datagram())
        sleep(0.1)

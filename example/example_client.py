#!/usr/bin/env python

from time import sleep

from astron.object_repository import ClientRepository
from shared_constants import LOGIN_MANAGER_DO_ID

if __name__ == '__main__':
    repo = ClientRepository('SimpleExample v0.2', 'example.dc')

    def connected():
        print('Connection established.')
        login_manager = repo.create_distobjglobal_view('LoginManager', LOGIN_MANAGER_DO_ID)
        login_manager.login("guest", "guest")

    def ejected(error_code, reason):
        print('Got ejected (%i): %s' % (error_code, reason))

    def failed():
        print('Connection attempt failed.')

    repo.connect(connected, failed, ejected, host = '127.0.0.1', port = 6667)

    while True:
        repo.poll_till_empty()
        #print(repo.poll_datagram())
        sleep(0.1)

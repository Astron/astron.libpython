#!/usr/bin/env python

from time import sleep

from astron.object_repository import InternalRepository
from shared_constants import LOGIN_MANAGER_DO_ID, MAP_ROOT_PARENT, MAP_ROOT_ZONE, SERVICES, COMMON_STATESERVER, COMMON_DBSS

if __name__ == '__main__':
    repo = InternalRepository('SimpleExample v0.2', 'example.dc',
                              stateserver = COMMON_STATESERVER,
                              dbss = COMMON_DBSS,
                              ai_channel = SERVICES)

    def connected():
        print('Connection established.')
        login_manager = repo.create_distobjglobal_view('LoginManagerUD', LOGIN_MANAGER_DO_ID)
        # FIXME: This should be folded into a 'set_ai = True' kwarg into create_distobjglobal_view
        repo.send_CONTROL_ADD_CHANNEL(LOGIN_MANAGER_DO_ID)
        repo.add_ai_interest(MAP_ROOT_PARENT, MAP_ROOT_ZONE)

    def failed():
        print('Connection attempt failed.')

    repo.connect(connected, failed, host = '127.0.0.1', port = 7199)

    while True:
        repo.poll_till_empty()
        sleep(0.1)

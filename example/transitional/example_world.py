#!/usr/bin/env python

from time import sleep

from astron.object_repository import InternalRepository
from shared_constants import MAP_ROOT_DO_ID, MAP_ROOT_PARENT, MAP_ROOT_ZONE

if __name__ == '__main__':
    repo = InternalRepository('SimpleExample v0.2', 'simple_example.dc', stateserver=402000, ai_channel=500001)

    def connected():
        print('Connection established.')
        repo.create_distobj('DistributedMaproot', MAP_ROOT_DO_ID, MAP_ROOT_PARENT, MAP_ROOT_ZONE, set_ai = True)

    def failed():
        print('Connection attempt failed.')

    repo.connect(connected, failed, host = '127.0.0.1', port = 7199)

    while True:
        # print("Polling...")
        repo.poll_till_empty()
        sleep(0.1)

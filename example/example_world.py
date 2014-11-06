#!/usr/bin/env python

from time import sleep

from astron.object_repository import InterestInternalRepository as InternalRepository
from shared_constants import MAP_ROOT_DO_ID, MAP_ROOT_PARENT, MAP_ROOT_ZONE, WORLD, COMMON_STATESERVER, COMMON_DBSS

if __name__ == '__main__':
    # FIXME: As soon as there are several AI servers, they have to
    # "instinctively" choose different control channels. There will
    # have to be a) a channel broker service, or b) have to use a
    # to-be-designed CONTROL message to get assigned a channel.
    repo = InternalRepository('SimpleExample v0.2', 'example.dc',
                              stateserver = COMMON_STATESERVER,
                              dbss = COMMON_DBSS,
                              ai_channel = WORLD)

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

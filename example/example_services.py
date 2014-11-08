#!/usr/bin/env python

# TODO
# * Catch SIGSTOP
# * Turn --login and --ai into something more generic
# * Proper logging
# * Monitoring output

import argparse
from time import sleep
import datetime

from astron.object_repository import InterestInternalRepository as InternalRepository
from shared_constants import LOGIN_MANAGER_DO_ID, \
    MAP_ROOT_DO_ID, MAP_ROOT_PARENT, MAP_ROOT_ZONE, \
    SERVICES_CHANNEL, STATESERVER, DBSS, \
    DC_FILE, \
    SERVER_FRAMERATE

class AstronServer:
    def __init__(self,
                 dc_file = DC_FILE,
                 stateserver = STATESERVER,
                 dbss = DBSS,
                 ai_channel = SERVICES_CHANNEL,
                 host = '127.0.0.1',
                 port = 7199,
                 frame_time = 1./100.,
                 login = False,
                 ai = False):
        self.host = host
        self.port = port
        self.frame_time = frame_time
        self.login = login
        self.ai = ai
        self.repo = InternalRepository(dc_file,
                                       stateserver = stateserver,
                                       dbss = dbss,
                                       ai_channel = ai_channel)

    def start(self):
        self.repo.connect(self.connected, self.failed, host = self.host, port = self.port)
        while True:
            self.repo.poll_till_empty()
            # FIXME: Measure the time left in the frame, and sleep accordingly here.
            # FIXM: Log ratio of time left, prevalence of overlong frames, total accumulated lag
            sleep(0.1)

    def connected(self):
        print('Connection established.')
        # Login server, assigner of AIs
        if self.login:
            print("Starting Login service")
            self.repo.create_distobjglobal_view('LoginManagerUD', LOGIN_MANAGER_DO_ID, set_ai = True)
            self.repo.add_ai_interest(MAP_ROOT_PARENT, MAP_ROOT_ZONE)
        # AI server
        if self.ai:
            print("Starting AI service")
            self.repo.create_distobj('DistributedMaproot', MAP_ROOT_DO_ID, MAP_ROOT_PARENT, MAP_ROOT_ZONE, set_ai = True)

    def failed(self):
        print('Connection attempt failed.')

if __name__ == '__main__':
    # FIXME: Add an epilog, at least an example usage
    parser = argparse.ArgumentParser(description='A generic server process for Astron networks.',
                                     epilog="")
    parser.add_argument('-D', '--dcfile', type = str, default = DC_FILE,
                        help='Distributed Classes definitions file')
    parser.add_argument('-H', '--host', type = str, default = '127.0.0.1',
                        help='astrond host')
    parser.add_argument('-P', '--port', type = int, default = 7199,
                        help='astrond port for message directors')
    parser.add_argument('-c', '--channel', type = int, default = SERVICES_CHANNEL,
                        help='Repository control channel')
    parser.add_argument('-s', '--stateserver', type = int, default = STATESERVER,
                        help='Number of cycles per second to aim for')
    parser.add_argument('-d', '--dbss', type = int, default = DBSS,
                        help='Number of cycles per second to aim for')
    parser.add_argument('-r', '--framerate', type = float, default = SERVER_FRAMERATE,
                        help='Number of cycles per second to aim for')

    # FIXME: These are specific to this application. Considering how
    # generic they are, they *should* be convertible into more
    # generic arguments. Maybe these are the positional args?
    parser.add_argument('-l', '--login', action = "store_true",
                        help='Login service')
    parser.add_argument('-a', '--ai', action = "store_true",
                        help='AI service')
    args = parser.parse_args()
    
    server = AstronServer(dc_file = args.dcfile,
                          stateserver = STATESERVER,
                          dbss = DBSS,
                          ai_channel = args.channel,
                          host = args.host,
                          port = args.port,
                          frame_time = 1. / args.framerate,
                          login = args.login,
                          ai = args.ai)
    server.start()

#!/usr/bin/env python

# TODO
# * Catch SIGSTOP
# * Turn --login and --ai into something more generic
# * Proper logging
# * Monitoring output
# * Framerate loop

import argparse
from time import sleep
import datetime

from astron.object_repository import InterestInternalRepository as InternalRepository
from shared_constants import SERVICES_CHANNEL, STATESERVER, DBSS, \
    POINT_OF_CONTACT_DO_ID, GAME_ROOT_DO_ID, WORLD_ZONE, LOGIN_SERVICE_ZONE, AI_SERVICES_ZONE, \
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
                 frame_time = 1./100.):
        self.host = host
        self.port = port
        self.frame_time = frame_time
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
        print('Connection established, connected() not overridden.')

    def failed(self):
        print('Connection attempt failed, failed() not overridden.')

class ExampleServer(AstronServer):
    def __init__(self,
                 contact = False, root = False, world = False, login = False, ai = False,
                 *args, **kwargs):
        AstronServer.__init__(self, *args, **kwargs)
        self.contact = contact
        self.root = root
        self.world = world
        self.login = login
        self.ai = ai

    def connected(self):
        print('Connection established.')
        # Point of contact for newly connected clients (state New)
        if self.contact:
            print("Creating Point of Contact")
            self.repo.create_distobjglobal_view('PointOfContactUD', POINT_OF_CONTACT_DO_ID, set_ai = True)
            self.repo.add_ai_interest(GAME_ROOT_DO_ID, LOGIN_SERVICE_ZONE)
        if self.root:
            print("Creating GameRoot")
            self.repo.create_distobj('GameRoot', GAME_ROOT_DO_ID, 0, 0, set_ai = True)
        if self.world:
            print("Creating World")
            self.repo.create_distobj_db('World', GAME_ROOT_DO_ID, WORLD_ZONE, set_ai = True)
        if self.login:
            print("Starting Login service")
            self.repo.create_distobj_db('LoginService', GAME_ROOT_DO_ID, LOGIN_SERVICE_ZONE, set_ai = True)
        if self.ai:
            print("Starting AI service")
            self.repo.create_distobj_db('AIServer', GAME_ROOT_DO_ID, AI_SERVICES_ZONE, set_ai = True)

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
    parser.add_argument('-f', '--framerate', type = float, default = SERVER_FRAMERATE,
                        help='Number of cycles per second to aim for')

    # FIXME: These are specific to this application. Considering how
    # generic they are, they *should* be convertible into more
    # generic arguments. Maybe these are the positional args?
    parser.add_argument('-p', '--point-of-contact', action = "store_true",
                        help='PointOfContact DOG')
    parser.add_argument('-r', '--root', action = "store_true",
                        help='GameRoot object')
    parser.add_argument('-w', '--world', action = "store_true",
                        help='World object')
    parser.add_argument('-l', '--login', action = "store_true",
                        help='Login service')
    parser.add_argument('-a', '--ai', action = "store_true",
                        help='AI service')
    args = parser.parse_args()
    
    server = ExampleServer(dc_file = args.dcfile,
                           stateserver = STATESERVER,
                           dbss = DBSS,
                           ai_channel = args.channel,
                           host = args.host,
                           port = args.port,
                           frame_time = 1. / args.framerate,
                           contact = args.point_of_contact,
                           root = args.root,
                           world = args.world,
                           login = args.login,
                           ai = args.ai)
    server.start()

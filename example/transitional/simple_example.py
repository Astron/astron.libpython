from datetime import datetime

from astron.object_repository import DistributedObject
from shared_constants import LOGIN_MANAGER_DO_ID, MAP_ROOT_ZONE
import random

from pprint import pprint

# Game settings
avatar_speed = 3.0
avatar_rotation_speed = 90.0


# -------------------------------------------------------------------
# LoginManager
# * Registers a DistributedMaproot
# * Authenticates Clients
# * Makes DistributedMaproot create an avatar for new Clients.
# -------------------------------------------------------------------

class LoginManager(DistributedObject):
    def init(self):
        print("LoginManager view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

    def login(self, username, password):
        print("Client logging in")
        self.send_update("login", username, password)

class LoginManagerAI(DistributedObject):
    def init(self):
        print("LoginManagerAI view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

    #def set_maproot(self, maproot_doId):
    #    print("LoginManagerAI view sends set_maproot")
    #    self.send_update("set_maproot", maproot_doId)

class LoginManagerUD(DistributedObject):
    def init(self):
        self.maproot_distobjs = set()
        print("LoginManagerUD view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

    def login(self, sender, username, password):
        print("Received login request for %d" % (sender, ))
        if len(self.maproot_distobjs) > 0:
            if username == "guest" and password == "guest":
                # FIXME: Set client into ESTABLISHED state! 
                print("  Logging in successfully")
                maproot_for_client = random.choice(list(self.maproot_distobjs))
                self.repo.distobj_by_do_id(maproot_for_client).create_avatar(sender, sender)
            else: # Bad credentials
                # FIXME: Implement
                print("  Disconnecting for bad credentials")
        else:
            # maproot hasn't contacted us yet.
            # FIXME: ...or has left, and no replacement has arrived.
            # FIXME: Implement a disconnection with reason "game not up yet".
            print("Dropping connection attempt due to missing maproot")

    def handle_STATESERVER_OBJECT_CHANGING_LOCATION(self, sender, do_id, new_parent, new_zone, old_parent, old_zone):
        if (new_parent == LOGIN_MANAGER_DO_ID) and (new_zone == MAP_ROOT_ZONE):
            # A new maproot "service" has entered
            self.maproot_distobjs.add(do_id)
            print("LoginManagerUD added %d to maproot services." % (do_id, ))
        elif (old_parent == LOGIN_MANAGER_DO_ID) and (old_zone == MAP_ROOT_ZONE):
            # A maproot has just left
            self.maproot_distobjs.remove(do_id)
            print("LoginManagerUD removed %d from maproot services." % (do_id, ))

# -------------------------------------------------------------------
# DistributedMaproot
# * has all avatars in its zone 0
# * generates new avatars
# -------------------------------------------------------------------

class DistributedMaproot(DistributedObject):
    pass

class DistributedMaprootAI(DistributedObject):
    def init(self):
        print("DistributedMaprootAI view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))
        # FIXME: ENTER astrond DO
        # Register with LoginManager
        # self.login_manager = self.repo.create_distobjglobal_view('LoginManagerAI', LOGIN_MANAGER_DO_ID)
        # self.login_manager.set_maproot(self.do_id)

    def create_avatar(self, sender, client_id):
        print("%d called DistributedMaprootAI.create_avatar(%d)" % (sender, client_id))

class DistributedMaprootAE(DistributedObject):
    def init(self):
        print("DistributedMaprootAE view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))
    
    def create_avatar(self, sender, client_id):
        print("DistributedMaprootAE.create_avatar(sender %d, client_id %d)" % (sender, client_id))
        self.send_update('create_avatar', client_id)

class DistributedMaprootUD(DistributedObject):
    def init(self):
        print("DistributedMaprootUD view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

# -------------------------------------------------------------------
# DistributedAvatar
# * represents players in the scene graph
# * routes indications of movement intents to AI
# * updates the actual position and orientation
# -------------------------------------------------------------------

class DistributedAvatar(DistributedObject):
    pass

class DistributedAvatarAI(DistributedObject):
    pass

class DistributedAvatarOV(DistributedObject):
    pass

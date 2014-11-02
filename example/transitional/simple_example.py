from datetime import datetime

from astron.object_repository import DistributedObject
from shared_constants import *

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
        print("LoginManager view created")

    def login(self, username, password):
        print("Client logging in")
        self.send_update("login", username, password)

class LoginManagerAI(DistributedObject):
    def init(self):
        print("LoginManagerAI view created")

    def set_maproot(self, maproot_doId):
        print("LoginManagerAI view sends set_maproot")
        self.send_update("set_maproot", maproot_doId)

class LoginManagerUD(DistributedObject):
    def init(self):
        self.maproot_do_id = None
        print("LoginManagerUD view created")

    def set_maproot(self, maproot_doId):
        self.maproot_do_id = maproot_doId
        print("Maproot DO ID = %d" % (maproot_doId, ))

    def login(self, username, password):
        print("Received login request")
        if self.maproot_do_id != None:
            if username == "guest" and password == "guest":
                print("Logging in successfully")
            else: # Bad credentials
                # FIXME: Implement
                print("Disconnecting for bad credentials")
        else:
            # maproot hasn't contacted us yet.
            # FIXME: ...or has left, and no replacement has arrived.
            # FIXME: Implement a disconnection with reason "game not up yet".
            print("Dropping connection attempt due to missing maproot")

# -------------------------------------------------------------------
# DistributedMaproot
# * has all avatars in its zone 0
# * generates new avatars
# -------------------------------------------------------------------

class DistributedMaproot(DistributedObject):
    pass

class DistributedMaprootAI(DistributedObject):
    def init(self):
        print("DistributedMaprootAI view created")
        # FIXME: ENTER astrond DO
        # Register with LoginManager
        self.login_manager = self.repo.create_distobjglobal_view('LoginManagerAI', LOGIN_MANAGER_DO_ID)
        # self.login_manager.set_maproot(self.do_id)

class DistributedMaprootUD(DistributedObject):
    pass

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

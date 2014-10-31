from astron.object_repository import DistributedObject

from datetime import datetime

# Constant DO and channel IDs
LoginManagerId = 1234

# Game settings
avatar_speed = 3.0
avatar_rotation_speed = 90.0


class GameRoot(DistributedObject):
    pass

class GameRootAI(DistributedObject):
    pass

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
        print("LoginManagerUD view created")

    def set_maproot(self, maproot_doId):
        self.maproot_do_id = maproot_doId
        print("Maproot DO ID = %d" % (maproot_doId, ))

    def login(self, username, password):
        print("Received login request")

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
        self.login_manager = self.repo.create_distobj('LoginManagerAI', 1234, 0, 0)
        self.login_manager.set_maproot(self.do_id)

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

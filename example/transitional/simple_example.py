from astron.object_repository import DistributedObject

from datetime import datetime

# Constant DO and channel IDs
LoginManagerId = 1234

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

    #def set_maproot(self, maproot_doId):
    #    print("LoginManagerAI view sends set_maproot")
    #    self.sendUpdate("set_maproot", [maproot_doId])

class LoginManagerUD(DistributedObject):
    def init(self):
        print("LoginManagerUD view created")

    def login(self, username, password):
        print("Received login request")




class DistributedMaproot(DistributedObject):
    pass

class DistributedMaprootAI(DistributedObject):
    pass

class DistributedMaprootUD(DistributedObject):
    pass




class DistributedAvatar(DistributedObject):
    pass

class DistributedAvatarAI(DistributedObject):
    pass

class DistributedAvatarOV(DistributedObject):
    pass

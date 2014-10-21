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
    def login(self, username, password):
        print("Logging in")
        self.send_update("login", username, password)

class LoginManagerAI(DistributedObject):
    def set_maproot(self, maproot_doId):
        print(datetime.now().strftime("%H:%M:%S")+" LoginManagerAI.set_maproot("+str(maproot_doId)+") in "+str(self.doId))
        self.sendUpdate("set_maproot", [maproot_doId])

class LoginManagerUD(DistributedObject):
    def generate(self):
        print(datetime.now().strftime("%H:%M:%S")+" LoginManagerUD.generate() for "+str(self.doId))

    def set_maproot(self, maproot_doId):
        """Tells the LoginManagerUD what maproot to notify on login."""
        print(datetime.now().strftime("%H:%M:%S")+" LoginManagerUD.set_maproot("+str(maproot_doId)+") in "+str(self.doId))
        self.maproot = DistributedMaprootUD(self.air)
        self.maproot.generateWithRequiredAndId(maproot_doId, 0, 1)

    def login(self, username, password):
        clientId = self.air.get_msg_sender()
        print(datetime.now().strftime("%H:%M:%S")+" LoginManagerUD.login("+username+", <password>)  in "+str(self.doId)+" for client "+str(clientId))
        if (username == "guest") and (password == "guest"):
            # Authenticate a client
            # FIXME: "2" is the magic number for CLIENT_STATE_ESTABLISHED,
            # for which currently no mapping exists.
            self.air.setClientState(clientId, 2)

            # The client is now authenticated; create an Avatar
            #self.maproot.sendUpdate("createAvatar", # Field to call
            #                        [clientId])     # Arguments
            self.maproot.create_avatar(clientId)
            
            # log login
            self.notify.info("Login successful (user: %s)" % (username,))

        else:
            # Disconnect for bad auth
            # FIXME: "122" is the magic number for login problems.
            # See https://github.com/Astron/Astron/blob/master/doc/protocol/10-client.md
            self.air.eject(clientId, 122, "Bad credentials")
            
            # log login attempt
            self.notify.info("Ejecting client for bad credentials (user: %s)" % (username,))

# -------------------------------------------------------------------
# DistributedMaproot
# * has all avatars in its zone 0
# * generates new avatars
# -------------------------------------------------------------------

#class DistributedMaproot(DistributedObject):
#    def generateInit(self):
#        print(datetime.now().strftime("%H:%M:%S")+" DistributedMaproot.generateInit() for "+str(self.doId))
    
#class DistributedMaprootOV(DistributedObjectOV):
#    def generate(self):
#        print(datetime.now().strftime("%H:%M:%S")+" DistributedMaprootOV.generate() for "+str(self.doId))

class DistributedMaproot(DistributedObject):
    pass

class DistributedMaprootAI(DistributedObject):
    def generate(self):
        print(datetime.now().strftime("%H:%M:%S")+" DistributedMaprootAI.generate() for "+str(self.doId))
    
    def set_maproot(self):
        print(datetime.now().strftime("%H:%M:%S")+" DistributedMaprootAI.set_maproot() in "+str(self.doId))
        login_manager = self.air.generateGlobalObject(LoginManagerId, 'LoginManager')
        login_manager.set_maproot(self.doId)
    
    def createAvatar(self, clientId):
        print(datetime.now().strftime("%H:%M:%S")+" DistributedMaprootAI.createAvatar("+str(clientId)+") in "+str(self.doId))
        # Create the avatar
        avatar = DistributedAvatarAI(self.air)
        avatar.generateWithRequiredAndId(self.air.allocateChannel(), self.getDoId(), 0) # random doId, parentId, zoneId
        self.air.setAI(avatar.doId, self.air.ourChannel)
        # Set the client to be interested in our zone 0. He can't do
        # that himself (or rather: shouldn't be allowed to) as he has
        # no visibility of this object.
        # We're always using the interest_id 0 because different
        # clients use different ID spaces, so why make things more
        # complicated?
        self.air.clientAddInterest(clientId, 0, self.getDoId(), 0) # client, interest, parent, zone
        # Set its owner to the client, upon which in the Clients repo
        # magically OV (OwnerView) is generated.
        self.air.setOwner(avatar.getDoId(), clientId)
        # Declare this to be a session object.
        self.air.clientAddSessionObject(clientId, self.getDoId())

class DistributedMaprootUD(DistributedObject):
    def generate(self):
        print(datetime.now().strftime("%H:%M:%S")+" DistributedMaprootUD.generate() for "+str(self.doId))
        
    def create_avatar(self, clientId):
        print(datetime.now().strftime("%H:%M:%S")+" DistributedMaprootUD.create_avatar("+str(clientId)+") in "+str(self.doId))
        self.sendUpdate("createAvatar", # Field to call
                        [clientId])     # Arguments

# -------------------------------------------------------------------
# DistributedAvatar
# * represents players in the scene graph
# * routes indications of movement intents to AI
# * updates the actual position and orientation
# -------------------------------------------------------------------

class DistributedAvatar(DistributedObject):
    def init(self):
        print("DistributedAvatar")
        
    def generateInit(self):
        print(datetime.now().strftime("%H:%M:%S")+" DistributedAvatar.generateInit() for "+str(self.doId))
        model = base.loader.loadModel("models/smiley")
        model.reparent_to(self)
        model.setH(180.0)
        # Signal app that this is its avatar
        base.messenger.send("distributed_avatar", [self])

    def delete(self):
        print(datetime.now().strftime("%H:%M:%S")+" DistributedAvatar.delete() for "+str(self.doId))
        
    def setXYZH(self, *args):
        DistributedNode.setXYZH(self, *args)

class DistributedAvatarOV(DistributedObject):
    def init(self):
        print("DistributedAvatarOV")

    def generateInit(self):
        # Make yourself known to the client
        print(datetime.now().strftime("%H:%M:%S")+" DistributedAvatarOV.generate() for "+str(self.doId))
        base.messenger.send("avatar", [self])

    def delete(self):
        print(datetime.now().strftime("%H:%M:%S")+" DistributedAvatarOV.delete() for "+str(self.doId))
        
    def indicateIntent(self, heading, speed):
        self.sendUpdate("indicateIntent", [heading, speed])

class DistributedAvatarAI(DistributedObject):
    def generate(self, repository=None):
        print(datetime.now().strftime("%H:%M:%S")+" DistributedAvatarAI.generate() for "+str(self.doId))
        self.heading = 0.0
        self.speed = 0.0
        self.update_task = base.taskMgr.add(self.update_position, "Avatar position update")

    def delete(self):
        print(datetime.now().strftime("%H:%M:%S")+" DistributedAvatarAI.delete() for "+str(self.doId))
        base.taskMgr.remove(self.update_task)

    def indicateIntent(self, heading, speed):
        if (heading < -1.0) or (heading > 1.0) or (speed < -1.0) or (speed > 1.0):
            # Client is cheating!
            # FIXME: Eject client
            return
        self.heading = heading
        self.speed = speed
    
    def update_position(self, task):
        if (self.heading != 0.0) or (self.speed != 0.0):
            dt = globalClock.getDt()
            self.setH((self.getH() + self.heading * avatar_rotation_speed * dt) % 360.0)
            self.setY(self, self.speed * avatar_speed * dt)
            if self.getX() < -10.0:
                self.setX(-10.0)
            if self.getX() > 10.0:
                self.setX(10.0)
            if self.getY() < -10.0:
                self.setY(-10.0)
            if self.getY() > 10.0:
                self.setY(10.0)
            self.b_setXYZH(self.getX(), self.getY(), self.getZ(), self.getH())
        return Task.cont

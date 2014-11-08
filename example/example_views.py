from datetime import datetime

from astron.object_repository import DistributedObject
from shared_constants import LOGIN_MANAGER_DO_ID, MAP_ROOT_ZONE, AVATARS_PARENT, AVATARS_ZONE
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

class LoginManagerUD(DistributedObject):
    def init(self):
        self.maproot_distobjs = set()
        print("LoginManagerUD view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

    def login(self, sender, username, password):
        print("Received login request for %d" % (sender, ))
        if len(self.maproot_distobjs) > 0:
            if username == "guest" and password == "guest":
                # Login successful
                self.repo.send_CLIENTAGENT_SET_STATE(sender, 2, sender = self.do_id)
                print("  Logging in successfully")
                maproot_for_client = random.choice(list(self.maproot_distobjs))
                self.repo.distobj_by_do_id(maproot_for_client).create_avatar(sender, sender)
            else:
                # Bad credentials
                self.send_CLIENTAGENT_EJECT(sender, 122, "Bad credentials")
                print("  Disconnecting for bad credentials")
        else:
            # No maproot has appeared yet.
            # FIXME: ...or has left, and no replacement has arrived.
            self.send_CLIENTAGENT_EJECT(sender, 999, "Server isn't ready")
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

    def create_avatar(self, sender, client_id):
        print("%d called DistributedMaprootAI.create_avatar(%d)" % (sender, client_id))
        self.repo.create_distobj_db('DistributedAvatar', AVATARS_PARENT, AVATARS_ZONE, set_ai = True,
                                    creation_callback = self.avatar_created, additional_args = [client_id])
        # FIXME: Choose better interest_id

    def avatar_created(self, do_id, parent_id, zone_id, set_ai, client_id):
        print("Avatar was created, now adding interest, setting owner and session object.")
        self.repo.send_CLIENTAGENT_ADD_INTEREST(client_id, 666, AVATARS_PARENT, AVATARS_ZONE)
        self.repo.send_STATESERVER_OBJECT_SET_OWNER(do_id, client_id)
        self.repo.send_CLIENTAGENT_ADD_SESSION_OBJECT(do_id, client_id)
        
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
    def init(self):
        print("DistributedAvatar created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

class DistributedAvatarAI(DistributedObject):
    def init(self):
        print("DistributedAvatarAI created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

class DistributedAvatarOV(DistributedObject):
    def init(self):
        print("DistributedAvatarOV created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

from datetime import datetime

from astron.object_repository import DistributedObject
from shared_constants import LOGIN_SERVICE_ZONE, WORLD_ZONE, GAME_ROOT_DO_ID, AI_SERVICES_ZONE
import random

from pprint import pprint

# Game settings
avatar_speed = 3.0
avatar_rotation_speed = 90.0


# -------------------------------------------------------------------
# PointOfContact
# * Is the only DOG, and is the only distobj that a player can
#   contact before logging in.
# * Has interest in LoginServices
# * Redirects player logins to a LoginService, if possible.
# -------------------------------------------------------------------

class PointOfContact(DistributedObject):
    def init(self):
        print("PointOfContact view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

    def login(self, username, password):
        print("Client logging in")
        self.send_update("login", username, password)

class PointOfContactUD(DistributedObject):
    def init(self):
        self.add_ai_interest(GAME_ROOT_DO_ID, LOGIN_SERVICE_ZONE)
        self.login_services = {}
        print("PointOfContactUD view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

    def login(self, sender, username, password):
        print("Received login request for %d" % (sender, ))
        if len(self.login_services.keys()) > 0:
                view = random.choice(self.login_services.values())
                view.login(sender, username, password)
        else:
            # No login service is known.
            self.send_CLIENTAGENT_EJECT(sender, 999, "Server isn't ready for logins")
            print("  Dropping connection attempt due to missing LoginService")

    def interest_distobj_enter(self, view, do_id, parent_id, zone_id):
        print("  PointOfContactUD learned of new LoginService %d" % (do_id, ))
        if (parent_id == GAME_ROOT_DO_ID) and (zone_id == LOGIN_SERVICE_ZONE):
            self.login_services[do_id] = view

    def interest_changing_location_enter(self, sender, do_id, new_parent, new_zone, old_parent, old_zone):
        if (new_parent == GAME_ROOT_DO_ID) and (new_zone == LOGIN_SERVICE_ZONE):
            # A new maproot "service" has entered
            self.login_services.add(do_id)
            print("  PointOfContactUD added %d to maproot services." % (do_id, ))

    def interest_changing_location_leave(self, sender, do_id, new_parent, new_zone, old_parent, old_zone):
        if (old_parent == GAME_ROOT_DO_ID) and (old_zone == LOGIN_SERVICE_ZONE):
            # A maproot has just left
            self.login_services.remove(do_id)
            print("  PointOfContactUD removed %d from maproot services." % (do_id, ))

# -------------------------------------------------------------------
# GameRoot
# * Is a container for top-level objects, especially the world and
#   services.
# -------------------------------------------------------------------

class GameRoot(DistributedObject):
    pass

class GameRootAI(DistributedObject):
    pass

class GameRootAE(DistributedObject):
    pass

# -------------------------------------------------------------------
# LoginService
# * Registers a CharacterServer
# * Authenticates Clients
# * Makes CharacterServer create an avatar for new Clients.
# -------------------------------------------------------------------

# This one isn't used on the client.
class LoginService(DistributedObject):
    def init(self):
        print("LoginService view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

class LoginServiceAE(DistributedObject):
    def init(self):
        print("LoginServiceAE view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

    def login(self, client_channel, username, password):
        print("  LoginServiceAE %d received login request for %d" % (self.do_id, client_channel, ))
        self.send_update('login', client_channel, username, password)
        
class LoginServiceAI(DistributedObject):
    def init(self):
        self.add_ai_interest(GAME_ROOT_DO_ID, WORLD_ZONE)
        self.worlds = {}
        print("LoginServiceAI view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

    def login(self, sender, client_channel, username, password):
        print("  LoginServiceAI %d received login request for %d" % (self.do_id, client_channel, ))
        if username == "guest" and password == "guest":
            # Login successful
            self.repo.send_CLIENTAGENT_SET_STATE(client_channel, 2, sender = self.do_id)
            print("  Logging in successfully")
            # FIXME: Create Avatar
        else:
            # Bad credentials
            self.send_CLIENTAGENT_EJECT(client_channel, 122, "Bad credentials")
            print("  Disconnecting for bad credentials")

    def interest_distobj_enter(self, view, do_id, parent_id, zone_id):
        if (parent_id == GAME_ROOT_DO_ID) and (zone_id == WORLD_ZONE):
            print("  LoginServiceAI learned of new World %d" % (do_id, ))
            self.worlds[do_id] = view

# -------------------------------------------------------------------
# World
# * is a container for Avatars (so far)
# -------------------------------------------------------------------

class World(DistributedObject):
    pass

class WorldAI(DistributedObject):
    def init(self):
        self.add_ai_interest(GAME_ROOT_DO_ID, AI_SERVICES_ZONE)
        self.ai_services = {}
        print("WorldAI view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

    def create_avatar(self, sender, client):
        print("  not implemented: WorldAI %d should create avatar for %d" % (self.do_id, client))

    def interest_distobj_enter(self, view, do_id, parent_id, zone_id):
        if (parent_id == GAME_ROOT_DO_ID) and (zone_id == AI_SERVICES_ZONE):
            print("  LoginServiceAI learned of new AIServer %d" % (do_id, ))
            self.ai_services[do_id] = view

class WorldAE(DistributedObject):
    def init(self):
        print("WorldAE view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))
        
    def create_avatar(self, client):
        self.send_update('create_avatar', client)

# -------------------------------------------------------------------
# CharacterServer
# * has all avatars in its zone 0
# * generates new avatars
# -------------------------------------------------------------------

class AIServer(DistributedObject):
    pass

class AIServerAI(DistributedObject):
    def init(self):
        print("AIServerAI view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))
        # self.repo.add_ai_interest(WORLD_PARENT, WORLD_ZONE)

    #def create_avatar(self, sender, client_id):
    #    print("%d called CharacterServerAI.create_avatar(%d)" % (sender, client_id))
    #    self.repo.create_distobj_db('Avatar', AVATARS_PARENT, AVATARS_ZONE, set_ai = True,
    #                                creation_callback = self.avatar_created, additional_args = [client_id])
    #    # FIXME: Choose better interest_id
    #
    #def avatar_created(self, do_id, parent_id, zone_id, set_ai, client_id):
    #    print("Avatar was created, now adding interest, setting owner and session object.")
    #    self.repo.send_CLIENTAGENT_ADD_INTEREST(client_id, 666, AVATARS_PARENT, AVATARS_ZONE)
    #    self.repo.send_STATESERVER_OBJECT_SET_OWNER(do_id, client_id)
    #    self.repo.send_CLIENTAGENT_ADD_SESSION_OBJECT(do_id, client_id)
        
class AIServerAE(DistributedObject):
    def init(self):
        print("AIServerAE view created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))
    
    def create_avatar(self, sender, client_id):
        print("  AIServerAE.create_avatar(sender %d, client_id %d)" % (sender, client_id))
        self.send_update('create_avatar', client_id)

# -------------------------------------------------------------------
# Avatar
# * represents players in the scene graph
# * routes indications of movement intents to AI
# * updates the actual position and orientation
# -------------------------------------------------------------------

class Avatar(DistributedObject):
    def init(self):
        print("Avatar created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

class AvatarAI(DistributedObject):
    def init(self):
        print("AvatarAI created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

class AvatarAE(DistributedObject):
    def init(self):
        print("AvatarAE created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

class AvatarOV(DistributedObject):
    def init(self):
        print("AvatarOV created for %d in (%d, %d)" % (self.do_id, self.parent, self.zone))

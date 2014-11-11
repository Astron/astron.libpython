# TODO
# * CLIENT_HEARTBEAT =  5

from bamboo import dcfile, module, traits
from bamboo.wire import Datagram, DatagramIterator
from connection import Connection
import client_messages as clientmsg
import internal_messages as servermsg
from helpers import parent_zone_to_location, separate_fields
import importlib

DATAGRAM_SIZE = 2
DATAGRAM_ENCODING = '<H'

MSG_TYPE_INTERNAL = 1
MSG_TYPE_CLIENT = 2

# This depends on MSG_TYPE_* already being defined.
from distributed_object import DistributedObject

astron_keywords = ['clsend', 'ownsend',
                   'broadcast', 'clrecv', 'ownrecv', 'airecv',
                   'ram', 'required', 'db']
default_host = "127.0.0.1"
default_internal_port = 7199
default_client_port = 7198
default_dcfilename = "astron.dc"


class ObjectRepository(Connection):
    def __init__(self, dcfilename=default_dcfilename):
        Connection.__init__(self)
        self.mod = module.Module()
        # Add Astron-specific keywords
        for word in astron_keywords:
            self.mod.add_keyword(word)
        dcfile.parse_dcfile(self.mod, dcfilename)
        # Create class definition dicts
        self.create_dclass_dicts()
        self.distributed_objects = {}
        self.owner_views = {}

        self.handlers = {}
        
        # FIXME: Maybe move this into ClientRepository, if Internals won't get Interests in the future.
        # FIXME: Actually, fold this into the general callback mechanism.
        self.interest_counters = {}
        self.interest_callback_map = {}

        # The callback system for handling *_RESP messages
        self.msg_to_msgresp_map = {
            servermsg.STATESERVER_OBJECT_GET_FIELD        : servermsg.STATESERVER_OBJECT_GET_FIELD_RESP,
            servermsg.STATESERVER_OBJECT_GET_FIELDS       : servermsg.STATESERVER_OBJECT_GET_FIELDS_RESP,
            servermsg.STATESERVER_OBJECT_GET_ALL          : servermsg.STATESERVER_OBJECT_GET_ALL_RESP,
            servermsg.STATESERVER_OBJECT_GET_LOCATION     : servermsg.STATESERVER_OBJECT_GET_LOCATION_RESP,
            servermsg.STATESERVER_OBJECT_GET_AI           : servermsg.STATESERVER_OBJECT_GET_AI_RESP,
            servermsg.STATESERVER_OBJECT_GET_OWNER        : servermsg.STATESERVER_OBJECT_GET_OWNER_RESP,
            servermsg.STATESERVER_OBJECT_GET_ZONE_COUNT   : servermsg.STATESERVER_OBJECT_GET_ZONE_COUNT_RESP,
            servermsg.STATESERVER_OBJECT_GET_ZONES_COUNT  : servermsg.STATESERVER_OBJECT_GET_ZONES_COUNT_RESP,
            servermsg.STATESERVER_OBJECT_GET_CHILD_COUNT  : servermsg.STATESERVER_OBJECT_GET_CHILD_COUNT_RESP,
            servermsg.DBSS_OBJECT_GET_ACTIVATED           : servermsg.DBSS_OBJECT_GET_ACTIVATED_RESP,
            servermsg.DBSERVER_CREATE_OBJECT              : servermsg.DBSERVER_CREATE_OBJECT_RESP,
            servermsg.DBSERVER_OBJECT_GET_FIELD           : servermsg.DBSERVER_OBJECT_GET_FIELD_RESP,
            servermsg.DBSERVER_OBJECT_GET_FIELDS          : servermsg.DBSERVER_OBJECT_GET_FIELDS_RESP,
            servermsg.DBSERVER_OBJECT_GET_ALL             : servermsg.DBSERVER_OBJECT_GET_ALL_RESP,
            servermsg.DBSERVER_OBJECT_SET_FIELD_IF_EQUALS : servermsg.DBSERVER_OBJECT_SET_FIELD_IF_EQUALS_RESP,
            servermsg.DBSERVER_OBJECT_SET_FIELDS_IF_EQUALS: servermsg.DBSERVER_OBJECT_SET_FIELDS_IF_EQUALS_RESP,
            servermsg.DBSERVER_OBJECT_SET_FIELD_IF_EMPTY  : servermsg.DBSERVER_OBJECT_SET_FIELD_IF_EMPTY_RESP,
            }
        self.context_counters = {
            servermsg.STATESERVER_OBJECT_GET_FIELD_RESP        : 0,
            servermsg.STATESERVER_OBJECT_GET_FIELDS_RESP       : 0,
            servermsg.STATESERVER_OBJECT_GET_ALL_RESP          : 0,
            servermsg.STATESERVER_OBJECT_GET_LOCATION_RESP     : 0,
            servermsg.STATESERVER_OBJECT_GET_AI_RESP           : 0,
            servermsg.STATESERVER_OBJECT_GET_OWNER_RESP        : 0,
            servermsg.STATESERVER_OBJECT_GET_ZONE_COUNT_RESP   : 0,
            servermsg.STATESERVER_OBJECT_GET_ZONES_COUNT_RESP  : 0,
            servermsg.STATESERVER_OBJECT_GET_CHILD_COUNT_RESP  : 0,
            servermsg.DBSS_OBJECT_GET_ACTIVATED_RESP           : 0,
            servermsg.DBSERVER_CREATE_OBJECT_RESP              : 0,
            servermsg.DBSERVER_OBJECT_GET_FIELD_RESP           : 0,
            servermsg.DBSERVER_OBJECT_GET_FIELDS_RESP          : 0,
            servermsg.DBSERVER_OBJECT_GET_ALL_RESP             : 0,
            servermsg.DBSERVER_OBJECT_SET_FIELD_IF_EQUALS_RESP : 0,
            servermsg.DBSERVER_OBJECT_SET_FIELDS_IF_EQUALS_RESP: 0,
            servermsg.DBSERVER_OBJECT_SET_FIELD_IF_EMPTY_RESP  : 0,
            }
        self.callbacks = {}

    def create_dclass_dicts(self):
        self.dclass_id_to_cls = {}   # (<int>, 'PF'): <Class>
        self.dclass_id_to_name = {}  # (<int>, 'PF'): 'DClass'
        self.dclass_name_to_id = {}  # 'DClassPF'   : <int>  , ('DClass', 'PF') : <int>
        self.dclass_name_to_cls = {} # 'DClassPF'   : <Class>, ('DClass', 'PF') : <Class>
        for dclass_id in range(0, self.mod.num_imports()):
            # Determine and import the module
            dclass_module_name = self.mod.get_import(dclass_id).module
            dclass_module = importlib.import_module(dclass_module_name)
            for symbol in self.mod.get_import(dclass_id).symbols:
                # Figure out the names of used classes
                fragments = str(symbol).split('/')
                base_class = fragments[0]
                postfixes = fragments[1:] + ['']
                for postfix in postfixes:
                    #print(dclass_module, base_class + postfix)
                    cls = getattr(dclass_module, base_class + postfix)
                    self.dclass_id_to_cls[(dclass_id, postfix)] = cls
                    self.dclass_id_to_name[(dclass_id, postfix)] = base_class
                    self.dclass_name_to_id[base_class + postfix] = dclass_id
                    self.dclass_name_to_id[(base_class, postfix)] = dclass_id
                    self.dclass_name_to_cls[base_class + postfix] = cls
                    self.dclass_name_to_cls[(base_class, postfix)] = cls

    def distobj_by_do_id(self, do_id):
        try:
            return self.distributed_objects[do_id]
        except KeyError:
            print("KeyError: No view for do_id %d present." % (do_id, ))

    def poll_till_empty(self):
        """Process all received messages.

        Return False if the connection hasn't been opened yet or has
        been closed.
        """
        # FIXME: A disambiguation between "not active yet" and "not
        # active anymore" is needed.
        #if not self.is_active():
        #    return False

        try:
            while True:
                dg = self.poll_datagram()
                if dg is not None:
                    self.handle_datagram(dg)
                else:
                    break
            # We're finished reading for now,
            # but the connection is still active.
            return True
        except EOFError:
            return False

    def poll_forever(self):
        """Blocks until connection is lost. Processes datagrams as
        they come in. Be sure to call this in a dedicated thread."""
        try:
            while True:
                dg = self.poll_datagram()
                if dg is not None:
                    self.handle_datagram(dg)
        except EOFError:
            return

    def handle_datagram(self, dg):
        print("ObjectRepository.handle_datagram(dg) was called, but should have been overloaded.")
        pass

    # Creating client/AI-side views

    def create_view_from_datagram(self, dgi, cls_postfix = ''):
        do_id = dgi.read_uint32()
        # Only create a view if one doesn't already exist!
        if not (do_id in self.distributed_objects.keys()):
            parent_id = dgi.read_uint32()
            zone_id = dgi.read_uint32()
            dclass_id = dgi.read_uint16()
            # Create the view object
            cls = self.dclass_id_to_cls[(dclass_id, cls_postfix)]
            dist_obj = cls(self, dclass_id, do_id, parent_id, zone_id)
            self.distributed_objects[do_id] = dist_obj
            # FIXME: Read the field values from the dgi and apply them
            dist_obj.init()
            return dist_obj, do_id, parent_id, zone_id
        else:
            return False

    def create_distobjglobal_view(self, cls_name, do_id, set_ai = False):
        cls = self.dclass_name_to_cls[cls_name]
        dclass_id = self.dclass_name_to_id[cls_name]
        dist_obj = cls(self, dclass_id, do_id, 0, 0)
        self.distributed_objects[do_id] = dist_obj
        dist_obj.init()
        # FIXME: Now set interest in that do_id to get messages if you're the "UD"
        if set_ai:
            self.send_CONTROL_ADD_CHANNEL(do_id)
        return dist_obj

    # Callback management for *_RESP messages

    def register_callback(self, msg_type, callback, args = [], kwargs = {}):
        resp_msg_type = self.msg_to_msgresp_map[msg_type]
        context = self.context_counters[resp_msg_type]
        self.context_counters[resp_msg_type] += 1
        self.callbacks[(resp_msg_type, context)] = (callback, args, kwargs)
        return context

    def fire_callback(self, resp_msg_type, context):
        callback = self.callbacks[(resp_msg_type, context)]
        del self.callbacks[(resp_msg_type, context)]
        return callback

class InternalRepository(ObjectRepository):
    def __init__(self, dcfilename=default_dcfilename, stateserver = 400000, dbss = 400001, ai_channel=500000):
        ObjectRepository.__init__(self, dcfilename=dcfilename)
        self.stateserver = stateserver
        self.dbss = dbss
        self.ai_channel = ai_channel
        self.msg_type = MSG_TYPE_INTERNAL
        self.handlers.update({
            servermsg.STATESERVER_OBJECT_SET_FIELD                   : self.handle_STATESERVER_OBJECT_SET_FIELD,
            servermsg.STATESERVER_OBJECT_CHANGING_LOCATION           : self.handle_STATESERVER_OBJECT_CHANGING_LOCATION,
            servermsg.STATESERVER_OBJECT_GET_AI                      : self.handle_STATESERVER_OBJECT_GET_AI,
            servermsg.STATESERVER_OBJECT_ENTER_LOCATION_WITH_REQUIRED: self.handle_STATESERVER_OBJECT_ENTER_LOCATION_WITH_REQUIRED,
            servermsg.STATESERVER_OBJECT_ENTER_AI_WITH_REQUIRED      : self.handle_STATESERVER_OBJECT_ENTER_AI_WITH_REQUIRED,
            servermsg.DBSERVER_CREATE_OBJECT_RESP                    : self.handle_DBSERVER_CREATE_OBJECT_RESP,
            # FIXME: Add handlers for incoming messages
            })
        self.global_views = {}
        
    def connect(self, connection_success, connection_failure,
                host=default_host, port=default_client_port):
        # FIXME: Handle connection failures
        ObjectRepository.connect(self, host, port)
        self.send_CONTROL_ADD_CHANNEL(self.ai_channel)
        connection_success()
        
    def handle_datagram(self, dg):
        dgi = DatagramIterator(dg)
        num_recipients = dgi.read_uint8()
        recipients = [dgi.read_uint64() for _ in range(0, num_recipients)]
        sender = dgi.read_uint64()
        msgtype = dgi.read_uint16()
        if msgtype in self.handlers.keys():
            self.handlers[msgtype](dgi, sender, recipients)
        else:
            print("Received unhandled message type " + str(msgtype))

    def create_message_stub(self, sender, *recipients):
        dg = Datagram()
        dg.add_uint8(len(recipients))
        for recipient in recipients:
            dg.add_uint64(recipient)
        dg.add_uint64(sender)
        return dg

    # Creating views and/or distobjs

    def create_distobj(self, cls_name, do_id, parent_id, zone_id, set_ai = False):
        dclass_id = self.dclass_name_to_id[cls_name]
        self.send_STATESERVER_CREATE_OBJECT_WITH_REQUIRED(dclass_id, do_id, parent_id, zone_id)
        if set_ai:
            self.send_STATESERVER_OBJECT_SET_AI(do_id)

    def create_distobj_db(self, cls_name, parent_id, zone_ai, set_ai = False, creation_callback = False, additional_args = []):
        dclass_id = self.dclass_name_to_id[cls_name]
        if not creation_callback:
            context = self.register_callback(servermsg.DBSERVER_CREATE_OBJECT,
                                             self.create_distobj_db_callback,
                                             args = [parent_id, zone_ai, set_ai])
        else:
            context = self.register_callback(servermsg.DBSERVER_CREATE_OBJECT,
                                             self.create_distobj_db_callback,
                                             args = [parent_id, zone_ai, set_ai, creation_callback, additional_args])
        self.send_DBSERVER_CREATE_OBJECT(dclass_id, context)

    def create_distobj_db_callback(self, do_id, parent_id, zone_id, set_ai, creation_callback = False, additional_args = []):
        """For internal use only. Should activate a DB object after its creation."""
        print(" DB distobj %d created, now moving into (%d, %d), setting AI? %s" % (do_id, parent_id, zone_id, str(set_ai)))
        self.send_DBSS_OBJECT_ACTIVATE_WITH_DEFAULTS(do_id, parent_id, zone_id)
        if set_ai:
            self.send_STATESERVER_OBJECT_SET_AI(do_id)
        # FIXME: STATESERVER_OBJECT_SET_LOCATION not required?
        # FIXME: Do SET_AI if requested
        if creation_callback:
            creation_callback(do_id, parent_id, zone_id, set_ai, *additional_args)

    # Sending messages
    
    def send_CONTROL_ADD_CHANNEL(self, channel):
        # CONTROL messages don't have sender fields
        dg = Datagram()
        dg.add_uint8(1)  # Number of recipients
        dg.add_uint64(1) # Recipient (control channel)
        dg.add_uint16(servermsg.CONTROL_ADD_CHANNEL)
        dg.add_uint64(channel)
        self.send_datagram(dg)

    def send_STATESERVER_OBJECT_SET_AI(self, do_id):
        dg = self.create_message_stub(self.ai_channel, do_id)
        dg.add_uint16(servermsg.STATESERVER_OBJECT_SET_AI)
        dg.add_uint64(self.ai_channel)
        self.send_datagram(dg)
        
    def send_STATESERVER_DELETE_AI_OBJECTS(self):
        dg = self.create_message_stub(self.ai_channel, self.stateserver)
        dg.add_uint16(servermsg.STATESERVER_DELETE_AI_OBJECTS)
        dg.add_uint64(self.ai_channel)
        self.send_datagram(dg)

    def send_STATESERVER_CREATE_OBJECT_WITH_REQUIRED(self, dclass_id, do_id, parent, zone):
        dg = self.create_message_stub(self.ai_channel, self.stateserver)
        dg.add_uint16(servermsg.STATESERVER_CREATE_OBJECT_WITH_REQUIRED)
        dg.add_uint32(do_id)
        dg.add_uint32(parent)
        dg.add_uint32(zone)
        dg.add_uint16(dclass_id)
        # FIXME: Add REQUIRED fields
        self.send_datagram(dg)

    def send_STATESERVER_CREATE_OBJECT_WITH_REQUIRED_OTHER(self):
        dg = self.create_message_stub(self.do_id, self.stateserver)
        dg.add_uint16(servermsg.STATESERVER_CREATE_OBJECT_WITH_REQUIRED_OTHER)
        dg.add_uint32(self.do_id)
        dg.add_uint32(self.parent)
        dg.add_uint32(self.zone)
        dg.add_uint16(self.dclass_id)
        # FIXME: Add REQUIRED fields
        # FIXME: Add OTHER fields
        self.send_datagram(dg)

    def send_DBSERVER_CREATE_OBJECT(self, dclass_id, context):
        dg = self.create_message_stub(self.ai_channel, self.dbss)
        dg.add_uint16(servermsg.DBSERVER_CREATE_OBJECT)
        dg.add_uint32(context)
        dg.add_uint16(dclass_id)
        # FIXME: This is actually `uint16 field_count`, `[uint16 field_id, <VALUE>]*field_count`
        # and should be accessible via create_distobj_db
        dg.add_uint16(0)
        self.send_datagram(dg)
    
    def send_DBSS_OBJECT_ACTIVATE_WITH_DEFAULTS(self, do_id, parent_id, zone_id):
        dg = self.create_message_stub(self.ai_channel, do_id)
        dg.add_uint16(servermsg.DBSS_OBJECT_ACTIVATE_WITH_DEFAULTS)
        dg.add_uint32(do_id)
        dg.add_uint32(parent_id)
        dg.add_uint32(zone_id)
        self.send_datagram(dg)

    def send_CLIENTAGENT_SET_STATE(self, clientagent, ca_state, sender = 0):
        if sender == 0:
            sender = self.ai_channel
        dg = self.create_message_stub(sender, clientagent)
        dg.add_uint16(servermsg.CLIENTAGENT_SET_STATE)
        dg.add_uint16(ca_state)
        self.send_datagram(dg)
    
    def send_CLIENTAGENT_ADD_SESSION_OBJECT(self, do_id, client_channel):
        dg = self.create_message_stub(self.ai_channel, client_channel)
        dg.add_uint16(servermsg.CLIENTAGENT_ADD_SESSION_OBJECT)
        dg.add_uint32(do_id)
        self.send_datagram(dg)

    def send_CLIENTAGENT_ADD_INTEREST(self, client_channel, interest_id, parent_id, zone_id):
        dg = self.create_message_stub(self.ai_channel, client_channel)
        dg.add_uint16(servermsg.CLIENTAGENT_ADD_INTEREST)
        dg.add_uint16(interest_id)
        dg.add_uint32(parent_id)
        dg.add_uint32(zone_id)
        self.send_datagram(dg)

    def send_STATESERVER_OBJECT_SET_OWNER(self, do_id, owner):
        dg = self.create_message_stub(self.ai_channel, do_id)
        dg.add_uint16(servermsg.STATESERVER_OBJECT_SET_OWNER)
        dg.add_uint64(owner)
        self.send_datagram(dg)

    def send_STATESERVER_OBJECT_GET_ZONE_OBJECTS(self, context, parent_id, zone_id):
        dg = self.create_message_stub(self.ai_channel, parent_id)
        dg.add_uint16(servermsg.STATESERVER_OBJECT_GET_ZONE_OBJECTS)
        dg.add_uint32(context)
        dg.add_uint32(parent_id)
        dg.add_uint32(zone_id)
        self.send_datagram(dg)

    # Receive messages

    def handle_STATESERVER_OBJECT_SET_FIELD(self, dgi, sender, recipients):
        do_id = dgi.read_uint32()
        field_id = dgi.read_uint16()
        self.distributed_objects[do_id].update_field(sender, field_id, dgi)

    def handle_STATESERVER_OBJECT_CHANGING_LOCATION(self, dgi, sender, recipients):
        print("handle_STATESERVER_OBJECT_CHANGING_LOCATION", sender, recipients)
        do_id = dgi.read_uint32()
        new_parent = dgi.read_uint32()
        new_zone = dgi.read_uint32()
        old_parent = dgi.read_uint32()
        old_zone = dgi.read_uint32()
        # FIXME: Do nothing else.
        
    def handle_STATESERVER_OBJECT_GET_AI(self, dgi, sender, recipients):
        print("handle_STATESERVER_OBJECT_GET_AI", sender, recipients)
        context = dgi.read_uint32()
        print("  Context: %d" % (context, ))
        # FIXME: Implement
        
    def handle_STATESERVER_OBJECT_ENTER_LOCATION_WITH_REQUIRED(self, dgi, sender, recipients):
        self.create_view_from_datagram(dgi, cls_postfix = 'AE')
        
    def handle_STATESERVER_OBJECT_ENTER_AI_WITH_REQUIRED(self, dgi, sender, recipients):
        self.create_view_from_datagram(dgi, cls_postfix = 'AI')

    def handle_DBSERVER_CREATE_OBJECT_RESP(self, dgi, sender, recipients):
        context = dgi.read_uint32()
        do_id = dgi.read_uint32()
        print("Received DBSERVER_CREATE_OBJECT_RESP for %d, sender %d, recipients %s" % (do_id, sender, str(recipients)))
        callback, args, kwargs = self.fire_callback(servermsg.DBSERVER_CREATE_OBJECT_RESP, context)
        callback(do_id, *args, **kwargs)

class InterestInternalRepository(InternalRepository):
    def __init__(self, *args, **kwargs):
        InternalRepository.__init__(self, *args, **kwargs)
        self.repo_interests = set()
        self.distobj_interests_do_id_to_locations = {}
        self.distobj_interests_location_to_do_id = {}
    
    def add_ai_interest(self, distobj_id, zone_id, by_distobj = False):
        if by_distobj:
            print("Interest for %d in (%d, %d)" % (by_distobj, distobj_id, zone_id))
            if not (by_distobj in self.distobj_interests_do_id_to_locations.keys()):
                self.distobj_interests_do_id_to_locations[by_distobj] = [parent_zone_to_location(distobj_id, zone_id)]
            else:
                self.distobj_interests_do_id_to_locations[by_distobj].append(parent_zone_to_location(distobj_id, zone_id))
            if not (by_distobj in self.distobj_interests_location_to_do_id.keys()):
                self.distobj_interests_location_to_do_id[parent_zone_to_location(distobj_id, zone_id)] = [by_distobj]
            else:
                self.distobj_interests_location_to_do_id[parent_zone_to_location(distobj_id, zone_id)].append(by_distobj)
        else:
            print("Interest for repo in (%d, %d)" % (distobj_id, zone_id))
            self.repo_interests.add(parent_zone_to_location(distobj_id, zone_id))
        self.send_CONTROL_ADD_CHANNEL(parent_zone_to_location(distobj_id, zone_id))
        # Request list of objects already existing in that zone for ENTER 
        # FIXME: Can we do something with the context?
        print("repo: STATESERVER_OBJECT_GET_ZONE_OBJECTS(%d, %d)" % (distobj_id, zone_id))
        self.send_STATESERVER_OBJECT_GET_ZONE_OBJECTS(0, distobj_id, zone_id)
        # FIXME: Messages for DOs that haven't entered yet may come
        # over the control channel. Either some kind of solution is
        # needed, or AIR interests shall be implemented in Astron as
        # actual messages.

    def remove_ai_interest(self, distobj_id, zone_id, by_distobj = False):
        # FIXME: Implement
        pass

    # Overwrites
    #            return dist_obj, do_id, parent_id, zone_id
    def handle_STATESERVER_OBJECT_ENTER_LOCATION_WITH_REQUIRED(self, dgi, sender, recipients):
        new_distobj = self.create_view_from_datagram(dgi, cls_postfix = 'AE')
        if new_distobj:
            view, do_id, parent_id, zone_id = new_distobj
            if parent_zone_to_location(parent_id, zone_id) in self.distobj_interests_location_to_do_id.keys():
                interested_distobjs = self.distobj_interests_location_to_do_id[parent_zone_to_location(parent_id, zone_id)]
                for distobj in interested_distobjs:
                    self.distributed_objects[distobj].interest_distobj_enter(view, do_id, parent_id, zone_id)
        
    def handle_STATESERVER_OBJECT_ENTER_AI_WITH_REQUIRED(self, dgi, sender, recipients):
        new_distobj = self.create_view_from_datagram(dgi, cls_postfix = 'AI')
        if new_distobj:
            view, do_id, parent_id, zone_id = new_distobj 
            if parent_zone_to_location(parent_id, zone_id) in self.distobj_interests_location_to_do_id.keys():
                interested_distobjs = self.distobj_interests_location_to_do_id[parent_zone_to_location(parent_id, zone_id)]
                for distobj in interested_distobjs:
                    self.distributed_objects[distobj].interest_distobj_ai_enter(view, do_id, parent_id, zone_id)

    def handle_STATESERVER_OBJECT_CHANGING_LOCATION(self, dgi, sender, recipients):
        print("handle_STATESERVER_OBJECT_CHANGING_LOCATION", sender, recipients)
        do_id = dgi.read_uint32()
        new_parent = dgi.read_uint32()
        new_zone = dgi.read_uint32()
        old_parent = dgi.read_uint32()
        old_zone = dgi.read_uint32()
        if parent_zone_to_location(new_parent, new_zone) in self.distobj_interests_location_to_do_id.keys():
            interested_distobjs = self.distobj_interests_location_to_do_id[parent_zone_to_location(new_parent, new_zone)]
            for distobj in interested_distobjs:
                self.distributed_objects[distobj].interest_changing_location_enter(sender, do_id, new_parent, new_zone, old_parent, old_zone)
        if parent_zone_to_location(old_parent, old_zone) in self.distobj_interests_location_to_do_id.keys():
            interested_distobjs = self.distobj_interests_location_to_do_id[parent_zone_to_location(old_parent, old_zone)]
            for distobj in interested_distobjs:
                self.distributed_objects[distobj].interest_changing_location_leave(sender, do_id, new_parent, new_zone, old_parent, old_zone)

class ClientRepository(ObjectRepository):
    def __init__(self, version_string, dcfilename=default_dcfilename):
        ObjectRepository.__init__(self, dcfilename=dcfilename)
        self.version_string = version_string
        self.msg_type = MSG_TYPE_CLIENT
        self.handlers.update({
            clientmsg.CLIENT_HELLO_RESP:                        self.handle_CLIENT_HELLO_RESP,
            clientmsg.CLIENT_EJECT:                             self.handle_CLIENT_EJECT,
            clientmsg.CLIENT_DONE_INTEREST_RESP:                self.handle_CLIENT_DONE_INTEREST_RESP,
            clientmsg.CLIENT_OBJECT_SET_FIELD:                  self.handle_CLIENT_OBJECT_SET_FIELD,
            clientmsg.CLIENT_OBJECT_SET_FIELDS:                 self.handle_CLIENT_OBJECT_SET_FIELDS,
            clientmsg.CLIENT_OBJECT_LOCATION:                   self.handle_CLIENT_OBJECT_LOCATION,
            clientmsg.CLIENT_OBJECT_LEAVING:                    self.handle_CLIENT_OBJECT_LEAVING,
            clientmsg.CLIENT_OBJECT_LEAVING_OWNER:              self.handle_CLIENT_OBJECT_LEAVING_OWNER,
            clientmsg.CLIENT_ENTER_OBJECT_REQUIRED:             self.handle_CLIENT_ENTER_OBJECT_REQUIRED,
            clientmsg.CLIENT_ENTER_OBJECT_REQUIRED_OTHER:       self.handle_CLIENT_ENTER_OBJECT_REQUIRED_OTHER,
            clientmsg.CLIENT_ENTER_OBJECT_REQUIRED_OWNER:       self.handle_CLIENT_ENTER_OBJECT_REQUIRED_OWNER,
            clientmsg.CLIENT_ENTER_OBJECT_REQUIRED_OTHER_OWNER: self.handle_CLIENT_ENTER_OBJECT_REQUIRED_OTHER_OWNER,
            clientmsg.CLIENT_ADD_INTEREST                     : self.handle_CLIENT_ADD_INTEREST,
            })

    def connect(self, connection_success, connection_failure, connection_eject,
                host=default_host, port=default_client_port):
        self.connection_success = connection_success
        self.connection_failure = connection_failure
        self.connection_eject = connection_eject

        ObjectRepository.connect(self, host, port)
        self.send_CLIENT_HELLO()
        
    def create_message_stub(self):
        dg = Datagram()
        return dg

    def handle_datagram(self, dg):
        dgi = DatagramIterator(dg)
        msgtype = dgi.read_uint16()
        if msgtype in self.handlers.keys():
            self.handlers[msgtype](dgi)
        else:
            print("Received unhandled message type " + str(msgtype))

    # Sending messages

    def send_CLIENT_HELLO(self):
        dg = Datagram()
        dg.add_uint16(clientmsg.CLIENT_HELLO)
        dg.add_uint32(traits.legacy_hash(self.mod))
        dg.add_string(self.version_string)
        self.send_datagram(dg)

    def send_CLIENT_DISCONNECT(self):
        dg = Datagram()
        dg.add_uint16(clientmsg.CLIENT_DISCONNECT)
        self.send_datagram(dg)
        # FIXME: The connection should be closed right now.
        #   What about later reads of cached messages?

    def send_CLIENT_ADD_INTEREST(self,
                                 parent_id, zone_id,
                                 interest_id = 0,
                                 callback = False, callback_args = [], callback_kwargs = {}):
        if not (interest_id in self.interest_counters.keys()):
            self.interest_counters[interest_id] = -1
        # FIXME: This needs to be protected against uint32 roll-overs. I'll probably
        # need to have a set of freed context_ids. But what if there are no more
        # usable context_ids? Raise an Exception?
        self.interest_counters[interest_id] = self.interest_counters[interest_id] + 1
        context_id = self.interest_counters[interest_id]
        dg = Datagram()
        dg.add_uint16(clientmsg.CLIENT_ADD_INTEREST)
        dg.add_uint32(context_id)
        dg.add_uint16(interest_id)
        dg.add_uint32(parent_id)
        dg.add_uint32(zone_id)
        self.send_datagram(dg)
        if callback != False:
            self.interest_callback_map[(interest_id, context_id)] = (callback, callback_args, callback_kwargs)
        return context_id

    def send_CLIENT_ADD_INTEREST_MULTIPLE(self,
                                          parent_id, zone_ids,
                                          interest_id = 0,
                                          callback = False, callback_args = [], callback_kwargs = {}):
        zone_count = len(zone_ids)
        # FIXME: interest_id (uint16), parent_id (uint32), zone_id (uint32) should
        # be asserted.
        if not (interest_id in self.interest_counters.keys()):
            self.interest_counters[interest_id] = -1
        # FIXME: This needs to be protected against uint32 roll-overs. I'll probably
        # need to have a set of freed context_ids. But what if there are no more
        # usable context_ids? Raise an Exception?
        self.interest_counters[interest_id] = self.interest_counters[interest_id] + 1
        context_id = self.interest_counters[interest_id]
        dg = Datagram()
        dg.add_uint16(clientmsg.CLIENT_ADD_INTEREST_MULTIPLE)
        dg.add_uint32(context_id)
        dg.add_uint16(interest_id)
        dg.add_uint32(parent_id)
        dg.add_uint16(zone_count)
        for zone_id in zone_ids:
            dg.add_uint32(zone_id)
        self.send_datagram(dg)
        if callback != False:
            self.interest_callback_map[(interest_id, context_id)] = (callback, callback_args, callback_kwargs)
        return context_id
    
    def send_CLIENT_REMOVE_INTEREST(self, interest_id, context_id):
        # FIXME: Should something be done about callbacks here?
        dg = Datagram()
        dg.add_uint16(clientmsg.CLIENT_REMOVE_INTEREST)
        dg.add_uint32(context_id)
        dg.add_uint16(interest_id)
        self.send_datagram(dg)

    def send_CLIENT_OBJECT_SET_FIELD(self):
        # FIXME: Needs signature and implementation
        pass

    def send_CLIENT_OBJECT_SET_FIELDS(self):
        # FIXME: Needs signature and implementation
        pass

    # Receive messages

    def handle_CLIENT_HELLO_RESP(self, dgi):
        self.connection_success()

    def handle_CLIENT_EJECT(self, dgi):
        error_code = dgi.read_uint16()
        reason = dgi.read_string()
        self.connection_eject(error_code, reason)

    def handle_CLIENT_DONE_INTEREST_RESP(self, dgi):
        context_id = dgi.read_uint32()
        interest_id = dgi.read_uint16()
        if (context_id, interest_id) in self.interest_callback_map.keys():
            (callback, callback_args, callback_kwargs) = self.interest_callback_map[(interest_id, context_id)]
            del self.interest_callback_map[(interest_id, context_id)]
            callback(*callback_args, **callback_kwargs)
        else:
            # FIXME: How do I report about this if no callback is registered?
            pass

    def handle_CLIENT_OBJECT_SET_FIELD(self, dgi):
        do_id = dgi.read_uint32()
        field_id = dgi.read_uint16()
        # FIXME: There's still the value in the dgi
        # FIXME: Implement
    
    def handle_CLIENT_OBJECT_SET_FIELDS(self, dgi):
        do_id = dgi.read_uint32()
        field_count = dgi.read_uint16()
        # FIXME: There's still <field_count> values in the dgi
        # FIXME: Implement
    
    def handle_CLIENT_OBJECT_LOCATION(self, dgi):
        do_id = dgi.read_uint32()
        parent_id = dgi.read_uint32()
        zone_id = dgi.read_uint32()
        # FIXME: Make DO set changed location
    
    def handle_CLIENT_OBJECT_LEAVING(self, dgi):
        do_id = dgi.read_uint32()
        dist_obj = self.distributed_objects[do_id]
        dist_obj.delete()
        del self.distributed_objects[do_id]
    
    def handle_CLIENT_OBJECT_LEAVING_OWNER(self, dgi):
        do_id = dgi.read_uint32()
        dist_obj = self.owner_views[do_id]
        dist_obj.delete()
        del self.distributed_objects[do_id]
    
    def handle_CLIENT_ENTER_OBJECT_REQUIRED(self, dgi):
        self.create_view_from_datagram(dgi)
    
    def handle_CLIENT_ENTER_OBJECT_REQUIRED_OTHER(self, dgi):
        self.create_view_from_datagram(dgi)
    
    def handle_CLIENT_ENTER_OBJECT_REQUIRED_OWNER(self, dgi):
        self.create_view_from_datagram(dgi, cls_postfix = 'OV')
    
    def handle_CLIENT_ENTER_OBJECT_REQUIRED_OTHER_OWNER(self, dgi):
        self.create_view_from_datagram(dgi, cls_postfix = 'OV')

    def handle_CLIENT_ADD_INTEREST(self, dgi):
        context = dgi.read_uint32()
        interest_id = dgi.read_uint16()
        parent_id = dgi.read_uint32()
        zone_id = dgi.read_uint32()
        print("Client received CLIENT_ADD_INTEREST, context %d, interest id %d for (%d, %d)" % (context, interest_id, parent_id, zone_id))

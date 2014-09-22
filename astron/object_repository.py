# TODO
# * CLIENT_HEARTBEAT =  5

from bamboo import dcfile, module, traits
from bamboo.wire import Datagram, DatagramIterator
from connection import Connection
import client_messages as clientmsg
import internal_messages as servermsg
from distributed_object import DistributedObject
import socket

DATAGRAM_SIZE = 2
DATAGRAM_ENCODING = '<H'

astron_keywords = ['clsend', 'ownsend',
                   'broadcast', 'clrecv', 'ownrecv', 'airecv',
                   'ram', 'required', 'db']
default_host = "127.0.0.1"
default_internal_port = 7199
default_client_port = 6667
default_dcfilename = "astron.dc"


class ObjectRepository(Connection):
    def __init__(self, dcfilename=default_dcfilename):
        Connection.__init__(self)
        self.mod = module.Module()
        # Add Astron-specific keywords
        for word in astron_keywords:
            self.mod.add_keyword(word)
        dcfile.parse_dcfile(self.mod, dcfilename)

        self.handlers = {}
        
        # FIXME: Maybe move this into ClientRepository, if Internals won't get Interests in the future.
        self.interest_counters = {}
        self.interest_callback_map = {}

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
        dgi = DatagramIterator(dg)
        msgtype = dgi.read_uint16()
        if msgtype in self.handlers.keys():
            self.handlers[msgtype](dgi)
        else:
            print("Received unhandled message type " + str(msgtype))

    def create_view(self, dgi, cls_postfix = ''):
        do_id = dgi.read_uint32()
        parent_id = dgi.read_uint32()
        zone_id = dgi.read_uint32()
        dclass_id = dgi.read_uint16()
        # Create the view object
        cls_name = mod.get_class_by_id(dclass_id).get_name() + cls_postfix
        # FIXME: Get the actual class
        cls = DistributedObject
        dist_obj = cls(self, do_id, parent_id, zone_id)
        self.distributed_objects[do_id] = dist_obj
        # FIXME: Read the field values from the dgi and apply them
        dist_obj.init()

    def create_view_directly(self, cls, do_id, parent_id, zone_id):
        cls = DistributedObject
        dist_obj = cls(self, do_id, parent_id, zone_id)
        self.distributed_objects[do_id] = dist_obj
        # FIXME: Read the field values from the dgi and apply them
        dist_obj.init()
        return dist_obj


class InternalRepository(ObjectRepository):
    def __init__(self, version_string, dcfilename=default_dcfilename):
        ObjectRepository.__init__(self, dcfilename=dcfilename)
        self.handlers = {}

    def connect(self, host=default_host, port=default_internal_port):
        ObjectRepository.connect(self, host, port)


class ClientRepository(ObjectRepository):
    def __init__(self, version_string, dcfilename=default_dcfilename):
        ObjectRepository.__init__(self, dcfilename=dcfilename)
        self.version_string = version_string
        self.distributed_objects = {}
        self.owner_views = {}
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
            })

    def connect(self, connection_success, connection_failure, connection_eject,
                host=default_host, port=default_client_port):
        self.connection_success = connection_success
        self.connection_failure = connection_failure
        self.connection_eject = connection_eject

        ObjectRepository.connect(self, host, port)
        # FIXME: send_client_hello needs to be asynchronous.
        self.send_CLIENT_HELLO()

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
        self.send(dg)
        # FIXME: The connection should be closed right now.
        #   What about later reads of cached messages?

    def send_CLIENT_ADD_INTEREST(self,
                                 parent_id, zone_id,
                                 interest_id = 0,
                                 callback = False, callback_args = [], callback_kwargs = {}):
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
        dg.add_uint16(clientmsg.CLIENT_ADD_INTEREST)
        dg.add_uint32(context_id)
        dg.add_uint16(interest_id)
        dg.add_uint32(parent_id)
        dg.add_uint32(zone_id)
        self.send(dg)
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
        self.send(dg)
        if callback != False:
            self.interest_callback_map[(interest_id, context_id)] = (callback, callback_args, callback_kwargs)
        return context_id
    
    def send_CLIENT_REMOVE_INTEREST(self, interest_id, context_id):
        # FIXME: Should something be done about callbacks here?
        dg = Datagram()
        dg.add_uint16(clientmsg.CLIENT_REMOVE_INTEREST)
        dg.add_uint32(context_id)
        dg.add_uint16(interest_id)
        self.send(dg)

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
        self.create_view(dgi)
    
    def handle_CLIENT_ENTER_OBJECT_REQUIRED_OTHER(self, dgi):
        self.create_view(dgi)
    
    def handle_CLIENT_ENTER_OBJECT_REQUIRED_OWNER(self, dgi):
        self.create_view(dgi, cls_postfix = 'OV')
    
    def handle_CLIENT_ENTER_OBJECT_REQUIRED_OTHER_OWNER(self, dgi):
        self.create_view(dgi, cls_postfix = 'OV')












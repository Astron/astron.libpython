# TODO: Split DistributedObject into ClientObject and InternalObject

from bamboo import module
from bamboo.wire import Datagram
from pprint import pprint
import client_messages as clientmsg
import internal_messages as servermsg
from astron.object_repository import MSG_TYPE_CLIENT, MSG_TYPE_INTERNAL
from astron.helpers import separate_fields

class DistributedObject:
    def __init__(self, repository, class_id, do_id, parent_id, zone_id):
        self.repo = repository
        self.class_ = self.repo.mod.get_class(class_id)
        self.do_id = do_id
        self.parent = parent_id
        self.zone = zone_id

        # FIXME: This lumps all non-required field into the other_fields bin
        #        but it should only lump "ram" fields into that bin.
        self.required_fields, self.other_fields = separate_fields(self.dclass, ["required"])

        # FIXME: Remove after debug
        print("Initing %s %d" % (self.dclass.name(), self.do_id))
        print("  REQUIRED fields: %s" % (" ".join([str(idx) for idx in self.required_fields]), ))
        print("  OTHER fields: %s" % (" ".join([str(idx) for idx in self.other_fields]), ))

    # Creating and destroying the view.

    def init(self):
        """Overwrite this to execute code right after view creation."""
        print("DO created without custom init(): %d (%s)" % (self.do_id, str(type(self))))

    def delete(self):
        """Overwrite this to execute code just before a views deletion."""
        # FIXME: Redup in object_repository if the docstring is actually accurate.
        print("DO deleted: %d" % (self.do_id, ))

    def acquire_ai(self):
        # FIXME: This should have more intelligence, i.e. using GET_AI (CHANGE_AI?)
        self.repo.send_STATESERVER_OBJECT_SET_AI(self.do_id)

    def recv_update(self, field_id, dgi):
        """Handles incoming SET_FIELD updates for Client Repository."""
        field = self.dclass.get_field_by_id(field_id)
        print("Receiving update for field %s in %d with args %s" % (field.name(), self.do_id, str(args)))

        args = dgi.read_value(field.type())
        getattr(self, field.name())(args)

    def recv_update_internal(self, sender, field_id, dgi):
        """Handles incoming SET_FIELD updates for Internal Repository."""
        field = self.dclass.get_field_by_id(field_id)
        print("Receiving update for field %s in %d with args %s" % (field.name(), self.do_id, str(args)))

        args = dgi.read_value(field.type())
        getattr(self, field.name())(sender, args)

    def send_update(self, field_name, *args):
        """Handles outgoing SET_FIELD updates for Client Repository."""
        field = self.dclass.get_field_by_name(field_name)
        print("Sending update for field %s, dmethod_id %d" % (field_name, dmethod_id))

        dg = self.repo.create_message_stub()
        dg.add_uint16(clientmsg.CLIENT_OBJECT_SET_FIELD)
        dg.add_uint32(self.do_id)
        dg.add_uint16(field.id())
        dg.add_value(arg.type(), args)
        self.repo.send_datagram(dg)

    def send_update_internal(self, recipients, field_name, *args):
        """Handles outgoing SET_FIELD updates for Internal Repository."""
        field = self.dclass.get_field_by_name(field_name)
        print("Sending update for field %s, dmethod_id %d" % (field_name, dmethod_id))

        dg = self.repo.create_message_stub(self.do_id, recipients)
        dg.add_uint16(servermsg.STATESERVER_OBJECT_SET_FIELD)
        dg.add_uint32(self.do_id)
        dg.add_uint16(field.id())
        dg.add_value(arg.type(), args)
        self.repo.send_datagram(dg)

    # Sending

    def send_CLIENTAGENT_EJECT(self, client_id, disconnect_code, reason):
        dg = self.repo.create_message_stub(self.do_id, client_id)
        dg.add_uint16(servermsg.CLIENTAGENT_EJECT)
        dg.add_uint16(disconnect_code)
        dg.add_string(reason)
        self.repo.send_datagram(dg)

    def send_CLIENTAGENT_DROP(self, client_id):
        dg = self.repo.create_message_stub(self.do_id, client_id)
        dg.add_uint16(servermsg.CLIENTAGENT_DROP)
        self.repo.send_datagram(dg)

    # Handle
    def handle_STATESERVER_OBJECT_CHANGING_LOCATION(self, sender, do_id, new_parent, new_zone, old_parent, old_zone):
        """Override this to react to STATESERVER_OBJECT_CHANGING_LOCATION messages."""
        pass

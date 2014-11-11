# TODO: Split DistributedObject into ClientObject and InternalObject 

from bamboo import module
from bamboo.wire import Datagram
from pprint import pprint
import client_messages as clientmsg
import internal_messages as servermsg
from astron.object_repository import MSG_TYPE_CLIENT, MSG_TYPE_INTERNAL
from astron.helpers import separate_fields

class DistributedObject:
    def __init__(self, repository, dclass_id, do_id, parent_id, zone_id):
        self.repo = repository
        self.dclass_id = dclass_id
        self.dclass = self.repo.mod.get_class(dclass_id)
        self.dmethod_name_to_id = dict([(self.dclass.get_field(dmethod_id).name(), dmethod_id)
                                        for dmethod_id in range(0, self.dclass.num_fields())])
        self.dmethod_id_to_name = dict([(dmethod_id, self.dclass.get_field(dmethod_id).name())
                                        for dmethod_id in range(0, self.dclass.num_fields())])
        self.field_id_to_dmethod_id = dict([(self.dclass.get_field(dmethod_id).id(), dmethod_id)
                                            for dmethod_id in range(0, self.dclass.num_fields())])
        self.do_id = do_id
        self.parent = parent_id
        self.zone = zone_id
        self.type_packer = {module.kTypeInt8: self.pack_int8,
                            module.kTypeInt16: self.pack_int16,
                            module.kTypeInt32: self.pack_int32,
                            module.kTypeInt64: self.pack_int64,
                            module.kTypeUint8: self.pack_uint8,
                            module.kTypeUint16: self.pack_uint16,
                            module.kTypeUint32: self.pack_uint32,
                            module.kTypeUint64: self.pack_uint64,
                            module.kTypeFloat32: self.pack_float32,
                            module.kTypeFloat64: self.pack_float64,
                            module.kTypeChar: self.pack_char,
                            module.kTypeString: self.pack_string,
                            module.kTypeVarstring: self.pack_string,
                            }
        self.type_unpacker = {module.kTypeInt8: self.unpack_int8,
                              module.kTypeInt16: self.unpack_int16,
                              module.kTypeInt32: self.unpack_int32,
                              module.kTypeInt64: self.unpack_int64,
                              module.kTypeUint8: self.unpack_uint8,
                              module.kTypeUint16: self.unpack_uint16,
                              module.kTypeUint32: self.unpack_uint32,
                              module.kTypeUint64: self.unpack_uint64,
                              module.kTypeFloat32: self.unpack_float32,
                              module.kTypeFloat64: self.unpack_float64,
                              module.kTypeChar: self.unpack_char,
                              module.kTypeString: self.unpack_string,
                              module.kTypeVarstring: self.unpack_string,
                            }
        self.required_fields, self.other_fields = separate_fields(self.dclass, ["required"])
        # FIXME: Remove after debug
        #print("Initing %s %d" % (self.dclass.name(), self.do_id))
        #print("  REQUIRED fields: %s" % (" ".join([str(idx) for idx in self.required_fields]), ))
        #print("  OTHER fields: %s" % (" ".join([str(idx) for idx in self.other_fields]), ))
    
    # Creating and destroying the view.
    
    def init(self):
        """Overwrite this to execute code right after view creation."""
        print("DO created without custom init(): %d (%s)" % (self.do_id, str(type(self))))
    
    def delete(self):
        """Overwrite this to execute code just before a views deletion."""
        # FIXME: Redup in object_repository if the docstring is actually accurate. 
        print("DO deleted: %d" % (self.do_id, ))

    def update_field(self, sender, field_id, dgi):
        """Handles incoming SET_FIELD updates."""
        decoded_args = []
        field = self.dclass.get_field(self.field_id_to_dmethod_id[field_id])
        num_args = field.type().as_method().num_parameters()
        for arg_id in range(0, num_args):
            arg = field.type().as_method().get_parameter(arg_id)
            arg_type = arg.type().subtype()
            if arg_type == module.kTypeStruct:
                decoded_args.append(self.unpack_struct(dgi, arg.type().as_struct()))
            else:
                decoded_args.append(self.type_unpacker[arg_type](dgi))
        # print("Updating field %s in %d with args %s" % (field.name(), self.do_id, str(decoded_args)))
        getattr(self, field.name())(sender, *decoded_args)

    def send_update(self, field_name, *values):
        """Handles outgoing SET_FIELD updates."""
        dmethod_id = self.dmethod_name_to_id[field_name]
        # print("  send_update to field %s, dmethod_id %d" % (field_name, dmethod_id))
        field = self.dclass.get_field(dmethod_id)
        num_args = field.type().as_method().num_parameters()
        if num_args != len(values):
            print("Distributed method %s requires %d args, %d were provided" % (field_name, num_args, len(values)))
        else:
            if self.repo.msg_type == MSG_TYPE_CLIENT:
                dg = self.repo.create_message_stub()
                dg.add_int16(clientmsg.CLIENT_OBJECT_SET_FIELD)
            else:
                # FIXME: If this an AIR object, recipients and sender have to be provided here.
                dg = self.repo.create_message_stub(self.do_id, self.do_id)
                dg.add_int16(servermsg.STATESERVER_OBJECT_SET_FIELD)
            dg.add_int32(self.do_id)
            dg.add_int16(field.id())
            for arg_id in range(0, num_args):
                arg = field.type().as_method().get_parameter(arg_id)
                arg_type = arg.type().subtype()
                if arg_type == module.kTypeStruct:
                    self.pack_struct(dg, arg. type().as_struct(), *values[arg_id])
                else:
                    self.type_packer[arg_type](dg, values[arg_id])
            self.repo.send_datagram(dg)

    # Packing and unpacking field data.

    def pack_struct(self, dg, struct, *values):
        num_args = struct.num_fields()
        if num_args != len(values):
            print("Struct %s requires %d args, %d were provided" % (struct.name(), num_args, len(values)))
        else:
            for arg_id in range(0, num_args):
                arg = struct.get_field(arg_id)
                arg_type = arg.type().subtype()
                if arg_type == module.kTypeStruct:
                    self.pack_struct(dg, arg.type().as_struct(), *values[arg_id])
                else:
                    self.type_packer[arg_type](dg, values[arg_id])

    def unpack_struct(self, dgi, struct):
        partial_args = []
        num_args = struct.num_fields()
        for arg_id in range(0, num_args):
            arg = struct.get_field(arg_id)
            arg_type = arg.type().subtype()
            if arg_type == module.kTypeStruct:
                partial_args.append(self.unpack_struct(dgi, arg.type().as_struct()))
            else:
                partial_args.append(self.type_unpacker[arg_type](dgi))
        return partial_args

    def pack_int8(self, dg, value):
        dg.add_int8(value)

    def pack_int16(self, dg, value):
        dg.add_int16(value)

    def pack_int32(self, dg, value):
        dg.add_int32(value)

    def pack_int64(self, dg, value):
        dg.add_int64(value)

    def pack_uint8(self, dg, value):
        dg.add_uint8(value)

    def pack_uint16(self, dg, value):
        dg.add_uint16(value)

    def pack_uint32(self, dg, value):
        dg.add_uint32(value)

    def pack_uint64(self, dg, value):
        dg.add_uint64(value)

    def pack_float32(self, dg, value):
        dg.add_float32(value)

    def pack_float64(self, dg, value):
        dg.add_float64(value)

    def pack_char(self, dg, value):
        dg.add_char(value)

    def pack_string(self, dg, value):
        dg.add_string(value)

    def unpack_int8(self, dgi):
        return dgi.read_int8()

    def unpack_int16(self, dgi):
        return dgi.read_int16()

    def unpack_int32(self, dgi):
        return dgi.read_int32()

    def unpack_int64(self, dgi):
        return dgi.read_int64()

    def unpack_uint8(self, dgi):
        return dgi.read_uint8()

    def unpack_uint16(self, dgi):
        return dgi.read_uint16()

    def unpack_uint32(self, dgi):
        return dgi.read_uint32()

    def unpack_uint64(self, dgi):
        return dgi.read_uint64()

    def unpack_float32(self, dgi):
        return dgi.read_float32()

    def unpack_float64(self, dgi):
        return dgi.read_float64()

    def unpack_char(self, dgi):
        return dgi.read_char()

    def unpack_string(self, dgi):
        return dgi.read_string()

    # Server-side things

    def acquire_ai(self):
        # FIXME: This should have more intelligence, i.e. using GET_AI (CHANGE_AI?)
        self.repo.send_STATESERVER_OBJECT_SET_AI(self.do_id)
    
    def add_ai_interest(self, distobj_id, zone_id):
        self.repo.add_ai_interest(distobj_id, zone_id, by_distobj = self.do_id)
    
    def remove_ai_interest(self, distobj_id, zone_id):
        self.repo.remove_ai_interest(distobj_id, zone_id, by_distobj = self.do_id)

    def interest_distobj_enter(self, view, do_id, parent_id, zone_id):
        """Overwrite this to be notified of new distributed objects
        entering a location that this object is interested in."""
        print("WARNING: Un-overwritten interest_distobj_enter called in %d" % (self.do_id, ))

    def interest_distobj_ai_enter(self, view, do_id, parent_id, zone_id):
        """Overwrite this to be notified of new AI distributed objects
        entering a location that this object is interested in."""
        print("WARNING: Un-overwritten interest_distobj_ai_enter called in %d" % (self.do_id, ))

    def interest_changing_location_enter(self, sender, do_id, new_parent, new_zone, old_parent, old_zone):
        print("WARNING: Un-overwritten interest_changing_location_enter called in %d" % (self.do_id, ))
    
    def interest_changing_location_leave(self, sender, do_id, new_parent, new_zone, old_parent, old_zone):
        print("WARNING: Un-overwritten interest_changing_location_leave called in %d" % (self.do_id, ))

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

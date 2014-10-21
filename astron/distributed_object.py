from bamboo import module
from bamboo.wire import Datagram
from pprint import pprint
from astron.client_messages import CLIENT_OBJECT_SET_FIELD

class DistributedObject:
    def __init__(self, repository, dclass_id, do_id, parent_id, zone_id):
        self.repo = repository
        self.dclass_id = dclass_id
        self.dclass = self.repo.mod.get_class(dclass_id)
        self.dmethod_name_to_id = dict([(self.dclass.get_field(dmethod_id).name(), dmethod_id)
                                        for dmethod_id in range(0, self.dclass.num_fields())])
        self.do_id = do_id
        self.parent = parent_id
        self.zone = zone_id
        self.type_packer = {module.kTypeInt8: self.pack_int8,
                            module.kTypeInt16: self.pack_int16,
                            module.kTypeInt32: self.pack_int32,
                            module.kTypeInt64: self.pack_int64,
                            module.kTypeFloat32: self.pack_float32,
                            module.kTypeFloat64: self.pack_float64,
                            module.kTypeChar: self.pack_char,
                            module.kTypeString: self.pack_string,
                            module.kTypeVarstring: self.pack_string,
                            }
        # FIXME: Remove after debugging
        #pprint(self.type_packer)
    
    def init(self):
        print("DO created: %d (%s)" % (self.do_id, str(type(self))))
    
    def delete(self):
        print("DO deleted: %d" % (self.do_id, ))

    def call_dist_method(self, name, *args):
        pass
    
    def send_update(self, field_name, *values):
        dmethod_id = self.dmethod_name_to_id[field_name]
        field = self.dclass.get_field(dmethod_id)
        num_args = field.type().as_method().num_parameters()
        if num_args != len(values):
            print("Distributed method %s requires %d args, %d were provided" % (field_name, num_args, len(values)))
        else:
            dg = Datagram()
            dg.add_int16(CLIENT_OBJECT_SET_FIELD)
            dg.add_int32(self.do_id)
            dg.add_int16(dmethod_id)
            for arg_id in range(0, num_args):
                arg = field.type().as_method().get_parameter(arg_id)
                arg_type = arg.type().subtype()
                if arg_type == module.kTypeStruct:
                    self.pack_struct(dg, arg.type().as_struct(), *values[arg_id])
                else:
                    self.type_packer[arg_type](dg, values[arg_id])
            self.repo.send_datagram(dg)

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

    def pack_int8(self, dg, value):
        dg.add_uint8(value)

    def pack_int16(self, dg, value):
        dg.add_uint16(value)

    def pack_int32(self, dg, value):
        dg.add_uint32(value)

    def pack_int64(self, dg, value):
        dg.add_uint64(value)

    def pack_float32(self, dg, value):
        dg.add_float32(value)

    def pack_float64(self, dg, value):
        dg.add_float64(value)

    def pack_char(self, dg, value):
        dg.add_char(value)

    def pack_string(self, dg, value):
        dg.add_string(value)

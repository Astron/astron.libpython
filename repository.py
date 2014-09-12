#!/usr/bin/env python

import socket, struct
from bamboo import dcfile, module, traits, wire
import MsgTypes as msgtype

DATAGRAM_SIZE = 2
DATAGRAM_ENCODING = '<H'

astron_keywords = ['clsend', 'ownsend',
                   'broadcast', 'clrecv', 'ownrecv', 'airecv',
                   'ram', 'required', 'db']
default_host = "127.0.0.1"
default_internal_port = 7199
default_client_port = 6667
default_dcfilename = "astron.dc"

class AstronBaseRepository:
    def __init__(self, dcfilename = default_dcfilename):
        self.mod = module.Module()
        # Add Astron keyworks
        for word in astron_keywords:
            self.mod.add_keyword(word)
        dcfile.parse_dcfile(self.mod, dcfilename)
        self.reading_message = False
        self.message_length = 0
        self.handlers = {}
        self.connection_active = False
        
    def connect(self, host, port, connect_nonblocking = False):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # FIXME: Maybe blocking itself should be non-blocking, too???
        if connect_nonblocking:
            self.conn.setblocking(0)
            self.conn.connect((host, port))
        else:
            self.conn.connect((host, port))
            self.conn.setblocking(0)
        self.connection_active = True
    
    def destroy(self):
        self.conn.close()
    
    # Sending messages
    
    def send(self, datagram):
        msg = struct.pack('<H', len(datagram)) + datagram.data()
        self.conn.send(msg)
    
    def tick(self):
        """Process all completely received messages. Returns True
        after that, False if the connection is inactive or has
        broken."""
        if self.connection_active:
            done = False
            while not done:
                try:
                    if not self.reading_message:
                        # Read the length of the next message
                        length = self.conn.recv(DATAGRAM_SIZE)
                        if len(length) == 0: # FIXME: Could also contain partial data
                            # Connection has been terminated
                            self.connection_active = False
                            # Breaking out of the loop *and* informing the app that
                            # the connection is gone.
                            # FIXME: Add optional callback
                            return False
                        else:
                            self.reading_message = True
                            self.message_length = struct.unpack('<H', length)[0]
                    else:
                        # Read a message
                        # FIXME: As above, the connection might have been broken.
                        msg = self.conn.recv(self.message_length)
                        self.reading_message = False
                        self.handle_message(msg)
                except socket.error:
                    # Connection is (too) empty to proceed
                    done = True
            # We're finished reading for now, but the connection is still active.
            return True
        else:
            # Currently the connection isn't active.
            return False

    def handle_message(self, msg):
        dg = wire.Datagram()
        dg.add_data(msg)
        dgi = wire.DatagramIterator(dg)
        msg_type = dgi.read_uint16()
        if msg_type in self.handlers.keys():
            self.handlers[msg_type](dgi)
        else:
            print("Received unhandled message type "+str(msg_type))

class AstronInternalRepository(AstronBaseRepository):
    def __init__(self, version_string, dcfilename = default_dcfilename):
        AstronBaseRepository.__init__(self, dcfilename = dcfilename)
        self.handlers = {}

    def connect(self, host = default_host, port = default_internal_port):
        AstronBaseRepository.connect(self, host, port)
        self.handlers = {}

class AstronClientRepository(AstronBaseRepository):
    def __init__(self, version_string, dcfilename = default_dcfilename):
        AstronBaseRepository.__init__(self, dcfilename = dcfilename)
        self.version_string = version_string
        self.handlers.update({msgtype.CLIENT_HELLO_RESP: self.handle_CLIENT_HELLO_RESP,
                              msgtype.CLIENT_EJECT     : self.handle_CLIENT_EJECT})
        
    def connect(self, connection_success, connection_failure, connection_eject,
                host = default_host, port = default_client_port):
        self.connection_success = connection_success
        self.connection_failure = connection_failure
        self.connection_eject = connection_eject
        # FIXME: This needs to be unblocking, and the send_client_hello needs to be asynchronous.
        # Using connect_nonblocking = True isn't properly implemented yet, though.
        AstronBaseRepository.connect(self, host, port, connect_nonblocking = False)
        # Send CLIENT_HELLO
        self.send_CLIENT_HELLO()

    # Sending messages
    
    def send_CLIENT_HELLO(self):
        dg = wire.Datagram()
        dg.add_uint16(1)                            # CLIENT_HELLO
        dg.add_uint32(traits.legacy_hash(self.mod)) # dc hash
        dg.add_string(self.version_string)          # version string
        self.send(dg)
    
    # Receive messages
    
    def handle_CLIENT_HELLO_RESP(self, dgi):
        self.connection_success()
    
    def handle_CLIENT_EJECT(self, dgi):
        error_code = dgi.read_uint16()
        reason = dgi.read_string()
        self.connection_eject(error_code, reason)

if __name__ == '__main__':
    import time
    repo = AstronClientRepository("SimpleExample v0.2", "simple_example.dc")
    def connected():
        print("Connection established.")
    def ejected(error_code, reason):
        print("Got ejected (%i): %s" % (error_code, reason))
    def failed():
        print("Connection attempt failed.")
    repo.connect(connected, failed, ejected)
    while repo.tick():
        time.sleep(0.5)

## Lets do some random things
#print mod.get_num_classes() # or GetNumClasses
#cls = mod.get_class_by_name('Foobar')  # or getClassByName
#print cls.get_name() # -> "Foobar"

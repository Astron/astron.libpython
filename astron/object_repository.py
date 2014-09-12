from bamboo import dcfile, module, traits
from bamboo.wire import DatagramIterator
from connection import Connection
import client_messages as clientmsg
import internal_messages as servermsg


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
        self.mod = module.Module()
        # Add Astron-specific keywords
        for word in astron_keywords:
            self.mod.add_keyword(word)
        dcfile.parse_dcfile(self.mod, dcfilename)

        self.handlers = {}

    def poll_till_empty(self):
        """Process all received messages.

        Return False if the connection has ended or is broken.
        """

        if self.is_connected():
            try:
                dg = self.poll_datagram()
                while dg is not None:
                    self._handle_datagram(dg)

            except socket.error:
                return False

            # We're finished reading for now,
            # but the connection is still active.
            return True
        else:
            # Currently the connection isn't active.
            return False

    def poll_forever(self):
        """Block forever and receive datagrams as they come in."""
        try:
            dg = self.recv_datagram()
            while dg is not None:
                self._handle_datagram(dg)
        except socket.error:
            return

    def _handle_datagram(self, dg):
        dgi = DatagramIterator(dg)
        msgtype = dgi.read_uint16()
        if msgtype in self.handlers.keys():
            self.handlers[msg_type](dgi)
        else:
            print("Received unhandled message type " + str(msgtype))


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
        self.handlers.update({
            clientmsg.CLIENT_HELLO_RESP: self.handle_CLIENT_HELLO_RESP,
            clientmsg.CLIENT_EJECT:      self.handle_CLIENT_EJECT})

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
        dg = wire.Datagram()
        dg.add_uint16(clientmsg.CLIENT_HELLO)
        dg.add_uint32(traits.legacy_hash(self.mod))
        dg.add_string(self.version_string)
        self.send(dg)

    # Receive messages

    def handle_CLIENT_HELLO_RESP(self, dgi):
        self.connection_success()

    def handle_CLIENT_EJECT(self, dgi):
        error_code = dgi.read_uint16()
        reason = dgi.read_string()
        self.connection_eject(error_code, reason)

import errno
import struct
import socket
from bamboo.wire import Datagram

DATAGRAM_HEADER_SIZE = 2

class Connection:
    def __init__(self):
        self._is_connected = False

    # FIXME: Make connect() non-blocking and timing out elegantly
    def connect(self, host='127.0.0.1', port=7199, connect_timeout=None):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(connect_timeout)
        # FIXME: Handle this!
        # socket.error: [Errno 111] Connection refused
        self.socket.connect((host, port))
        self.socket.setblocking(0)
        self._is_connected = True
        self.reading_message = False
        self.remaining_length = DATAGRAM_HEADER_SIZE
        self.partial_data = ''

    def disconnect(self):
        self.socket.close()
        self.is_connected = False

    def is_connected(self):
        return self.is_connected

    def send_datagram(self, datagram):
        msg = struct.pack('<H', len(datagram)) + datagram.data()
        self.socket.send(msg)

    def poll_datagram(self):
        """Reads a datagram from the socket and returns it. If a
        datagram can't be read completely, it's readable data will
        be cached and None will be returned. If the connection has
        been closed, EOFError will be raised."""
        self.read()
        # Did we just finish reading the message length?
        if (not self.reading_message) and (self.remaining_length == 0):
            length = struct.unpack('<H', self.partial_data)[0]
            self.partial_data = ''
            self.remaining_length = length
            self.reading_message = True
            self.read()
        # If either the initial read or the read at the end of the
        # block above finished reading a message body, then this
        # happens:
        if self.reading_message and (self.remaining_length == 0):
            dg = Datagram()
            dg.add_data(self.partial_data)
            self.partial_data = ''
            self.remaining_length = DATAGRAM_HEADER_SIZE
            self.reading_message = False
            return dg
        # So we did not actually finish reading a message at all. :(
        return

    def read(self):
        try:
            data = self.socket.recv(self.remaining_length)
            # Has the connection been closed?
            if len(data) == 0:
                raise EOFError('no data received')
            self.partial_data += data
            self.remaining_length -= len(data) # FIXME: Why does this work without /2?
        except socket.error:
            # This is the one error that is not a problem at all,
            # just an empty connection.
            return

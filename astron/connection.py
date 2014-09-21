import errno
import struct
import socket
from bamboo.wire import Datagram


class Connection:
    def __init__(self):
        self._is_connected = False

    def connect(self, host='127.0.0.1', port=7199, connect_timeout=None):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(connect_timeout)
        self.socket.connect((host, port))
        self.socket.settimeout(None)
        self._is_connected = True

    def disconnect(self):
        self.socket.close()

    def is_connected(self):
        return self.is_connected

    def send_datagram(self, datagram):
        msg = struct.pack('<H', len(datagram)) + datagram.data()
        self.conn.send(msg)

    def recv_datagram(self):
        """Wait for the next datagram and return it."""
        length = struct.unpack('<H', self._read(2))
        data = self._read(length)
        dg = Datagram()
        dg.add_data(data)
        return dg

    def poll_datagram(self):
        self.socket.setblocking(0)
        try:
            length = struct.unpack('<H', self._read(2))
        except socket.error as err:
            if err.errno is errno.EWOULDBLOCK:
                return None
            else:
                raise err

        self.socket.setblocking(1)
        data = self._read(length)
        dg = Datagram()
        dg.add_data(data)
        return dg


        "Receive a datagram if immediately available, otherwise return None."
        raise NotImplementedError

    def _read(self, length):
        result = ''
        while len(result) < length:
            data = self.socket.recv(length - len(result))
            if len(data) is 0:
                raise EOFError('no data received')
            result += data
        return result

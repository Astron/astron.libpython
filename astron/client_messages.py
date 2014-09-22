# This file defines messages used by the Astron "Client Protocol"
# See https://astron.github.io/astron/en/master/10-client.html.

CLIENT_HELLO =      1 # Sent to handshake the protocol
CLIENT_HELLO_RESP = 2 # 
CLIENT_DISCONNECT = 3 # Sent when client is leaving.
CLIENT_EJECT =      4 # Received when server is booting the client.
CLIENT_HEARTBEAT =  5

CLIENT_OBJECT_SET_FIELD =     120 # Sent and received when a DO field is updated
CLIENT_OBJECT_SET_FIELDS =    121 # Sent and received when multiple DO fields are updated
CLIENT_OBJECT_LOCATION =      140 # Received when DO changes location within clients interests
CLIENT_OBJECT_LEAVING =       132 # Received when DO leaves clients interests
CLIENT_OBJECT_LEAVING_OWNER = 161 # Received when client loses ownership of a DO

CLIENT_ENTER_OBJECT_REQUIRED =             142 # Received when a DO enters the clients interest visibility.
CLIENT_ENTER_OBJECT_REQUIRED_OTHER =       143 # As above; DO has optional fields.
CLIENT_ENTER_OBJECT_REQUIRED_OWNER =       172 # Received when the client gets ownership of a DO.
CLIENT_ENTER_OBJECT_REQUIRED_OTHER_OWNER = 173 # As above; DO has optional fields.

CLIENT_ADD_INTEREST =          200 # Sent to set interest in a location
CLIENT_ADD_INTEREST_MULTIPLE = 201 # Sent to set interest in multiple locations
CLIENT_REMOVE_INTEREST =       203 # Sent to remove interest in a location
CLIENT_DONE_INTEREST_RESP =    204 # Received when setting an interest in a location has been set and all relevant DOs have entered 

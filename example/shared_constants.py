from astron.helpers import parent_zone_to_location

VERSION_STRING = 'SimpleExample v0.2'
DC_FILE = 'example.dc'
SERVER_FRAMERATE = 120.0

# Channels
# 1,000 - 9,999: Roles
STATESERVER = 1000
DBSS = 1001

# 10,000 - 19,999: Internal Repositories
SERVICES_CHANNEL = 10000

# 20,000 - 99,999: Fixed-ID Distributed Objects in StateServer
POINT_OF_CONTACT_DO_ID = 20000

GAME_ROOT_DO_ID = 30000
GAME_ROOT_PARENT = 0
GAME_ROOT_ZONE = 0
LOGIN_SERVICE_ZONE = 0
WORLD_ZONE = 1
AI_SERVICES_ZONE = 2

# 100,000- 999,999: Clients

# 100,000 - 4294967295: Distributed Objects in DBSS

from astron.helpers import parent_zone_to_location

# 1,000 - 9,999: Roles
COMMON_STATESERVER = 1000
COMMON_DBSS = 1001

# 10,000 - 19,999: Internal Repositories
SERVICES = 10000
WORLD = 10001

# 20,000 - 99,999: Fixed-ID Distributed Objects in StateServer
LOGIN_MANAGER_DO_ID = 20000
# The increasingly inaccurately named MapRoot is the representative
# Distributed Object for the repository that AIs for player
# characters.
# FIXME: These need more flexible assignment, so that several
# InternalRepos can share a pool of DO IDs. 
MAP_ROOT_DO_ID = 21000
MAP_ROOT_PARENT = LOGIN_MANAGER_DO_ID 
MAP_ROOT_ZONE = 0
MAP_ROOT_LOCATION = parent_zone_to_location(MAP_ROOT_PARENT, MAP_ROOT_ZONE)

# 100,000- 999,999:Clients

# 100,000 - 4294967295: Distributed Objects in DBSS
AVATARS_PARENT = LOGIN_MANAGER_DO_ID
AVATARS_ZONE = 1
AVATARS_LOCATION = parent_zone_to_location(LOGIN_MANAGER_DO_ID, AVATARS_ZONE)

# This file defines messages used by the Astron "Internal Protocol"

# MessageDirector / Control Messages
# https://astron.github.io/astron/en/master/19-messagedirector.html
CONTROL_CHANNEL =                                   1
CONTROL_ADD_CHANNEL =                               9000
CONTROL_REMOVE_CHANNEL =                            9001
CONTROL_ADD_RANGE =                                 9002
CONTROL_REMOVE_RANGE =                              9003
CONTROL_ADD_POST_REMOVE =                           9010
CONTROL_CLEAR_POST_REMOVES =                        9011


# StateServer Messages
# https://astron.github.io/astron/en/master/12-stateserver.html

# StateServer Control
STATESERVER_CREATE_OBJECT_WITH_REQUIRED =           2000 # -> SS. Create object in SS. it'll then broadcast ENTER_LOCATION
STATESERVER_CREATE_OBJECT_WITH_REQUIRED_OTHER =     2001 # -> SS. Create object in SS. it'll then broadcast ENTER_LOCATION

# Distributed Object Control
STATESERVER_DELETE_AI_OBJECTS =                     2009 # -> SS. Delete all DOs associated with this AI.
STATESERVER_OBJECT_GET_FIELD =                      2010 # -> DO. Request value of field. 
STATESERVER_OBJECT_GET_FIELD_RESP =                 2011 # <- DO. Inform of value of field.
STATESERVER_OBJECT_GET_FIELDS =                     2012
STATESERVER_OBJECT_GET_FIELDS_RESP =                2013
STATESERVER_OBJECT_GET_ALL =                        2014
STATESERVER_OBJECT_GET_ALL_RESP =                   2015
STATESERVER_OBJECT_SET_FIELD =                      2020
STATESERVER_OBJECT_SET_FIELDS =                     2021
STATESERVER_OBJECT_DELETE_FIELD_RAM =               2030
STATESERVER_OBJECT_DELETE_FIELDS_RAM =              2031
STATESERVER_OBJECT_DELETE_RAM =                     2032

# Distributed Object Visibility
STATESERVER_OBJECT_SET_LOCATION =                           2040
STATESERVER_OBJECT_CHANGING_LOCATION =                      2041
STATESERVER_OBJECT_ENTER_LOCATION_WITH_REQUIRED =           2042
STATESERVER_OBJECT_ENTER_LOCATION_WITH_REQUIRED_OTHER =     2043
STATESERVER_OBJECT_GET_LOCATION =                           2044
STATESERVER_OBJECT_GET_LOCATION_RESP =                      2045
STATESERVER_OBJECT_SET_AI =                                 2050
STATESERVER_OBJECT_CHANGING_AI =                            2051
STATESERVER_OBJECT_ENTER_AI_WITH_REQUIRED =                 2052
STATESERVER_OBJECT_ENTER_AI_WITH_REQUIRED_OTHER =           2053
STATESERVER_OBJECT_GET_AI =                                 2054
STATESERVER_OBJECT_GET_AI_RESP =                            2055
STATESERVER_OBJECT_SET_OWNER =                              2060
STATESERVER_OBJECT_CHANGING_OWNER =                         2061
STATESERVER_OBJECT_ENTER_OWNER_WITH_REQUIRED =              2062
STATESERVER_OBJECT_ENTER_OWNER_WITH_REQUIRED_OTHER =        2063
STATESERVER_OBJECT_GET_OWNER =                              2064
STATESERVER_OBJECT_GET_OWNER_RESP =                         2065

# Parent Object Queries
STATESERVER_OBJECT_GET_ZONE_OBJECTS =               2100
STATESERVER_OBJECT_GET_ZONES_OBJECTS =              2102
STATESERVER_OBJECT_GET_CHILDREN =                   2104
STATESERVER_OBJECT_GET_ZONE_COUNT =                 2110
STATESERVER_OBJECT_GET_ZONE_COUNT_RESP =            2111
STATESERVER_OBJECT_GET_ZONES_COUNT =                2112
STATESERVER_OBJECT_GET_ZONES_COUNT_RESP =           2113
STATESERVER_OBJECT_GET_CHILD_COUNT =                2114
STATESERVER_OBJECT_GET_CHILD_COUNT_RESP =           2115
STATESERVER_OBJECT_DELETE_ZONE =                    2120
STATESERVER_OBJECT_DELETE_ZONES =                   2122
STATESERVER_OBJECT_DELETE_CHILDREN =                2124

# DBSS-Backed Object Control
DBSS_OBJECT_ACTIVATE_WITH_DEFAULTS =         2200
DBSS_OBJECT_ACTIVATE_WITH_DEFAULTS_OTHER =   2201
DBSS_OBJECT_GET_ACTIVATED =                  2207
DBSS_OBJECT_GET_ACTIVATED_RESP =             2208
DBSS_OBJECT_DELETE_FIELD_DISK =              2230
DBSS_OBJECT_DELETE_FIELDS_DISK =             2231
DBSS_OBJECT_DELETE_DISK =                    2232


# Database Server Messages
# https://astron.github.io/astron/en/master/13-dbserver.html
DBSERVER_CREATE_OBJECT =                        3000
DBSERVER_CREATE_OBJECT_RESP =                   3001
DBSERVER_OBJECT_GET_FIELD =                     3010
DBSERVER_OBJECT_GET_FIELD_RESP =                3011
DBSERVER_OBJECT_GET_FIELDS =                    3012
DBSERVER_OBJECT_GET_FIELDS_RESP =               3013
DBSERVER_OBJECT_GET_ALL =                       3014
DBSERVER_OBJECT_GET_ALL_RESP =                  3015
DBSERVER_OBJECT_SET_FIELD =                     3020
DBSERVER_OBJECT_SET_FIELDS =                    3021
DBSERVER_OBJECT_SET_FIELD_IF_EQUALS =           3022
DBSERVER_OBJECT_SET_FIELD_IF_EQUALS_RESP =      3023
DBSERVER_OBJECT_SET_FIELDS_IF_EQUALS =          3024
DBSERVER_OBJECT_SET_FIELDS_IF_EQUALS_RESP =     3025
DBSERVER_OBJECT_SET_FIELD_IF_EMPTY =            3026
DBSERVER_OBJECT_SET_FIELD_IF_EMPTY_RESP =       3027
DBSERVER_OBJECT_DELETE_FIELD =                  3030
DBSERVER_OBJECT_DELETE_FIELDS =                 3031
DBSERVER_OBJECT_DELETE =                        3032

# ClientAgent Messages
# https://astron.github.io/astron/en/master/11-clientagent.html
CLIENTAGENT_SET_STATE =                         1000
CLIENTAGENT_SET_CLIENT_ID =                     1001
CLIENTAGENT_SEND_DATAGRAM =                     1002
CLIENTAGENT_EJECT =                             1004
CLIENTAGENT_DROP =                              1005
CLIENTAGENT_DECLARE_OBJECT =                    1010
CLIENTAGENT_UNDECLARE_OBJECT =                  1011
CLIENTAGENT_ADD_SESSION_OBJECT =                1012
CLIENTAGENT_REMOVE_SESSION_OBJECT =             1013
CLIENTAGENT_SET_FIELDS_SENDABLE =               1014
CLIENTAGENT_OPEN_CHANNEL =                      1100
CLIENTAGENT_CLOSE_CHANNEL =                     1101
CLIENTAGENT_ADD_POST_REMOVE =                   1110
CLIENTAGENT_CLEAR_POST_REMOVES =                1111
CLIENTAGENT_ADD_INTEREST =                      1200
CLIENTAGENT_ADD_INTEREST_MULTIPLE =             1201
CLIENTAGENT_REMOVE_INTEREST =                   1203

# FIXME: This needs to acknowledge the fact that there may be 128 bit
#  locations (64 bit do_ids and zones).
def parent_zone_to_location(parent, zone):
    return parent * 2**32 | zone

def location_to_parent_zone(location):
    return (location / 2**32, location % 2**32)

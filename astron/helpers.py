# FIXME: This needs to acknowledge the fact that there may be 128 bit
#  locations (64 bit do_ids and zones).
def parent_zone_to_location(parent, zone):
    return (parent << 32) | zone

def location_to_parent_zone(location):
    return (location >> 32, location % (2 << 32))

# Separate fields by keywords.

def field_has_keyword(field, keywords):
    """For internal use. Determines whether the field has any of
    the given keywords."""
    for keyword in keywords:
        if field.has_keyword(keyword):
            return True
    return False
        

def separate_fields(dclass, *preconditions):
    """Separate fields into lists based on the presence of keywords.
    preconditions are lists of keywords.
    This method returns a list of field IDs in ascending order
    where each field is in the first list that corresponds with a
    precondition where the field has a keyword named in the list.
    If it has no keyword named in the preconditions, it will be
    filed into an additional slot. For instance, calling
      separate_fields(["required", "db"], ["ram"])
    will return a tuple with three lists, where the first list
    contains the indices of all fields that have either the
    keyword "required" or "db", the second has "ram", but neither
    "required" or "db", and the third has the indices of fields
    that have none of "required", "db" or "ram".
    """
    sorted_fields = [[] for _ in range(0, len(preconditions) + 1)]
    for fld_index in range(0, dclass.num_fields()):
        field = dclass.get_field(fld_index)
        field_is_sorted = False
        for precon_index in range(0, len(preconditions)):
            if field_has_keyword(field, preconditions[precon_index]):
                sorted_fields[precon_index].append(fld_index)
                field_is_sorted = True
                break
        if not field_is_sorted:
            sorted_fields[-1].append(fld_index)
    return tuple(sorted_fields)

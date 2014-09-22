class DistributedObject:
    def __init__(self, repository, do_id, parent_id, zone_id):
        self.repo = repository
        self.do_id = do_id
        self.parent = parent_id
        self.zone = zone_id
    
    def init(self):
        print("DO created: %d" % (self.do_id, ))
    
    def delete(self):
        print("DO deleted: %d" % (self.do_id, ))

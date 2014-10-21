#!/usr/bin/env python

from time import sleep

from astron.object_repository import ClientRepository

if __name__ == '__main__':
    repo = ClientRepository('SimpleExample v0.2', 'simple_example.dc')

    def connected():
        print('Connection established.')
        login_manager = repo.create_view_by_classname('LoginManager', 1234, 0, 0)
        sleep(1)
        login_manager.login("guest", "guest")

    def ejected(error_code, reason):
        print('Got ejected (%i): %s' % (error_code, reason))

    def failed():
        print('Connection attempt failed.')

    repo.connect(connected, failed, ejected)

    while True:
        repo.poll_till_empty()
        #print(repo.poll_datagram())
        sleep(1)

## Lets do some random things
#print mod.get_num_classes() # or GetNumClasses
#cls = mod.get_class_by_name('Foobar')  # or getClassByName
#print cls.get_name() # -> 'Foobar'

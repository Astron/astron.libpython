python-libastron example
========================

This is a minimal example of how to build an MMO with Panda3D and Astron. To run it:
* start an astrond with the given config file: astrond astrond.yml
* start the login service: ./example_services.py
* start the AI service: ./example_world.py
* start clients

Major missing features:
* Preventing multiple logins.
* Merging example_services.py and example_world.py into a generic server process.
* Creating avatars.
* Panda3D bindings.

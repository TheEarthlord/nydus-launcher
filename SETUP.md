# Building the Nydus Launcher

### TODO get list of needed packages.
To build Nydus Launcher, you need the
apt packages ```devscripts``` and ```debhelper```.

The makefile in the root of the project should be
adequate. You just need to run ```make```.
Essentially the makefile runs ```debuild```.
The Nydus Launcher is entirely written in Python,
no C, so no compiling should be necessary.

# Installing and Configuring the Nydus Launcher

### TODO
Install python and Minecraft dependencies first
Install debs via apt
Create Azure account, create client, get client ID
Create certificates; a certificate chain for your
domain and a signed certificate for the server.
Fill out the configuration files at /etc/nydus
on the server and on all the clients.
Start the server.
Authenticate all your Minecraft accounts.
Go.

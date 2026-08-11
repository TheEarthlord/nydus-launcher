# Nydus Launcher

The Nydus Launcher is a custom distributed Minecraft Launcher.

## Basic Structure

Minecraft accounts are manually authenticated on a central server
daemon, then the authenticated access tokens are stored and renewed
there.
Clients which play Minecraft request accounts from the server.
The server allocates accounts to clients from its list of already
authenticated Minecraft accounts.

## Getting Started

See [SETUP.md](SETUP.md).

## Uses

The clients only ever see the username, uuid, and access token for
the account the server has allocated to them, never the password or
other authentication secrets. This is enough for the client to launch
an instance of Minecraft.

This is useful if you have users who you want to be able to play Minecraft,
but don't want to trust them with control of a Minecraft account or with
the secrets needed to log in to that account. This may be relevant in a
situation where an organisation owns a large number of Minecraft accounts
and wants members to be able to use those accounts to play games, but
not to be able to gain control of the accounts and take them home.

## Details

Network communication between clients and server is encrypted via TLS;
you'll need to provide a certificate identifying the server and a
certificate chain the clients will trust.

The server tracks which accounts are allocated to which clients,
and deallocates them when the client notifies the server that it's
finished playing. The server will only ever allocate an account to
one client at a time.

The Nydus Launcher is specifically written with the expectation of
a Ubuntu installation on all machines, where users log into clients
using SSHFS connections to the server; that is, all users on the clients
will be visible on the server.
This is used for things like checking that a request for account is coming
from a real user, and for additional strategies to detect when an
allocated Minecraft account is no longer in use and can be deallocated.
If your setup is different, the Nydus Launcher will likely require
modification.

It is assumed that the administrator has administrative control over the
clients (to install needed packages and certificates) as well as
the server, and has the ability to authenticate all the Minecraft accounts
to be used in the Nydus Launcher.

The Nydus Launcher uses Microsoft's Python MSAL to authenticate Minecraft
accounts. This will only work if your Minecraft account is a Microsoft one.

## Packages Included

The nydus-server package contains the server portion of the Nydus Launcher.
This should be installed on the server machine which the clients will
communicate with.

The nydus-cli package contains a command line interface to modify some
of the state of the server, in particular to manually edit the account
allocation database. It is not required for the Nydus Launcher to work,
but may be useful.

The nydus-common package contains code needed by both nydus-server and
nydus-cli.

The nydus-client package contains the client portion of the Nydus Launcher,
which requests a Minecraft account from the server and launches an instance
of Minecraft. It does not require the nydus-common package to function.

The nydus-test package has a variety of unit tests which it will run using
other installed Nydus Launcher packages.

## Requirements

Several additional python modules and some other packages are needed for the
Nydus Launcher to work.
The additional python modules needed are listed in nydus-server-requirements.txt
and nydus-client-requirements.txt. They may be installed by pip, but on
Debian-based systems such as Ubuntu (on which the Nydus Launcher was designed)
there are often apt packages which will install the same python modules.
Other required packages are listed as package dependencies in the Debian
control file under nydus-launcher/nydus-launcher/debian.

Worthy of note is that the nydus-client package needs the offical
minecraft-launcher deb package installed. This is because the minecraft-launcher
package sets up the needed installation environment, in particular the contents
of ~/.minecraft, and makes sure that the Java installation is correct
to allow Minecraft to run. The nydus-client package does have some functionality
to download needed jar files for requested Minecraft versions on the fly, but
can't set up the whole installation environment on its own.

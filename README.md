# Firework Controller
This repository contains the PC application for the firework controller.  Ultimately, this PC application in conjunction with the controller module (attached to the PC) will send and receive commands to the firework igniter.    

A configuration file *.json will define pertinent parameters as they relate to fireworks.  

* Python v3.8.0

## Development Environment
The source contained within this directory was written and tested under **Python v3.8.0**.  

### OS X

To install Python on Mac OS X, use [Homebrew](brew.sh). Then you can install
[virtualenv](https://virtualenv.pypa.io/en/latest/) and [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) using [pip](https://pip.pypa.io/en/stable/).

    $ brew install python3

### Windows

To install Python3 on Windows, download the appropriate package from
Python.org. See the [Install pip](https://pip.pypa.io/en/latest/installing/#install-pip) instructions for installing
pip on Windows.


## Dependencies
* datetime
* serial
* timeit
* re
* binascii
* os
* logging
* sys


## Tagged Versions 
* v1.0.0 -- This version, although very basic, is suitable to control a show.

* v1.0.1 -- Minor updates that allow the user to easily exit the application.  BAUD rate was changed to 9600. Successfully tested with XBee wireless controller and wireless igniter.  

* v1.2.0 -- Application now accepts --setcurrent and --getcurrent input arguments.  These arguments can be used to see or set the fuse-current value.  These features were successfully tested against the igniter.  
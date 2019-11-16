vSphere template installer
==========================

A python-based wizard for cloning one-off VMs from templates. Configures the network via
guestinfo parameters used by cloud-init-vmware-guestinfo package.

Installation
------------

Optionally create a python virtualenv, then run `pip install -r requirements.txt`.
Tested with python 3.7. 

Environment
-----------

To avoid entering the vSphere connection details multiple times you can set the following
environment variables:
- VSPHERE_ADDRESS
- VSPHERE_USERNAME
- VSPHERE_PASSWORD

Currently skipping other questions is not supported

![Screenshot of wizard](/screenshot.png?raw=true)


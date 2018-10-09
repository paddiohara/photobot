Notes on the updates for August 2018
====================================

Overview
--------
This document details changes made to allow the unit to run both the Canon
and Lorex camera's, and to be more robust with regard to drive and camera mounting.
To fix this we have added a new script, init_photobot.py, that is run by cron
on boot time to do some housekeeping, and we have adjusted the scripts.

Changes
-------
- new file: init_photobot.py - housekeeping script
- new file: photobot_lorex.py & lorex.py - lorex version of photobot
- entry in /etc/fstab removed to disable automounting of USB drive
- execution of init_photobot.py added to crontab for boot time
  - unmounts drive and camera
  - mounts drive
  - if mount successful, creates symlink /var/captures to /mnt/usbstorage/captures
  - if mount fails, creates symlink /var/captures to /home/pi/captures
- delays added to both photobot scripts to skip execution in first minute
  to ensure boot housekeeping has completed
- photobot scripts now write to /var/captures
- the files are checked out with git to /home/pi/master
- the photobot scripts run from their own python virtualenv at /home/pi/master/env

Git and Virtual Env
-------------------

>>> before all this gets done - need to init the repo "master" then when pulling for first time -
    must provide https://github.com/paddiohara/photobot.git   URL after pull

To keep files in sync better, we have a checkout from the git repo
on the device at /home/pi/master. To update from hit, we do:

$ cd /home/pi/master
$ git pull 

There should now be a python virtual env at /home/pi/master/env. To
create this on a new setup:

>>>> for this to work - need to install virtualenv first using apt-get

$ cd /home/pi/master
$ virtualenv env

To activate this virtualenv when working at the terminal, do:

$ source /home/pi/master/env/bin/activate

After activation, execution of python or pip will use the version in
the virtualenv. This means that cron entries and manual runs of photobot
must use this python binary. This can be done by activating (as above)
or using the full path when calling, like so:

$ /home/pi/master/env/bin/python /home/pi/master/src/photobot.py

After activating a new virtualenv we will also need to install any
python dependencies into it.

The Init Script
---------------
We've removed the fstab entry to automount the USB drive as it was occasionally
hanging the whole unit. We handle his now in the boot script, creating a
symlink at /var/captures. The boot script includes stub calls for making
notification HTTP requests to let us know when a reboot happened and whether
the USB mount failed. These can be filled in when we have a central service
for them to notify to. The boot script also unmounts the camera from the gnome
file system.

Rather than add the boot script to linux runlevels, it is scheduled in cron
to make it easier to administer. We have the following now in /etc/crontab

@reboot root /home/pi/master/env/bin/python /home/pi/master/src/init_pyphotobot.py
@reboot root /home/pi/master/env/bin/python /home/pi/master/src/photobot_lorex.py
@reboot root /home/pi/master/env/bin/python /home/pi/master/src/photobot.py

Changes to Photobot Scripts
---------------------------
There are now two photobot scripts, one for the lorex and one for the canon.
Note that the lorex version uses a companion file that it imports, lorex.py,
which must be in the same directory as photobot_lorex.py

These both have a new section at the beginning of main execution that checks
if the system has been up for more than one minute, and aborts if not. This
is to ensure our init script has finished all it's mounting.

Both scripts now write to /var/captures, which will then go to either the
USB drive or local storage.


System File Checklist
---------------------
- git repo checked out at /home/pi/master
- virtualenv creasted at /home/pi/master/env
- python dependencies installed using this virtualenv
- /etc/fstab empty
- /etc/crontab has:
  - @reboot root /home/pi/master/env/bin/python /home/pi/master/src/init_photobot.py
  - @reboot root /home/pi/master/env/bin/python /home/pi/master/src/photobot_lorex.py
  - @reboot root /home/pi/master/env/bin/python /home/pi/master/src/photobot.py
  - crontab entries for both photobot scripts every minute




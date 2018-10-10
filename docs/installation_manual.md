#  Setting up the Raspberry Pi 3 for photo capture

## Requirements:
This document details how to get the Pi 3 working for photo capture. In this doc,

You will need:
 * A computer running OSX, Windows, or Linux (the host)
 * A raspberry Pi 3
 * An SD card and reader, we will load the SD card from the host and put it in the Pi
 * An ethernet cable and connection for the Pi
 * Internet connection for your host and Pi, we assume you have wireless.

We have only tested these instructions on OSX. They should work (almost) identically on Linux.
It's definitely possible on Windows but the commands and tools are likely different. 

In our instructions:
 * "on your host" means commands exected on your computer (OSX, or Linux)
 * "on the pi":  menas commands exectued on the Pi at a command line prompt that we get to via SSH 

Lines in this document starting with '$' are commands typed at a terminal,
either on the host or the Pi. You don't need to type the '$', that's your prompt.

## Overview of Steps:
1) Setup up Raspberry Pi with Raspbian Jessie 
2) Get wifi working on Pi
3) Copy the installer script on to the pi
4) Run the installer script


We're going to install the Pi's operating system on an SD card, tweak it a bit,
put it in the Pi, boot up, and SSH into the Pi.

## Download Raspbian Jessie Lite
- on your host computer, download the Raspbian linux OS for the pi: https://www.raspberrypi.org/downloads/raspbian/
- the latest at time of writing is: Rasbian Stretch Lite, June 2018
- we are using Stretch Lite as we will not be plugging a keyboard and monitor into the Pi, 
  we're going to do everything over SSH. ("Stretch" is just the release nickname)

## Burn image on the SD card:
How you do this depends on your operating system. You may be able to do this with a 
graphical tool on your operating system, or you can follow the manual instructions below.
If you know how to burn the image, skip the next step and resume from "Enable SSH"
### OSX image burning instructions.
- put the SD card in your card reader and plug it into the USB port on your host (or 
  directly into your host if you have an SD card reader built in).
- find out the disk number of SD card by opening a terminal and executing:
  `$ diskutil list`
- look for the entry that matches the size of your card (so we know it's not your host hard drive)
- for this example, on our machine it was: /dev/disk2
- unmount that disk: 
  $ diskutil unmountDisk /dev/disk2
- copy or move the image you downloaded to the current directory, and execute
  the following to copy that image onto your sd card
  $ sudo dd bs=1m if=2017-01-11-raspbian-jessie-lite.img of=/dev/rdisk2
- note that in the above command, you must replace the name of the image file with your image
  and /dev/rdisk2 with /dev/rdisk{X} where X is your disk number. 
  Note that it is "/dev/rdiskX", not "/dev/diskX" in this command

## Enable SSH: Alter the image to enable 
After we have created a Raspbian image, we will alter it to enable networking.
Raspbian, for security reasons, disables SSH by default, so we won't be able to 
log into our Pi unless we enable it.
- Take out your SD card and put it back in. Your OS should automount the drives,
  with the boot sector of our burned image automounting on the host as "Boot".
- We need to put an empty file called 'ssh' in to the boot directory. (The Pi checks to
  see if this empty file was deliberately added before enabling SSH to prevent bot-net-of-things activity)
- In a terminal in your host, cd into the boot directory and execute:
  $ sudo touch ssh
- Check that it worked:
  `$ ls` 
- You should see the file called 'ssh' in there

## Load into Pi
- Unmount your SD reader, take out the SD card, and put the card into the pi. It slides
  into the metal holder on the underside of the pi, on the opposite end of the USB plugs.
- Plug the Pi into your network with an ethernet cable. We need to use a cable because 
  it doesn't know how to find wireless until we configure wifi.
- Boot the Pi. This happens as soon as you plug in the power.
- On your host, find the ip address of the pi using a portscanning application or through
  your router. On OSX, we used the free application "ipscan" (free download)
- Once we know the IP address, we can ssh in to the pi from the host using the 
  username 'pi' and password 'raspberry'
  * $ ssh pi@192.168.1.68  
- You are now on the PI!


## Setup the Pi (from the Pi)
Now we're going to continue setting up the Pi from the Linux prompt ON the Pi.

### Update System and Install Tools
- update the Debian repository info
  $ sudo apt-get update  
- you might want to install some text editors (optional). If you do, you know what you want. ;-)
  $ sudo apt-get install vim nano 

Setup up Wifi
- we have two options: 
   - A) log into PI over ethernet cable and ssh and set it up, what we'll do here
   - B) mount the image file on some host that can read ext3 and edit the filesystem directly
        - this is easy if you have a host system that runs linux, and otherwise it's a pain

A) setup ON the pi (these commands are executed on the pi, over ssh)
  - scan for networks to find out the name of your wifi network
  $ sudo iwlist wlan0 scan
  - look for your network, ie the same one you use for normal wireless at home
   (at my house it's called TELUS0001, we're going to pretend my password is "Hunter2")
  - we need to edit the wireless config file, using the editor of your choice. I use vim,
    you prob want to use nano if you don't know any linux editors. 
  $ sudo vim /etc/wpa_supplicant/wpa_supplicant.conf
  or 
  $ sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
  
- add in an entry for your wifi and save the file:
  network={
    ssid="TELUS0001"
    psk="hunter2"
  }

- restart networking
  $ sudo ifdown wlan0
  $ sudo ifup wlan0
- if you look on your host ip scanner again, the pi should now appear with a second IP address
- test this out by unplugging the ethernet cable, rebooting the pi, and SSH'in with the 
  new (wireless) network IP. 


B) Setting up by directly accessing the drive
  - on OSX, you can install extfs drivers from https://www.paragon-software.com/home/extfs-mac
    or:
  - start up a linux install. We used VirtualBox and Ubuntu, which are free. We needed to install
  the VirtualBox guest addons and extensions to be able to read the USB drive.
  - put your SD card for the Pi in the reader, mount it from your linux or osx install
  - you should see two drives on there, Boot and the main drive
  - in the main drive, open /etc/wpa_supplicant/wpa_supplicant.conf and add the networking
    entry as detailed above

Installing Gphoto2
------------------
We're going to use gphoto2 to make the Pi take pictures. Plug your camera into the Pi
over USB.
  
Install Gphoto2
  - install gphoto2 from debian packages:
    $ sudo apt-get install gphoto2
  - plug in your camera over USB to check if gphoto2 is working
    $ gphoto2 --list-config 
  - you should see it detect your camera


Setting up the External USB drive
---------------------------------
We don't want the Pi drive to fill up, so we need to connect the USB drive
and make sure it's working fine on a reboot


Setting up the drive
- if you can, format your drive to ext3 so that the Pi can mount it without issue
  - you can use others, but it's easier to make it native readable by linux
- A very detailed guide with instructions for more complex situations (non-ext3) is here:
  http://www.htpcguides.com/properly-mount-usb-storage-raspberry-pi/

- make a directory on the Pi that we'll use as the mount point, IE this will be 
  the path to the USB drive after it's mounted for copying images.
  Note, the photobot code uses this path, so don't name it anything different!
  $ sudo mkdir /mnt/usbstorage

- on the pi, after plugging in the drive, get the drive id:
  $ sudo blkid
  - we found it as /dev/sda1

- mount it on /mnt/usbstorage
  $ sudo mount /dev/sda1 /mnt/usbstorage

- change permissions so we can write to it ok
  $ sudo chmod 755 /mnt/usbstorage

- now we'll edit the fstab file to automount the drive on boot.
  - this is a tricky step, if you screw up an fstab file your device will hang on boot
  and you'll have to take out the SD card, mount it on your host, and repair it there
  
 - edit the fstab file (with your editor, vim/nano/emacs, whatever)  
    $ sudo vim /etc/fstab
  - add the following line IF your drive is formatted as ext3, 
   where /dev/sda1 is your device name found above
    
    /dev/sda1 /mnt/usbstorage /ext3 defaults 0 0

  - test your fstab! Don't skip this!
  $ sudo mount -a
  - if we get errors, your fstab is no good and you should consult the link at the beginning
  of this section for instructions for other drive types. 
  - keep working on this until the "sudo mount -a" command works. Do not reboot the Pi until it does.


Testing our Setup 
-----------------
At this point we have a Pi setup, with wireless networking, a mounted USB drive,
and Gphoto2 installed. We can test to see whether we really are setup before adding the code:

- reboot, with camera and drive attached over USB
- ssh in to Pi
- make a directory for our pictures:
  $ mkdir /mnt/usbstorage/captures
- take a picture with Gphoto.
  NB: This is a long command and you will find shorter ones online, however this method works 
  reliably while the other commands we tried hung way too frequently
  
  $ gphoto2 --wait-event=1s --set-config eosremoterelease=2 --wait-event=1s \ 
    --set-config eosremoterelease=4 --wait-event-and-download=2s \
    --force-overwrite --get-all-files --delete-all-files \
    --filename=/mnt/usbstorage/captures/test.jpg

  - your camera should take a picture
  - you should see our test.jpg file in /mnt/usbstorage/captures:
  $ ls /mnt/usbstorage/captures

Success, the Pi is ready for automation!


Setting up the photobot software on the Pi
------------------------------------------
- on your host download the latest photobot file from github, and go
  to a directory with the file in it

- upload the photobot software to Pi
  $ sftp pi@{IP ADDRESS}
  $ put photobot_2017-02-05.py
  (where photobot_2017-02-05.py is the latest photobot python script)

- make sure photobot script paths exist
  - log files get written somewhere
  - captures go somewhere local
  - captures get moved somewhere to
- test a run of photobot:
  $ python photobot_2017-02-05.py

- a run should produce the following artifacts:
  - photobot.pid -> file with process id of the run
  - photo_bot.log -> log file with all the log output
  - image files in captures directory 

- create a symlink to photobot_2017-02-05.py called photobot.py so cron doesn't need version info
  $ sudo ln -s photobot_2017-02-05.py photobot.py


SETUP CRONTAB:
- edit system crontab to call script once a minute
  $ sudo vim /etc/crontab
  - add the line:
  * * * * * root python /home/pi/photobot.py 
 
ALL DONE!


Appendix:
CLONING THE PI:
- article:
  https://thepihut.com/blogs/raspberry-pi-tutorials/17789160-backing-up-and-restoring-your-raspberry-pis-sd-card
  http://michaelcrump.net/the-magical-command-to-get-sdcard-formatted-for-fat32/

- to copy an image from the SD card to computer:
  - find out disk number using:
     $ diskutil list
  - unmount disk:
     $ diskutil unmountDisk /dev/disk2
  - copy image
     $ sudo dd if=/dev/disk2 of=~/SDCardBackup.dmg

- to copy image to an SD card:
  - unmount SD disk, find out disk number using diskutil as above:
  - format disk to FAT32 and name it 
    sudo diskutil eraseDisk FAT32 NAME_RASPBIAN MBRFormat /dev/disk2
  - copy the image over, warning this can take a very long time (hours)
    sudo dd if=raspbian_photobot_2017-03-06.dmg of=/dev/disk2


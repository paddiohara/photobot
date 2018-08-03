#!/bin/python

"""
Housekeeping reboot job that runs on reboot of the Pi:
Purpose:
 - attempt to mount usb drive
 - if usb mount fails, use SD card
 - create a symlink to be used for image storage
 - notify us somehow if the mount was the SD card
   - this will prob be an http post to our control panel
     so as not to rely on email from the hosting network
 - log whatever was done

 NB: this needs to execute with SUDO privileges, it mounts drives and so on
"""

import os
import subprocess

import logging
log = logging.getLogger(__name__)

USB_DEV = "/dev/sd??"
USB_DIR = "/mnt/usbstorage"
SD_DIR = ""

def setup_logging(log_filepath, log_level=logging.INFO):
    # set up logging, saves output to a log file
    fh = logging.FileHandler(log_filepath)
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    log.addHandler(fh)
    log.addHandler(ch)
    log.level = log_level


def notify_mount_failed():
    """post to control panel that usb mount failed"""
    # make an http request to somewhere that will notify us, yo
    print("I'm posting a mount failure, yo")
    log.info("notifying control panel of mount failure")

def notify_reboot():
    """post to control panel that the photobot rebooted"""
    print("I'm posting a reboot, yo")
    log.info("notifying control panel of reboot")


if __name__=="__main__":
    # try log with two paths so we can run this in non-pi envs
    try:
        setup_logging('/home/pi/init_photobot.log', logging.INFO)
    except IOError as exc:
        setup_logging('init_photobot.log', logging.INFO)
    log.info("Reboot, init_photobot.py executing")

    notify_reboot()

    # remove old symlink
    os.system("rm -f /var/captures")

    # attempt to mount the USB drive, returns non-zero on failure
    mount_failed = os.system("mount %s %s" % (USB_DEV, USB_DIR))

    # create a symlink at /var/captures to either usb mount or SD card
    if mount_failed:
        log.info("Mount of usb drive failed, falling back to SD card")
        notify_mount_failed()
        # make the symlink to local dir
        os.system("ln -s %s /var/captures" % SD_DIR)
    else:
        log.info("USB drive mounted.")
        os.system("ln -s %s /var/captures" % USB_DIR)

    # public permissions on our symlink
    os.system("chmod a+rw /var/captures")


# python script to setup photobot on pi
import subprocess
from datetime import datetime
import time
import sys
import os
import logging
import argparse

def do(command):
    "execute a shell command"
    print(command)
    #output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True, universal_newlines=True) 
    subprocess.check_call(command, stderr=subprocess.STDOUT, shell=True, universal_newlines=True) 


class PhotobotInstaller(object):

    def __init__(self, args):
        self.args = args
        self.wpa_file = args.wpa_file or "/etc/wpa_supplicant/wpa_supplicant.conf"

    def do(command, kw=None):
        "print and execute a shell command, exiting on failure"
        if kw:
            command = command.format(**kw)
        print(command)
        if not args.dry_run:
            try:
                subprocess.check_call(command, stderr=subprocess.STDOUT, shell=True, universal_newlines=True) 
            except:
                print("\n\nERROR executing command: '%s'" % command)
                print("INSTALL ABORTED\n")
                sys.exit() 

    def confirm(self, question, allow_no=True):
        "ask user for confirmation to do task, returns result as boolean"
        while True:
            if allow_no:
                res = input("%s y/n/x >> " % question)
            else:
                res = input("%s y/x >> " % question)

            if res.lower() == 'x':
                print("\nEXITING")
                self.exit()
            if res.lower() in ('y','yes'):
                return True
            if res.lower() in ('n','no'):
                return False
            # anything else, we reask the question


    def exit(self):
        print("EXITING")
        sys.exit()


    def setup_wifi(self):
        # get network settings    
        # TODO check if the network is already in there
        while True:
            network_name = input("Network name: ")
            network_password = input("Network password: ")
            if self.confirm("Patch %s with network '%s' and password '%s'?" % 
                (self.wpa_file, network_name, network_password) ):
                break
        # patch file
        patch = """
  network={
    ssid="%s"
    psk="%s"
  }
""" % (network_name, network_password)
        with open(self.wpa_file, "a") as wpa_file:
            wpa_file.write(patch)
        if self.confirm("wpa file patched, restart networking?"):
            self.do("ifdown wlan0")
            self.do("ifup wlan0")
        self.confirm("select 'y' to continue or 'x' to exit so you can reboot your pi")


    def install_packages(self):
        print("running apt-get update, installing nano, vim, gphoto2...")
        self.do("apt-get update")
        self.do("apt-get install nano vim")
        self.do("install gphoto2")
        if self.confirm("test gphoto2 to see camera? (plug in camera)")
            do("gphoto2 --list-config")
            self.confirm("camera found, continue?", allow_no=False)    


    def setup_drive(self):
        print("setting up external USB drive")
        if self.confirm("create dir /mnt/usbstorage")
            do("mkdir /mnt/usbstorage")
        self.confirm("plug in USB drive and continue", allow_no=False)
        print("checking drive ID with 'blkid'")
        do("blkid")
        while True:
            dev_num = int( input("Enter drive number: ") )
            if self.confirm("Drive number is '%i' " % dev_num):
                break
        print("mounting /dev/sda%i" % dev_num)
        do("mount dev/sda%i /mnt/usbstorage")
        do("chmod 755 /mnt/usbstorage")        
        if self.confirm("edit fstab file to automount drive as ext3?")
            patch = "/dev/sda%i /mnt/usbstorage /ext3 defaults 0 0"
            # patch the fstab file and test 
            with open(self.fstab_file, "a") as fstab_file:
                fstab_file.write(patch)
            print("Testing fstab file. WARNING: do not reboot if this errors, Pi will hang.")
            do("mount -a")
            self.confirm("press y to continue, x for exit", allow_no=False)



    # main install process
    def main(self):
        print("Running photobot installer")

        if not self.confirm("Did you execute this as sudo?"):
            self.exit()

        if self.confirm("setup wifi configuration?"):
            self.setup_wifi()

        if self.confirm("Install packages?"):
            self.install_packages()             

        if self.confirm("Setup USB drive?"):
            self.setup_drive()
   
        # left off: 
        # download photobot script from github
        # make/check directories
        # setup cronjob
 


if __name__=="__main__":
  
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action="store_true", help="print commands but don't run them")
    parser.add_argument('--wpa-file', help="alternate networking file to patch")
    parser.add_argument('--fstab-file', help="alternate fstab file to patch")
    args = parser.parse_args()

    print("running with args: %s" % args)
    installer = PhotobotInstaller(args) 
    installer.main()

#!/usr/bin/python3

"""
Lorex Camera version of photobot

TODO/Sort out
- python 2.7 only
- we need the wsdl dir
- we need the network location for the lorex, we might
  need to scan for that??
"""


import subprocess
from datetime import datetime
import time
import os
import sys
import logging
from lorex import LorexCam


# TODO: move all this stuff into an ini file!

# length of one sequence of photos
NUM_PHOTOS = 3
#NUM_ROUNDS = 2
NUM_ROUNDS = 1
#ROUND_DELAY = 30
ROUND_DELAY = 5
PICTURE_DELAY = 3

# the below will be a symlink to where we want captures
CAPTURE_DIR = "/var/lorex"
# WSDL dir for the lorex lib
WSDL_DIR = "/home/pi/.local/wsdl"
# network host for the camera
LOREX_HOST = "192.168.0.101"
LOREX_PORT = 80
LOREX_USER = 'admin'
LOREX_PASSWORD = '1wingDfeat'


def get_photo_filename():
    "return a filename with date and time, ie: capture_2017-04-02_02-03-12"
    time_str = str(datetime.now()).split('.')[0].replace(' ','_').replace(':','-')
    filename = 'lx_capture_%s.jpg' % time_str
    return filename


def setup_logging(log_filepath, log_level=logging.INFO):
    "setup the python logging structure"
    # set up logging, saves output to a log file
    log = logging.getLogger("PHOTOBOT")
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
    return log

################################################################################
# beginning of main execution
if __name__=="__main__":

    # check if system has been up for a minute, if not, exit
    # this is to make sure our housekeeper has finished its job first
    uptime_str = subprocess.check_output("uptime -p",
        stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    # when uptime is less than 1 minute, the output is just "up"
    if uptime_str.strip() == "up":
        sys.exit()

    # set file path and log level for logging
    try:
        log = setup_logging('/mnt/usbstorage/captures/photobot.log', logging.INFO)
    except IOError as exc:
        # fall back to logging in local dir
        try:
            log = setup_logging('/home/pi/photobot.log', logging.INFO)
        except IOError as exc:
            log = setup_logging('photobot.log', logging.INFO)

    log.info("-----------------------------------------------------------------------------")
    log.info("EXECUTING RUN at %s" % datetime.now() )

    # get the pid of the last run of photobot, and try to kill that process
    # this because sometimes the camera and script can hang
    # it's harmless if the previous pass didn't hang
    try:
        # open the text file with the last pid
        with open("photobot.pid", "r") as f:
            last_pid = int( f.read() )
            kill_command = "kill -9 %s" % last_pid
            output = subprocess.check_output(kill_command, stderr=subprocess.STDOUT, shell=True, universal_newlines=True) 
            log.info("killed previous process: %i" % last_pid)
    except Exception, e:
        # previous process did not hang, do nothing
        pass 

    # save pid of this pass so that subsequent photobot passes can kill a hung photobot process
    this_pid = os.getpid()
    with open("photobot.pid", "w") as f:
        f.write( str(this_pid) )
        log.info("saved current pid %i to file" % this_pid)
   
    # done process housekeeping 

    # instantiate our lorex camera
    # these settings could come from env variables. How will we get the network address??
    lorex_cam = LorexCam(
        host = LOREX_HOST,
        port = LOREX_PORT,
        user = LOREX_USER,
        password = LOREX_PASSWORD,
        wsdl_dir = WSDL_DIR
    )

    # take two rounds of pictures, separated by 30 seconds 
    for i in range(0, NUM_ROUNDS):
        for i in range(0, NUM_PHOTOS):
            filename = get_photo_filename() 
            local_filepath = "%s" % filename
            ext_filepath = "%s/%s" % (CAPTURE_DIR, filename)
            # save capture from camera
            lorex_cam.save_image(local_filepath)
            # move the file from pi to usb drive
            move_command = "mv %s %s" % (local_filepath, ext_filepath)
            try:
                output = subprocess.check_output(move_command, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
                log.info("image moved to %s" % ext_filepath)
            except subprocess.CalledProcessError as exc:
                log.info("ERROR moving image: '%s'" % exc.output)
            time.sleep(PICTURE_DELAY)

        # sleep until next round
        time.sleep( ROUND_DELAY )

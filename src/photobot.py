#!/usr/bin/python3

import subprocess
from datetime import datetime
import time
import sys
import os
import logging


# length of one sequence of photos
NUM_PHOTOS = 3
NUM_ROUNDS = 2
ROUND_DELAY = 30

def get_photo_filename():
    "return a filename with date and time, ie: capture_2017-04-02_02-03-12"
    time_str = str(datetime.now()).split('.')[0].replace(' ','_').replace(':','-')
    filename = 'capture_%s.jpg' % time_str 
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


# beginning of main execution
if __name__=="__main__":

    # set file path and log level for logging
    try:
        log = setup_logging('/mnt/usbstorage/captures/photobot.log', logging.INFO)
    except IOError as exc:
        # fall back to logging in local dir
        log = setup_logging('/home/pi/photobot.log', logging.INFO)

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

    # take two rounds of pictures, separated by 30 seconds 
    for i in range(0, NUM_ROUNDS):

        for i in range(0,NUM_PHOTOS):
            filename = get_photo_filename() 
            local_filepath = "/home/pi/captures/%s" % filename
            ext_filepath = "/mnt/usbstorage/captures/%s" % filename

            # NB: no sleep necessary, time delay is in the command
            # NB: this long form with eosremotereleases is the ONLY version that has worked reliably
            # for the camera, the simpler version you can find online hung frequently for us
            photo_command = ("gphoto2 --wait-event=1s --set-config eosremoterelease=2 --wait-event=1s "
                " --set-config eosremoterelease=4 --wait-event-and-download=2s --filename=%s "
                "--force-overwrite --get-all-files --delete-all-files" % local_filepath)
           
            try: 
                output = subprocess.check_output(photo_command, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
                log.info("captured photo: %s" % filename)
            except subprocess.CalledProcessError as exc: 
                log.info("ERROR capturing photo: '%s'" % exc.output)

            # move the file from pi to usb drive
            move_command = "mv %s %s" % (local_filepath, ext_filepath)
            try:
                output = subprocess.check_output(move_command, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
                log.info("image moved to %s" % ext_filepath)
            except subprocess.CalledProcessError as exc: 
                log.info("ERROR moving image: '%s'" % exc.output)

        # sleep until next round
        time.sleep( ROUND_DELAY )

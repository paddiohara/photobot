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
import argparse
from configparser import ConfigParser


# settings that must be present in the ini file
required_settings = [
    'photos_per_round',
    'number_of_rounds',
    'delay_between_rounds',
    'delay_between_photos',
    'capture_dir',
    'wsdl_dir',
    'lorex_host',
    'lorex_port',
    'lorex_user',
    'lorex_password'
]

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
    # NB: this does NOT work on OSX/BSD, you'll need to disable it for dev on OSX
    uptime_str = subprocess.check_output("uptime -p",
        stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    # when uptime is less than 1 minute, the output is just "up"
    if uptime_str.strip() == "up":
        sys.exit()

    # register the process identifier utility for multiprocess logging
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--settings',
        help='Path to settings INI file for Lorex photobot',
        required=True)
    options = argparser.parse_args()
    settings_file = options.settings

    config = ConfigParser()
    config.read(settings_file)
    settings = dict(config.items('app:main'))

    # exit if settings file missing items
    for setting_name in required_settings:
        try:
            assert settings[setting_name]
        except:
            raise Exception("Missing setting '%s' in ini file" % setting_name)

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

    # instantiate our lorex camera
    # these settings could come from env variables. How will we get the network address??
    lorex_cam = LorexCam(
        host = settings['lorex_host'],
        port = settings['lorex_port'],
        user = settings['lorex_user'],
        password = settings['lorex_password'],
        wsdl_dir = settings['wsdl_dir'],
    )

    # execute X rounds of Y pictures according to settings
    for i in range(0, int(settings['number_of_rounds'])):
        for i in range(0, int(settings['photos_per_round'])):
            filename = get_photo_filename() 
            local_filepath = "%s" % filename
            ext_filepath = "%s/%s" % (settings['capture_dir'], filename)
            # save capture from camera
            lorex_cam.save_image(local_filepath)
            # move the file from pi to usb drive
            move_command = "mv %s %s" % (local_filepath, ext_filepath)
            try:
                output = subprocess.check_output(move_command, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
                log.info("image moved to %s" % ext_filepath)
            except subprocess.CalledProcessError as exc:
                log.info("ERROR moving image: '%s'" % exc.output)
            time.sleep( int(settings['delay_between_photos']) )

        # sleep until next round
        time.sleep( int(settings['delay_between_rounds']) )

import logging
import logging.config
import argparse
from configparser import ConfigParser
import os
import sys
import time
import json
from gps3 import agps3

from ais_model import Model

import pdb
# required settings, which can come from ini file or command line args
# db_url                sqlalchemy db connection url
# minimum_latitude      min latitude in which to capture data
# maximum_latitude      max latitude in which to capture data
# minimum_longitude     min longitude in which to capture data
# maximum_longitude     max longitude in which to capture data


# TODO: move this later
def setup_logging(log_level):
    "setup the python logging structure"
    # set up logging, saves output to a log file
    log = logging.getLogger(__name__)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)
    log.level = log_level
    return log


def main():
    # register the process identifier utility for multiprocess logging
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--settings',
        help='Path to settings INI file for AIS Receiver',
        required=True)
    argparser.add_argument(
        '--init-db',
        help='Initialize the database, creating tables',
        action="store_true",
        required=False)
    options = argparser.parse_args()
    settings_file = options.settings

    config = ConfigParser()
    config.read(settings_file)
    settings = dict(config.items('app:main'))

    # TODO later, config logging from ini file
    #logging.config.fileConfig(settings_file)
    #log = logging.getLogger(__name__)
    log = setup_logging(logging.DEBUG)

    log.debug("instantiating model")
    model = Model(settings, logger=log)

    if options.init_db:
        log.info("Initializing database")
        model.init_db()
        log.info("  db initialized, exiting")
        return

    log.info("ais_receiver main()")

    # connect to the gpsd server
    # TODO: do the right thing if gpsd not on or can't connect 
    gps_socket = agps3.GPSDSocket()
    ds = agps3.DataStream()
    gps_socket.connect()
    gps_socket.watch()
    
    for json_msg in gps_socket:
        if json_msg:
            #log.debug("received msg: %s" % json_msg)
            model.handle_json_message(json_msg)
    else:
        time.sleep(.001)


if __name__=="__main__":
    main()

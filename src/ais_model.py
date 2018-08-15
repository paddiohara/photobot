from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from sqlalchemy import (
    Column,
    Text,
    Integer,
    DateTime,
    Boolean,
    ForeignKey
)
from sqlalchemy.orm import relationship

from datetime import datetime
import json

import logging
log = logging.getLogger(__name__)
import pdb

# sqlachemy Declarative Base base class for ORM models
Base = declarative_base()

class Resource(object):
    "mixin to provide constructor for models"
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

class PositionMessage(Resource, Base):
    "base class/table for position messages of type A and B"
    __tablename__ = 'position_message'

    __mapper_args__ = {
        'polymorphic_identity': 'position_base',
        'polymorphic_on': 'message_class'
    }

    id = Column(Integer, primary_key=True)
    # polyphonic id field
    message_class = Column(Text, nullable=False)
    datetime = Column(DateTime, nullable=False, default=datetime.now)
    # store the raw json message for ref
    json_message = Column(Text, nullable=False)

    # below are the raw fields from the message
    # all fields in this base class are in both Position A & B messages
    type = Column(Integer, nullable=False)
    repeat = Column(Integer)
    mmsi = Column(Integer)
    # speed is in tenths of a knot, with max val of 1023
    speed = Column(Integer)
    accuracy = Column(Boolean)
    # lon and lat are in 1/10000 min. divide by 600 000 to get degrees
    lon = Column(Integer)
    lat = Column(Integer)
    # course over ground in 10th of a degree
    course = Column(Integer)
    # heading in degrees
    heading = Column(Integer)
    # second of timestamp of message
    second = Column(Integer)
    # raim flag: is Receiver Autonomous Integrity Monitoring used to check the performance of EPFD.
    raim = Column(Boolean, default=False)
    # diagnostic bits for radio system
    radio = Column(Integer)


class PositionMessageA(PositionMessage):
    """
    derived class for Class A Position Messages, Type 3
    contains only fields unique to Class A Position messages
    """

    __tablename__ = 'position_class_a'
    __mapper_args__ = {
        'polymorphic_identity': 'position_a',
    }

    id = Column(Integer, ForeignKey('position_message.id'), primary_key=True)

    # navigation status, see web page for codes
    status = Column(Integer)
    # turn rate code from 0-128 see web page for codes
    turn = Column(Integer)
    # 0=n/a, 1=no special maneuver, 2=special maneuver
    maneuver = Column(Integer)


class PositionMessageB(PositionMessage):
    """
    derived class for Class B Position Messages, Type 18
    contains only fields unique to Class B Position messages
    """

    __tablename__ = 'position_class_b'
    __mapper_args__ = {
        'polymorphic_identity': 'position_b',
    }

    id = Column(Integer, ForeignKey('position_message.id'), primary_key=True)
    # 0=Class B SOTDMA unit 1=Class B CS (Carrier Sense) unit
    cs = Column(Boolean)
    # 0=No visual display, 1=Has display, (Probably not reliable).
    display = Column(Boolean)
    # If 1, unit is attached to a VHF voice radio with DSC capability.
    dsc = Column(Boolean)
    #  If this flag is 1, the unit can use any part of the marine channel.
    band = Column(Boolean)
    # If 1, unit can accept a channel assignment via Message Type 22.
    msg22 = Column(Boolean)
    # Assigned-mode flag: 0 = autonomous mode (default), 1 = assigned mode.
    assigned = Column(Boolean)



class StaticDataMessage(Resource, Base):
    "base class/table for status messages of type A and B"
    __tablename__ = 'static_data_message'

    __mapper_args__ = {
        'polymorphic_identity': 'static_data_base',
        'polymorphic_on': 'message_class',
    }

    id = Column(Integer, primary_key=True)
    # polyphonic id field
    message_class = Column(Text, nullable=False)

    # fields common to both Class A and Class B
    type = Column(Integer, nullable=False)
    repeat = Column(Integer)
    mmsi = Column(Integer)
    callsign = Column(Text)
    shipname = Column(Text)
    to_bow = Column(Integer)
    to_stern = Column(Integer)
    to_port = Column(Integer)
    to_starboard = Column(Integer)


class StaticDataMessageA(StaticDataMessage):
    "derived class for Static Data Class A - Type 5"
    __tablename__ = 'static_data_class_a'

    __mapper_args__ = {
        'polymorphic_identity': 'static_data_a',
        'polymorphic_on': 'message_class'
    }

    id = Column(Integer, ForeignKey('static_data_message.id'), primary_key=True)
    # polyphonic id field
    message_class = Column(Text, nullable=False)

    # fields in Class A only
    # 0=[ITU1371], 1-3 = future editions
    ais_version = Column(Integer)
    # IMO ship ID number
    imo = Column(Integer)
    # int code for shiptype
    shiptype = Column(Integer)
    # int code for EPFD Fix types
    epfd = Column(Integer)
    month = Column(Integer)
    day = Column(Integer)
    hour = Column(Integer)
    # draught in 1/10 meters
    draught = Column(Integer)
    destination = Column(Text)
    # 0=data terminal ready, 1=not ready (default)
    dte = Column(Boolean)


class StaticDataMessageB(StaticDataMessage):
    "derived class for Static Data Class A - Type 5"
    __tablename__ = 'static_data_class_b'

    __mapper_args__ = {
        'polymorphic_identity': 'static_data_b',
        'polymorphic_on': 'message_class'
    }

    id = Column(Integer, ForeignKey('static_data_message.id'), primary_key=True)
    # polyphonic id field
    message_class = Column(Text, nullable=False)

    # fields in Class B only
    partno = Column(Integer)
    vendorid = Column(Text)
    model = Column(Integer)
    serial = Column(Integer)
    mothership_mmsi = Column(Integer)


class Model(object):
    "Model singleton for the main script to use"

    # only messages of these NMEA types get stored
    _types_to_message_class = {
        1: PositionMessageA,
        2: PositionMessageA,
        3: PositionMessageA,
        5: StaticDataMessageA,
        18: PositionMessageB,
        24: StaticDataMessageB,
    }

    def __init__(self, settings, logger=None):
        self.log = logger if logger else log 
        self.log.info("Model.__init__()")

        if 'sqlalchemy.url' not in settings:
            raise Exception("ERROR: model requires a valid db_url in settings")
        self.engine = create_engine(settings['sqlalchemy.url'])
        self.Session = sessionmaker(bind=self.engine)
        # to get an sqlalchemy session, client code will call model.Session()
        
        # convert our ini files lat/lon grid to the NMEA format
        # where lat and lon are in 10000/ths of a min
        self.min_lon = int( float(settings['minimum_longitude']) * 600000 )
        self.max_lon = int( float(settings['maximum_longitude']) * 600000 )
        self.min_lat = int( float(settings['minimum_latitude']) * 600000 )
        self.max_lat = int( float(settings['maximum_latitude']) * 600000 )

        self.log.info("model settings: min_lat: %s min_lon: %s max_lat: %i max_lon: %i" %
             (self.min_lat, self.min_lon, self.max_lat, self.max_lon) )
        self.log.debug("model init complete")
        
        
    def init_db(self):
        self.log.info("creating tables")
        Base.metadata.create_all(self.engine)


    def handle_json_message(self, json_msg):
        "save an AIS message from data dict"
        data = json.loads(json_msg)

        self.log.debug("model.handle_json_message() data:%s" % data)

        msg_type = data.get('type',None)
        if msg_type not in self._types_to_message_class:
            self.log.debug("  - msg type field missing or out of range ignoring")
            return

        # for position messages, (type 1,2,3,18,19) filter on location
        if msg_type in [1,2,3,18,19]:
            if( data['lat'] < self.min_lat or data['lat'] > self.max_lat or
              data['lon'] < self.min_lon or data['lon'] > self.max_lon): 
                self.log.debug(' msg out of position range, ignoring ')
                return


        # if we get this far, we have a msg to store as a DB object
        # NB: static data messages don't have lat/lon so we get them ALL

        dbs = self.Session()
        MessageClass = self._types_to_message_class[msg_type]
        self.log.debug("storing message of class: %s" % MessageClass)
        msg = MessageClass(
            datetime = datetime.now(),
            json_message = json.dumps(data),
            **data
        )
        dbs.add( msg )
        dbs.commit()
        self.log.debug("  - message stored")

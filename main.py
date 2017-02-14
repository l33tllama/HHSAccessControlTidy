#!/usr/bin/env/python

import time
import logging, logging.handlers
import ConfigParser
from DoorController import DoorController as dc
from TinyDBConnector import TinyDBConnector as tdb
from PushbulletMessager import PushbulletMessager

# separate program in separate user, to hide password..
from TidyHQController import TidyHQController

config_filename = 'config.cfg'

#TODO: messaging (pushbullet)
# - person entered, alarm armed, alarm sounding, etc
#TODO: debug log
#TODO: log when someone tries to enter after several tag scans

class AccessController():
    def __init__(self):
        self.last_tag_scanned = 0
        self.db_reload_interval_seconds = 2 * 60
        self.db_reload_seconds = 0

        # CONFIG
        self.config = ConfigParser.RawConfigParser()
        self.config.read(config_filename)

        # CONFIG VARIABLES
        db_loc = self.config.get('TinyDB', 'db_location')
        pb_token = self.config.get('Pushbullet', 'access_token')
        pb_channel = self.config.get('Pushbullet', 'channel_name')
        tidy_client_id = self.config.get('TidyHQ', 'client_id')
        tidy_client_secret = self.config.get('TidyHQ', 'client_secret')
        tidy_member_group = self.config.get('TidyHQ', 'group_id')
        tidy_domain_prefix = self.config.get('TidyHQ', 'domain_prefix')
        self.tidy_username = self.config.get('TidyHQ', 'username')
        # IMPORTANT - Make sure you run this on a server with a password only you know!
        # As it's saved in plain text :/
        self.tidy_password = self.config.get('TidyHQ', 'password')
        log_filename = self.config.get('Logging', 'filename')
        log_filesize = self.config.get('Logging', 'size_bytes')
        log_backup_count = self.config.get('Logging', 'backup_count')

        # LOGGING
        self.entrant_logger = logging.getLogger('EntrantLogger')
        self.entrant_logger.setLevel(logging.INFO)
        FORMAT = "%(asctime)-15s %(message)s"
        logging.basicConfig(format=FORMAT)
        self.formatter = logging.Formatter("%(asctime)s;%(message)s")

        self.rot_handler = logging.handlers.RotatingFileHandler(log_filename,
                                                                maxBytes=log_filesize,
                                                                backupCount=log_backup_count)
        self.rot_handler.setFormatter(self.formatter)
        self.entrant_logger.addHandler(self.rot_handler)

        # PUSHBULLET
        self.pb = PushbulletMessager(pb_token, pb_channel)
        #self.pb.test_message("TESTING")

        # DOOR CONTROLLER
        self.dc = dc(nopigpio=True)
        self.dc.set_tag_scanned_callback(self.tag_scanned)

        # TINYDB
        self.tinydb = tdb(db_loc)

        # TIDYHQ
        self.tidyhq = TidyHQController(tidy_client_id, tidy_client_secret, tidy_member_group, tidy_domain_prefix)

    def tag_scanned(self, bits, rfid):
        contact, is_allowed = self.tinydb.is_allowed(rfid)
        if contact is not None:
            print(contact['first_name'] + " " + contact['last_name'])
            if is_allowed is True:
                self.dc.unlock_door()
                print ("is allowed!")
            else:
                print ("isn't allowed")
        else:
            print ("Unknown tag ID")

    def run(self):
        self.tidyhq.connect_to_api(self.tidy_username, self.tidy_password)
        self.tidyhq.reload_db(self.tinydb.userdb)

        self.tag_scanned(0, 99412070)

        while True:
            time.sleep(1)
            self.db_reload_seconds += 1
            if(self.db_reload_seconds > self.db_reload_interval_seconds):
                self.tidyhq.connect_to_api(self.tidy_username, self.tidy_password)
                self.tidyhq.reload_db(self.tinydb.userdb)

        self.dc.on_end()

if __name__ == '__main__':
    ac = AccessController()
    ac.run()



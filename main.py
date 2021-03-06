#!/usr/bin/env/python

import time
import ConfigParser
from DoorController import DoorController as dc
from TinyDBConnector import TinyDBConnector as tdb
from LogAndPBMessager import LogAndPBMessager as logger
from TidyHQController import TidyHQController

config_filename = 'config.cfg'

class AccessController():
    def __init__(self):
        self.last_tag_scanned = 0
        self.tag_scan_count = 0
        self.tag_scan_repeat_message = 3
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
        self.db_reload_interval_seconds = self.config.getint('TidyHQ', 'update_interval_sec')
        # IMPORTANT - Make sure you run this on a server with a password only you know!
        # As it's saved in plain text :/
        self.tidy_password = self.config.get('TidyHQ', 'password')
        log_filename = self.config.get('Logging', 'filename')
        log_filesize = self.config.get('Logging', 'size_bytes')
        log_backup_count = self.config.get('Logging', 'backup_count')
        debug_nopigpio = self.config.getboolean('Debug', 'nopigpio')
        self.config.getint('TidyHQ','update_interval_sec')

        # LOGGING AND PUSHBULLET FOR MESSAGES
        self.log = logger(pb_token, pb_channel, log_filename, log_filesize, log_backup_count)

        # DOOR CONTROLLER
        self.dc = dc(nopigpio=debug_nopigpio)
        self.dc.set_tag_scanned_callback(self.tag_scanned)
        self.dc.set_alarm_sounding_callback(self.alarm_sounding)
        self.dc.set_alarm_armed_callback(self.alarm_armed)

        # TINYDB
        self.tinydb = tdb(db_loc)

        # TIDYHQ
        self.tidyhq = TidyHQController(tidy_client_id, tidy_client_secret, tidy_member_group, tidy_domain_prefix)


    def open_door(self, contact_name):
        self.tag_scan_count = 0
        self.dc.unlock_door()
        self.log.new_occupant(contact_name)


    def tag_scanned(self, bits, rfid):

        self.log.info("Tag scanned: " + str(rfid))

        contact, is_allowed = self.tinydb.is_allowed(rfid)
        contact_name = "Unknown"

        if contact is not None:
            contact_name = contact['first_name'] + " " + contact['last_name']
            info_str = "Contact found: " + contact_name

            if is_allowed is True:
                info_str += " - allowed."
            else:
                info_str += " - not allowed."
            self.log.info(info_str)

            if is_allowed: self.open_door(contact_name)
        else:
            self.log.info("Unknown ID.")

        if not is_allowed:
            self.log.invalid_tag_retries(rfid, contact_name)

            # Cheack for repeat scans
            if(rfid == self.last_tag_scanned):
                self.tag_scan_count += 1
                if(self.tag_scan_count >= self.tag_scan_repeat_message):
                    self.log.invalid_tag_retries(rfid, contact_name)
            else:
                self.tag_scan_count = 0
            self.last_tag_scanned = rfid

    def alarm_sounding(self):
        self.log.alarm_sounding()
        pass

    def reload_db(self, show_info=False):
        self.tidyhq.connect_to_api(self.tidy_username, self.tidy_password)
        if self.tidyhq.reload_db(self.tinydb.userdb) is False:
            self.log.error("DB update failed!")
        else:
            if show_info is True:
                self.log.info("DB update complete.")

    def alarm_armed(self):
        self.log.alarm_armed()

    def run(self):
        self.reload_db(True)
        self.log.info("Start-up complete.")

        while True:
            time.sleep(1)
            self.db_reload_seconds += 1
            if(self.db_reload_seconds > self.db_reload_interval_seconds):
                self.db_reload_seconds = 0
                self.reload_db(False)

        #TODO: handle on exit.. self.dc.on_end()

if __name__ == '__main__':
    ac = AccessController()
    ac.run()
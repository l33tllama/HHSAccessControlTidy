from PushbulletMessager import PushbulletMessager
from pushbullet import PushBullet
import logging, logging.handlers
from time import gmtime, strftime

class PushbulletMessager():
    def __init__(self, api_token, channel_name):
        self.pb = PushBullet(api_token)
        self.channel = self.pb.channels[0]
        channel_found = False
        for channel in self.pb.channels:
            if channel.name == channel_name:
                channel_found = True
                self.channel = channel
        if not channel_found:
            print("Channel: " + channel_name + " not found.")

    def _get_time(self):
        return strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

    def test_message(self, message):
        self.channel.push_note("HHS Test Message", message)

    def new_occupant(self, member):
        self.channel.push_note("HHS New Occupant", member + " entered at " + self._get_time())
        pass

    def invalid_tag_attempts(self, tag_id, member):
        self.channel.push_note("HHS repeat tag fail", "Tag ID: " + str(tag_id) + " name: " + member)
        pass

    def alarm_armed(self, last_entrant):
        self.channel.push_note("HHS Alarm Armed", "Alarm armed at " + self._get_time() + " last occupant scanned: "
                               + last_entrant)
        pass

    def alarm_sounding(self):
        self.channel.push_note("ALARM! at HHS", "Alarm is currently sounding. Might want to check it out.")

class access_logger():
    def __init__(self, log_filename, log_filesize, log_backup_count):
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

    def new_occupant(self, member):
        self.entrant_logger.info(member + " entered the building.")

    def invalid_tag(self, rfid, member):
        self.entrant_logger.info("Invalid tag scanned: " + str(rfid) + " member?: " + member)

    def invalid_tag_retries(self, rfid, member):
        self.entrant_logger.info("Multiple invalid tag attempts, notifying via Pushbullet..")

    def alarm_armed(self):
        self.entrant_logger.info("Alarm armed.")

    def alarm_sounding(self):
        self.entrant_logger.error("Alarm has been triggered and is sounding!!")

    def log(self, message):
        self.entrant_logger.log(message)

class LogAndPBMessager():
    def __init__(self, pb_token, pb_channel, log_filename, log_filesize, log_backup_count):
        self.pb = PushbulletMessager(pb_token, pb_channel)
        self.logger = access_logger(log_filename, log_filesize, log_backup_count)
        self.last_occupant = "No-one"
        pass

    def new_occupant(self, member):
        self.pb.new_occupant(member)
        self.logger.new_occupant(member)
        self.last_occupant = member
        pass

    def invalid_tag(self, rfid_tag, member):
        self.logger.invalid_tag(rfid_tag, member)
        pass

    def invalid_tag_retries(self, rfid_tag, member):
        self.logger.invalid_tag_retries(rfid_tag, member)
        self.pb.invalid_tag_attempts(rfid_tag, member)
        pass

    def alarm_armed(self):
        self.logger.alarm_armed()
        self.pb.alarm_armed(self.last_occupant)
        pass

    def alarm_sounding(self):
        self.logger.alarm_sounding()
        self.pb.alarm_sounding()
        pass

    def log(self, message):
        self.logger.log(message)
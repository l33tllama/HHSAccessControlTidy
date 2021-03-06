from pushbullet import PushBullet
import logging, logging.handlers
import threading
from time import localtime, strftime, sleep
from requests import ConnectionError
import OpenSSL

class PushbulletMessenger(object):
    def __init__(self, api_token, channel_name):

        self.channel_name = channel_name
        self.api_token = api_token
        self.pb_connected = False

        try:
            self.pb = PushBullet(self.api_token)
        except ConnectionError as e:
            #print "Retrying PB loop"
            print "PB connection error - not connecting today.."
            #TODO: figure out how to get PB to reconnect - thread isn't working!
            #self.retry_connect_pushbullet()
        else:
            print "PB connected"
            self.pb_connected = False
            self.setup_pb()

        self.pending_messages = []

        thread = threading.Thread(target=self.message_loop, args=())
        thread.daemon = True
        thread.start()
        self._send('HHS Access Start-up', 'Yep, I\'m working.')

    # on successful connect, setup PB
    def setup_pb(self):
        self.channel = self.pb.channels[0]
        channel_found = False
        for channel in self.pb.channels:
            if channel.name == self.channel_name:
                channel_found = True
                self.channel = channel
                print("Channel " + self.channel_name + " found")
        if not channel_found:
            print("Channel: " + self.channel_name + " not found.")

    # try to send messages
    def message_loop(self):
        while True:
            if self.pb_connected:
                if len(self.pending_messages) > 0:
                    backup = (title, content) = self.pending_messages.pop()
                    try:
                        self.channel.push_note(title, content)
                    except ConnectionError as e:
                        print("Error sending message, trying again..")
                        self.pending_messages.append(backup)
                    except OpenSSL.SSL.SysCallError as e:
                        self.pending_messages.append(backup)
            sleep(2)

    # retry PB in a thread..
    def retry_pb_thread(self):
        while not self.pb_connected:
            try:
                self.pb = PushBullet(self.api_token)
            except ConnectionError as e:
                print "PB connection error"
                self.error("PB Connection error")
            else:
                print "PB connected now"
                self.pb_connected = True
                self.setup_pb()
                #self._send('PB connected after error..')

            sleep(2)

    # Start thread to retry PB connection
    def retry_connect_pushbullet(self):
        thread = threading.Thread(target=self.retry_pb_thread, args=())
        thread.daemon = True
        thread.start()

    def _send(self, title, content):
        self.pending_messages.append((title, content))

    def _get_time(self):
        return strftime("%a, %d %b %Y %H:%M:%S", localtime())

    def test_message(self, message):
        self._send("HHS Test Message", message)

    def new_occupant(self, member):
        self._send("HHS New Occupant", member + " entered at " + self._get_time())

    def invalid_tag_attempts(self, tag_id, member):
        self._send("HHS repeat tag fail", "Tag ID: " + str(tag_id) + " name: " + member)

    def alarm_armed(self, last_entrant):
        self._send("HHS Alarm Armed", "Alarm armed at " + self._get_time() + " last occupant scanned: "
                               + last_entrant)

    def alarm_sounding(self):
        self._send("ALARM! at HHS", "Alarm is currently sounding. Might want to check it out.")

    def error(self, message):
        self._send("HHS Access ERROR", message)

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

    def info(self, message):
        self.entrant_logger.info(message)

    def error(self, message):
        self.entrant_logger.error(message)

class LogAndPBMessager():
    def __init__(self, pb_token, pb_channel, log_filename, log_filesize, log_backup_count):
        self.pb = PushbulletMessenger(pb_token, pb_channel)
        self.logger = access_logger(log_filename, log_filesize, log_backup_count)
        self.last_occupant = "No-one"

    def new_occupant(self, member):
        self.pb.new_occupant(member)
        self.logger.new_occupant(member)
        self.last_occupant = member

    def invalid_tag(self, rfid_tag, member):
        self.logger.invalid_tag(rfid_tag, member)

    def invalid_tag_retries(self, rfid_tag, member):
        self.logger.invalid_tag_retries(rfid_tag, member)
        self.pb.invalid_tag_attempts(rfid_tag, member)

    def alarm_armed(self):
        self.logger.alarm_armed()
        self.pb.alarm_armed(self.last_occupant)

    def alarm_sounding(self):
        self.logger.alarm_sounding()
        self.pb.alarm_sounding()

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)
        self.pb.error(message)
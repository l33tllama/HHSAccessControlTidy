from pushbullet import PushBullet

class PushbulletMessager():
    def __init__(self, api_token, channel_name):
        self.pb = PushBullet(api_token)
        self.channel = self.pb.channels[0]
        for channel in self.pb.channels:
            if channel.name == channel_name:
                print ("Channel found! " + channel.name)
                self.channel = channel

    def test_message(self, message):
        self.channel.push_note("HHS Test Message", message)

    def new_occupant(self, member):
        self.channel.push_note("HHS Member Entered", member)
        pass

    def invalid_tag_attempts(self, tag_id, member):
        self.channel.push_note("HHS repeat tag fail", "Tag ID: " + str(tag_id) + " name: " + member)
        pass

    def message_alarm_armed(self):
        self.channel.push_note("HHS Alarm Armed", "")
        pass


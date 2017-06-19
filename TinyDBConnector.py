from tinydb import TinyDB, Query

class TinyDBConnector:
    def __init__(self, database_file):
        self.userdb = TinyDB(database_file)
        pass

    def is_allowed(self, rfid):
        User = Query()
        rfid_match = False
        rfid_contact_found = None
        rfid_contacts = self.userdb.search(User['custom_fields'] != None)
        #TODO: error handling
        for rfid_contact in rfid_contacts:
            for custom_field in rfid_contact['custom_fields']:
                if custom_field['title'] == 'RFID Tag':
                    if custom_field['value'] == str(rfid):
                        rfid_match = True
                        rfid_contact_found = rfid_contact
                    #print "Tag id: " + custom_field['value'] + " name: " + rfid_contact['first_name'] + " " + rfid_contact['last_name'] + " Tag state: " + rfid_contact['membership_state']

        if rfid_match is True:
            temp_member = False
            # Check for temp member field (temp hack..)
            for custom_field in rfid_contact_found['custom_fields']:
                if custom_field['title'] == 'temporary_member':
                    if custom_field['value'] == 'true':
                        temp_member = True
                        print "Temp member allowed"
            if rfid_contact_found['membership_state'] == 'activated':
                return (rfid_contact_found, True)
            else:
                if temp_member is True:
                    return (rfid_contact_found, True)

                return (rfid_contact_found, False)
        else:
            return (None, False)
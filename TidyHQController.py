from TidyHQOAuthWrapper import TidyHQOAuthWrapper
import json
from tinydb import TinyDB, Query

def insert_membership_state(state):
    def transform(element):
        element["membership_state"] = state
    return transform

# Controller for TidyHQ
# - Used mainly to dump contacts database to local TinyDB database
class TidyHQController():

    def __init__(self, client_id, client_secret, member_group_id, domain_prefix):
        self.member_group_id = member_group_id
        self.oauth = TidyHQOAuthWrapper(client_id=client_id, client_secret=client_secret, domain_prefix=domain_prefix)
        self.authenticated = False

    def connect_to_api(self, username, password):
        self.authenticated = self.oauth.request_api_access_pw(username, password)

    # Get the latest contacts list
    def reload_db(self, tinydb):
        if not self.authenticated:
            print("Not authenticated! Can't sync DB.")
            return False
        contacts = self.oauth.get_contacts_in_group(self.member_group_id)
        memberships = self.oauth.get_memberships()
        if contacts is False or memberships is False:
            print("Error getting data from TidyHQ!")
            return False

        # clear DB
        tinydb.purge()
        User = Query()
        for contact in contacts:
            # TODO: remove sensitive info (address, phone, etc) - otherwise saved in json file
            # insert contact to TInuyDB
            tinydb.insert(contact)
            contact_id = contact["id"]

            # look through members in membership list and add 'membership_state'
            # into contacts list
            for membership in memberships:
                if membership["contact_id"] == contact_id:
                    membership_state = membership["state"]
                    #print("Inserting state: " + membership_state)
                    tinydb.update(insert_membership_state(membership_state),
                                  User["id"] == contact_id)
                    #print(tinydb.search(User["id"] == contact_id))
        return True


    def dump_to_tinydb(self, tinydb):
        pass
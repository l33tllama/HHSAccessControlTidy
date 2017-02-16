'''
'Wrapper' for TidyHQ's Oauth2 API
- Basic CURL calls to get HTTPS data
-
'''
import pycurl

from StringIO import StringIO
from urllib import urlencode
import json

class TidyHQOAuthWrapper():

    def __init__(self, client_id, client_secret, domain_prefix):
        self.access_token = ''
        self.client_id = client_id
        self.client_secret = client_secret
        self.domain_prefix = domain_prefix
        self.authenticated = False

    def generic_fail_cb(self, message):
        print(message)

    # Request access to API before sending CURL GETs for specific data
    def request_api_access_pw(self, username, password, on_fail_cb=None):
        buffer = StringIO()
        cr = pycurl.Curl()
        if on_fail_cb is None:
            on_fail_cb = self.generic_fail_cb
        cr.setopt(cr.URL, 'https://accounts.tidyhq.com/oauth/token')
        cr.setopt(cr.WRITEFUNCTION, buffer.write)
        post_data = {   'domain_prefix' : self.domain_prefix,
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                        'redirect_uri': 'https://tidyhq.com',
                        'username' : username,
                        'password' : password,
                        'grant_type': 'password'}
        postfields = urlencode(post_data)
        cr.setopt(cr.POSTFIELDS, postfields)

        try:
            cr.perform()
        except pycurl.error, error:
            if callable(on_fail_cb):
                errno, errstr = error
                on_fail_cb('CURL error ' + errstr)
            return False
        finally:
            cr.close()

        body = buffer.getvalue()
        body_json = {}
        try:
            body_json = json.loads(body)
        except ValueError:
            if callable(on_fail_cb):
                on_fail_cb("No JSON object returned from CURl request.")
            return False
        try:
            self.access_token = body_json['access_token']
            self.authenticated = True
        except KeyError:
            on_fail_cb("No key 'access_token' in JSON repsonse.")
        return self.authenticated

    # Generic CURL GET, programmatic version of 'curl url'
    def curl_get(self, request, fields=None):
        if not self.authenticated:
            print ("Not authenticated! Cannot continue.")
            return False
        on_fail_cb = self.generic_fail_cb
        buffer = StringIO()
        cr = pycurl.Curl()
        cr.setopt(cr.URL, 'https://api.tidyhq.com/v1/' + request)
        cr.setopt(cr.WRITEFUNCTION, buffer.write)

        # Add URI fields if specified
        if fields is not None:
            post_data = fields
            postfields = urlencode(post_data)
            cr.setopt(cr.POSTFIELDS, postfields)
        cr.setopt(cr.HTTPHEADER, ["Authorization: Bearer " + str(self.access_token)])
        try:
            cr.perform()
        except pycurl.error, error:
            on_fail_cb('CURL error: ' + error)
            return False
        finally:
            cr.close()

        body = buffer.getvalue()
        try:
            body_json = json.loads(body)
        except ValueError:
            on_fail_cb("JSON decode error on CURL GET " + request)
            return False
        return body_json

    def get_contacts(self):
        contacts = self.curl_get('contacts')
        return contacts

    def get_memberships(self):
        memberships = self.curl_get('memberships')
        return memberships

    def get_contacts_in_group(self, group_id):
        contacts = self.curl_get('groups/' + group_id + '/contacts')
        return contacts

    def get_contact_memberships(self, contact_id):
        contact_memberships = self.curl_get('contacts/:' + contact_id + '/memberships')
        return contact_memberships

    # OLD - for web interface method
    def request_api_access(self, auth_token):
        buffer = StringIO()
        cr = pycurl.Curl()
        self.access_token = auth_token
        cr.setopt(cr.URL, 'https://accounts.tidyhq.com/oauth/token')
        cr.setopt(cr.WRITEFUNCTION, buffer.write)
        post_data = {'client_id': self.client_id,
                     'client_secret': self.client_secret,
                     'redirect_uri': 'https://tidyhq.com',
                     'code': auth_token,
                     'grant_type': 'authorization_code'}
        postfields = urlencode(post_data)
        cr.setopt(cr.POSTFIELDS, postfields)
        cr.perform()
        cr.close()
        body = buffer.getvalue()
        print(body)

    # Not needed?
    def connect_app(self):
        buffer = StringIO()
        hbuff = StringIO()
        cr = pycurl.Curl()
        cr.setopt(cr.URL, 'https://accounts.tidyhq.com/oauth/authorize')
        cr.setopt(cr.WRITEFUNCTION, buffer.write)
        cr.setopt(cr.HEADERFUNCTION, hbuff.write)
        cr.setopt(cr.FOLLOWLOCATION, True)
        cr.setopt(cr.CONNECTTIMEOUT, 30)
        cr.setopt(cr.AUTOREFERER, 1)
        cr.setopt(cr.FOLLOWLOCATION, 1)
        cr.setopt(cr.COOKIEFILE, '')
        cr.setopt(cr.TIMEOUT, 30)
        cr.setopt(cr.USERAGENT, '')
        post_data = {'domain_prefix': self.domain_prefix,
                     'client_id' : self.client_id,
                     'redirect_uri': 'https://tidyhq.com',
                     'response_type': 'code'}
        postfields = urlencode(post_data)
        cr.setopt(cr.POSTFIELDS, postfields)
        cr.perform()
        cr.close()

        hbuff.seek(0)
        location = ""

        for l in hbuff:
            if "Location" in l:
                location = l.split(": ")[-1]

        print location

import facebook
import urllib
from urllib.parse import urlencode
import subprocess
import collections
import sys
import time
import sqlite3 as lite
from utils import url_to_json

def read_token():
    try:
        with open("user.settings", "r") as access_token:
            ACCESS_TOKEN = access_token.read().split()[0]
    except:
        print("Please put your access token in user.settings file (see README.md)")
        raise
    return ACCESS_TOKEN


def find_contact(options, inbox, USER_ID, interlocutor_limit=2):
    while(True):
        for conversation_list in inbox['data']:
            to = conversation_list['to']['data']
            if len(to) <= interlocutor_limit and len(to) > 1:
                interlocutor = to[0] if to[1]['id'] == USER_ID else to[1]
                if interlocutor['name'] == options.contact:
                    return interlocutor
        if not 'paging' in inbox.keys() or not 'next' in inbox['paging'].keys():
            print("Contact not found.")
            sys.exit(1)
        time.sleep(options.s)
        inbox = url_to_json(inbox['paging']['next'])

def has_reached_end(options, cursor, interlocutor_id):
   stats = cursor.execute("SELECT updated_time, reached_end \
           FROM Retrieving_stats \
           JOIN Interlocutors ON Interlocutors.id=contact_id \
           WHERE contact_id='{}'".format(interlocutor_id)).fetchone()
   return (stats and stats[1] == 1)


def has_n_messages(options, cursor, interlocutor_id):
   msgs = cursor.execute("SELECT name, count(sender_id) \
               FROM Messages \
               JOIN Interlocutors ON Interlocutors.id=sender_id \
               WHERE sender_id='{}' \
               GROUP BY sender_id;".format(interlocutor_id)).fetchone()
   return (msgs and options.n and msgs[1] >= options.n)

def handle_interlocutor(options, cursor, contacts, interlocutor):
    if has_n_messages(options, cursor, interlocutor['id']):
        if options.debug:
            print("Did not add %s: too much messages" % (interlocutor['name']))
    elif options.new and has_reached_end(options, cursor, interlocutor['id']):
        if options.debug:
            print("Did not add %s: reached end" % (interlocutor['name']))
    else:
        if options.debug:
            print("Add %s" % interlocutor['name'])
        n_contact = len(contacts)
        contacts.update({n_contact : interlocutor})
    return contacts

def pull_contact_list(options, inbox, USER_ID, n_interlocutor=2):
    try:
        con = lite.connect("user.db")
        cursor = con.cursor()
    except lite.Error as e:
        print("Error: %s" % e.args[0])
        raise

    contacts = collections.OrderedDict()
    for i in range(options.l):
        for conversation_list in inbox['data']:
            to = conversation_list['to']['data']
            if len(to) <= n_interlocutor and len(to) > 1:
                contacts = handle_interlocutor(options, cursor, contacts,
                    to[0] if to[1]['id'] == USER_ID else to[1])

        # End of inbox
        if not 'paging' in inbox.keys() or not 'next' in inbox['paging'].keys():
            con.close()
            return contacts

        time.sleep(options.s)
        inbox = url_to_json(inbox['paging']['next'])
    con.close()
    return contacts

# This is not used, but should be, actually.
'''
def normal_way_to_get_token():
    FACEBOOK_APP_ID     = 'XXXXXXXXXXXXXXX'
    FACEBOOK_APP_SECRET = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    FACEBOOK_PROFILE_ID = 'XXXXXX'

    oauth_args = dict(client_id     = FACEBOOK_APP_ID,
            client_secret = FACEBOOK_APP_SECRET,
            grant_type    = 'client_credentials')
    oauth_curl_cmd = ['curl', 'https://graph.facebook.com/oauth/access_token?' + \
            urlencode(oauth_args)]
    oauth_response = subprocess.Popen(oauth_curl_cmd,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE).communicate()[0]

    try:
        ACCESS_TOKEN = urllib.parse.parse_qs(str(oauth_response))['access_token'][0]
    except KeyError:
        print('Unable to grab an access token!')
        exit(1)
'''

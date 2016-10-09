#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class KeyEntfernen(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Die ID der zu löschenden Instanz holen
        key = self.request.get('key')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
            # Schlüsselpaar löschen
            conn_region.delete_key_pair(key)
        except EC2ResponseError:
            # Wenn es nicht geklappt hat...
            fehlermeldung = "104"
            self.redirect('/schluessel?mobile='+str(mobile)+'&message='+fehlermeldung)
        except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            fehlermeldung = "8"
            self.redirect('/schluessel?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
            # Wenn es geklappt hat...
            fehlermeldung = "103"
            self.redirect('/schluessel?mobile='+str(mobile)+'&message='+fehlermeldung)


#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class SnapshotsErzeugenDefinitiv(webapp.RequestHandler):
    def post(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Name Volume holen, von dem ein Snapshot erzeugt werden soll
        volume = self.request.get('volume')
        # Die Beschreibung des Snapshots holen
        beschreibung = self.request.get('beschreibung')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        # Wenn die Variable "beschreibung" nicht gesetzt wurde,
        # dann wird sie als leere Variable erzeugt
        if not beschreibung: beschreibung = ''

        try:
            # Snapshot erzeugen
            conn_region.create_snapshot(volume, description=beschreibung)
        except EC2ResponseError:
            # Wenn es nicht klappt...
            fehlermeldung = "14"
            self.redirect('/snapshots?mobile='+str(mobile)+'&message='+fehlermeldung)
        except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            fehlermeldung = "8"
            self.redirect('/snapshots?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
            # Wenn es geklappt hat...
            fehlermeldung = "13"
            self.redirect('/snapshots?mobile='+str(mobile)+'&message='+fehlermeldung)
            
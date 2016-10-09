#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class SnapshotsEntfernen(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Name des zu löschenden Snapshots holen
        snapshot = self.request.get('snapshot')        
        # War es die Liste aller AMIs oder nur der eigenen AMIs
        ami = self.request.get('ami')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        if ami == "own":
          try:
              # Snapshot löschen
              conn_region.delete_snapshot(snapshot)
          except EC2ResponseError:
              # Wenn es nicht klappt...
              fehlermeldung = "12"
              self.redirect('/snapshots?mobile='+str(mobile)+'&message='+fehlermeldung)
          except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              fehlermeldung = "8"
              self.redirect('/snapshots?mobile='+str(mobile)+'&message='+fehlermeldung)
          else:
              # Wenn es geklappt hat...
              fehlermeldung = "11"
              self.redirect('/snapshots?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          # ami == "all"
          try:
              # Snapshot löschen
              conn_region.delete_snapshot(snapshot)
          except EC2ResponseError:
              # Wenn es nicht klappt...
              fehlermeldung = "12"
              self.redirect('/snapshots_amazon_all?mobile='+str(mobile)+'&message='+fehlermeldung)
          except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              fehlermeldung = "8"
              self.redirect('/snapshots_amazon_all?mobile='+str(mobile)+'&message='+fehlermeldung)
          else:
              # Wenn es geklappt hat...
              fehlermeldung = "11"
              self.redirect('/snapshots_amazon_all?mobile='+str(mobile)+'&message='+fehlermeldung)

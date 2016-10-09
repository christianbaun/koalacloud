#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class VolumesEntfernen(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Name des zu löschenden Volumes holen
        volume = self.request.get('volume')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Volume löschen
          conn_region.delete_volume(volume)
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "19"
          self.redirect('/volumes?mobile='+str(mobile)+'&message='+fehlermeldung) 
        except DownloadError:
          # Wenn es nicht klappt...
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/volumes?mobile='+str(mobile)+'&message='+fehlermeldung) 
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "22"
          self.redirect('/volumes?mobile='+str(mobile)+'&message='+fehlermeldung) 

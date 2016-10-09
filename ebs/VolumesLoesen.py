#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class VolumesLoesen(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Name des zu lösenden Volumes holen
        # Name of the volume that has to be detached
        volume = self.request.get('volume')
        # Den Usernamen erfahren
        # Get the username
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Volume entkoppeln
          conn_region.detach_volume(volume)
        except EC2ResponseError:
          # Wenn es nicht klappt...
          # If it didn't work to detach the volume...
          fehlermeldung = "20"
          self.redirect('/volumes?mobile='+str(mobile)+'&message='+fehlermeldung) 
        except DownloadError:
          # Wenn es nicht klappt...
          # If it didn't work to detach the volume...
          # Diese Exception hilft gegen diese beiden Fehler:
          # This exception helps against this two errors:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/volumes?mobile='+str(mobile)+'&message='+fehlermeldung) 
        else:
          # Wenn es geklappt hat...
          # If it worked...
          fehlermeldung = "24"
          self.redirect('/volumes?mobile='+str(mobile)+'&message='+fehlermeldung) 

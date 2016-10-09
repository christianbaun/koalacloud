#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class VolumeDefinitivAnhaengen(webapp.RequestHandler):
    def post(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Name des anzuhängenden Volumes holen
        volume = self.request.get('volume')
        # Instanz-ID holen
        instance_id = self.request.get('instanzen')
        # Device holen
        device = self.request.get('device')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Volume anhaengen
          neues_volume = conn_region.attach_volume(volume, instance_id, device)
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "21"
          self.redirect('/volumes?mobile='+str(mobile)+'&message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/volumes?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "23"
          self.redirect('/volumes?mobile='+str(mobile)+'&message='+fehlermeldung)
          
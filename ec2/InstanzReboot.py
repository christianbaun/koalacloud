#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class InstanzReboot(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Die ID der neuzustartenden Instanz holen
        id = self.request.get('id')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        # Es muss eine Liste mit den IDs übergeben werden
        instance_ids = [id]

        try:
          # Instanz beenden
          conn_region.reboot_instances(instance_ids)
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "80"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "79"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)

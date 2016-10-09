#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class AlleVolumesLoeschenDefinitiv(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Liste mit den Volumes
          liste_volumes = conn_region.get_all_volumes()
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "10"
          self.redirect('/volumes?mobile='+str(mobile)+'&message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/volumes?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          # Anzahl der Volumes in der Liste
          laenge_liste_volumes = len(liste_volumes)
          for i in range(laenge_liste_volumes):
                try:
                  # Volume entfernen
                  conn_region.delete_volume(liste_volumes[i].id)
                except EC2ResponseError:
                  # Wenn es nicht klappt...
                  fehlermeldung = "26"
                  self.redirect('/volumes?mobile='+str(mobile)+'&message='+fehlermeldung)
                except DownloadError:
                  # Diese Exception hilft gegen diese beiden Fehler:
                  # DownloadError: ApplicationError: 2 timed out
                  # DownloadError: ApplicationError: 5
                  fehlermeldung = "8"
                  self.redirect('/volumes?mobile='+str(mobile)+'&message='+fehlermeldung)

          fehlermeldung = "27"
          self.redirect('/volumes?mobile='+str(mobile)+'&message='+fehlermeldung)

#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class AlleInstanzenBeenden(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Liste der Instanzen holen
          instances = conn_region.get_all_instances()
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "10"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          for reserv in instances:
            for inst in reserv.instances:
              # Wenn die Instanz schon im Zustand "terminated" ist, dann kann man sie nicht mehr beenden
              if inst.state != u'terminated':

                try:
                  # Instanz beenden
                  #inst.stop()
                  inst.terminate()
                except EC2ResponseError:
                  # Wenn es nicht klappt...
                  fehlermeldung = "82"
                  self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
                except DownloadError:
                  # Diese Exception hilft gegen diese beiden Fehler:
                  # DownloadError: ApplicationError: 2 timed out
                  # DownloadError: ApplicationError: 5
                  fehlermeldung = "8"
                  self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)

          fehlermeldung = "81"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)

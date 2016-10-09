#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class InstanzTerminate(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Die ID der zu terminierenden Instanz holen
        id = self.request.get('id')
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
          fehlermeldung = "9"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...

          # Mit dieser Variable wird überprüft, ob die Instanz gleich gefunden wird
          # Wenn die Instanz nicht gefunden wird, braucht auch nichts terminiert zu werden
          gefunden = 0
          for reserv in instances:
              for inst in reserv.instances:
                  # Vergleichen
                  if str(inst.id) == id:
                      # Die Instanz wurde gefunden!
                      gefunden = 1

                      # Wenn die Instanz schon im Zustand "terminated" ist,
                      # kann man sie nicht mehr terminieren
                      if inst.state == u'terminated':
                        fehlermeldung = "76"
                        self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
                      else:
                        try:
                          # Instanz terminieren
                          inst.terminate()
                        except EC2ResponseError:
                          # Wenn es nicht klappt...
                          fehlermeldung = "74"
                          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
                        except DownloadError:
                          # Diese Exception hilft gegen diese beiden Fehler:
                          # DownloadError: ApplicationError: 2 timed out
                          # DownloadError: ApplicationError: 5
                          fehlermeldung = "8"
                          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
                        else:
                          # Wenn es geklappt hat...
                          fehlermeldung = "73"
                          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)

          # Wenn die Instanz nicht gefunden werden konnte
          if gefunden == 0:
            fehlermeldung = "75"
            self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
            
#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import loginelb

class LoadBalancer_Zone_Zuordnen(webapp.RequestHandler):
    def post(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # self.response.out.write('posted!')
        # Zu verknüpfenden Load Balancer holen
        loadbalancer = self.request.get('loadbalancer')
        # Zu verknüpfende Zone holen
        zone = self.request.get('zonen')
        # Den Usernamen erfahren
        username = users.get_current_user()

        # Mit ELB verbinden
        conn_elb = loginelb(username)

        # Eine leere Liste für die Zonen erzeugen
        list_of_zones = []
        # Die Zone in Liste einfügen
        list_of_zones.append(zone)

        try:
          # Die Instanz verknüpfen
          conn_elb.enable_availability_zones(loadbalancer, list_of_zones)
        except EC2ResponseError:
          # Wenn es nicht geklappt hat...
          fehlermeldung = "69"
          self.redirect('/loadbalanceraendern?mobile='+str(mobile)+'&name='+loadbalancer+'&message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/loadbalanceraendern?mobile='+str(mobile)+'&name='+loadbalancer+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "68"
          self.redirect('/loadbalanceraendern?mobile='+str(mobile)+'&name='+loadbalancer+'&message='+fehlermeldung)
          
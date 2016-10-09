#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import loginelb
from library import login

class DeleteLoadBalancer(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Name des zu löschenden Load Balancers holen
        name = self.request.get('name')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)
        # Mit ELB verbinden
        conn_elb = loginelb(username)

        try:
          # Volume löschen
          conn_elb.delete_load_balancer(name)
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "71"
          self.redirect('/loadbalancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/loadbalancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "70"
          self.redirect('/loadbalancer?mobile='+str(mobile)+'&message='+fehlermeldung)
          
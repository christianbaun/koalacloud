#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class Disassociate_IP(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Zu enfelchtende (disassociate) Elastic IP-Adresse holen
        address = self.request.get('address')
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        try:
          # Die Elastic IP-Adresse freigeben (löschen)
          conn_region.disassociate_address(address)
        except EC2ResponseError:
          # Wenn es nicht geklappt hat...
          fehlermeldung = "2"
          self.redirect('/elastic_ips?mobile='+str(mobile)+'&message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/elastic_ips?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "3"
          self.redirect('/elastic_ips?mobile='+str(mobile)+'&message='+fehlermeldung)
          
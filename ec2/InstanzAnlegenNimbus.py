#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class InstanzAnlegenNimbus(webapp.RequestHandler):
    def post(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        #self.response.out.write('posted!')
        image_manifest = self.request.get('image_manifest')
        image_id = self.request.get('image_id')
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')

        conn_region, regionname = login(username)

        try:
          # Instanz(en) anlegen
          reservation = conn_region.run_instances(image_id)
        except EC2ResponseError:
          # Wenn es nicht geklappt hat
          fehlermeldung = "78"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat
          fehlermeldung = "77"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)



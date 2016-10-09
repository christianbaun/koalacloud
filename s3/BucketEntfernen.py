#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import logins3

class BucketEntfernen(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        #self.response.out.write('posted!')
        # Den Namen des zu löschen Buckets holen
        bucketname = self.request.get('bucket')

        # Den Usernamen erfahren
        username = users.get_current_user()

        # Mit S3 verbinden
        conn_s3 = logins3(username)
        try:
          # Versuch den Bucket zu löschen
          conn_s3.delete_bucket(bucketname)
        except:
          fehlermeldung = "109"
          # Wenn es nicht klappt...
          self.redirect('/s3?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          fehlermeldung = "110"
          # Wenn es geklappt hat...
          self.redirect('/s3?mobile='+str(mobile)+'&message='+fehlermeldung)
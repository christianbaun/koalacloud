#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import logins3

from boto.ec2.connection import *

class ACL_Aendern(webapp.RequestHandler):
    def post(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Zum Testen, ob "post" funktioniert hat
        # self.response.out.write('posted!')
        keyname    = self.request.get('keyname')
        bucketname = self.request.get('bucketname')
        canned_acl = self.request.get('canned_acl')
        typ        = self.request.get('typ')
        directory  = self.request.get('dir')

        # Den Usernamen erfahren
        username = users.get_current_user()

        # Mit S3 verbinden
        conn_s3 = logins3(username)
        # Mit dem Bucket verbinden
        bucket_instance = conn_s3.get_bucket(bucketname)

        try:
          # Access Control List (ACL) setzen
          bucket_instance.set_acl(canned_acl, key_name=keyname)
        except EC2ResponseError:
          # Wenn es nicht klappt...
          fehlermeldung = "119"
          if typ == "pur":
            self.redirect('/bucket_inhalt_pure?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)
          else:
            if directory == "/":
              self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)
            else:
              directory = str(directory)[:-1]
              self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&dir='+directory+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "118"
          if typ == "pur":
            self.redirect('/bucket_inhalt_pure?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)
          else:
            if directory == "/":
              self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)
            else:
              directory = str(directory)[:-1]
              self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&dir='+directory+'&message='+fehlermeldung)

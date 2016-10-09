#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import logins3
from library import login

class AlleKeysLoeschenDefinitiv(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Den Usernamen erfahren
        username = users.get_current_user()
        # Den Namen des Buckets erfahren
        bucketname = self.request.get('bucket')
        # Die S3-Ansicht (pur oder Komfort) erfahren
        s3_ansicht = self.request.get('s3_ansicht')

        conn_region, regionname = login(username)

        # Mit S3 verbinden
        conn_s3 = logins3(username)
        bucket_instance = conn_s3.get_bucket(bucketname)

        liste_keys = bucket_instance.get_all_keys()
        # Anzahl der Keys in der Liste
        laenge_liste_keys = len(liste_keys)

        # Wenn wir in einer Eucalyputs-Infrastruktur sind, dann muss dieser
        # dämliche None-Eintrag weg
        if regionname != "Amazon":
          liste_keys2 = []
          for i in range(laenge_liste_keys):
            if str(liste_keys[i].name) != 'None':
              liste_keys2.append(liste_keys[i])
          laenge_liste_keys2 = len(liste_keys2)
          laenge_liste_keys = laenge_liste_keys2
          liste_keys = liste_keys2


        try:
          for i in range(laenge_liste_keys):
            # Versuch den Key zu löschen
            liste_keys[i].delete()
        except:
          # Wenn es nicht klappt...
          fehlermeldung = "121"
          self.redirect('/bucket_inhalt_pure?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat...
          fehlermeldung = "120"
          self.redirect('/bucket_inhalt_pure?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)

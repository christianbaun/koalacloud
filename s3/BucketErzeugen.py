#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import re

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import logins3

class BucketErzeugen(webapp.RequestHandler):
    def post(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # self.response.out.write('posted!')
        # Die Eingabe aus dem Formular holen
        neuerbucketname = self.request.get('bucketname')

        # Den Usernamen erfahren
        username = users.get_current_user()

        if neuerbucketname == "":
          # Testen ob ein Name für den neuen key angegeben wurde
          # Wenn kein Name angegeben wurde, kann kein Key angelegt werden
          #fehlermeldung = "Sie haben keine Namen angegeben"
          fehlermeldung = "92"
          self.redirect('/s3?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif re.search(r'[^\-.a-zA-Z0-9]', neuerbucketname) != None:
          # Testen ob der Name für den neuen key nicht erlaubte Zeichen enthält
          fehlermeldung = "106"
          self.redirect('/s3?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          # Mit S3 verbinden
          conn_s3 = logins3(username)
          try:
            # Liste der Buckets
            liste_buckets = conn_s3.get_all_buckets()
          except:
            # Wenn es nicht klappt...
            fehlermeldung = "107"
            self.redirect('/s3?mobile='+str(mobile)+'&message='+fehlermeldung)
          else:
            # Wenn es geklappt hat...
            # Variable erzeugen zum Erfassen, ob der neue Bucket schon existiert
            laenge_liste_buckets = len(liste_buckets)

            # Variable erzeugen zum Erfassen, ob der neue Bucket schon existiert
            schon_vorhanden = 0
            for i in range(laenge_liste_buckets):
              # Bucket-Namen in einen String umwandeln
              vergleich = str(liste_buckets[i].name)
              # Vergleichen
              if vergleich == neuerbucketname:
                # Bucket-Name existiert schon!
                schon_vorhanden = 1

            if schon_vorhanden == 0:
              # Wenn man noch keinen Bucket mit dem eingegebenen Namen besitzt...
              try:
                # Versuch den Bucket anzulegen
                conn_s3.create_bucket(neuerbucketname)
              except:
                fehlermeldung = "107"
                # Wenn es nicht klappt...
                self.redirect('/s3?mobile='+str(mobile)+'&message='+fehlermeldung)
              else:
                fehlermeldung = "105"
                # Wenn es geklappt hat...
                self.redirect('/s3?mobile='+str(mobile)+'&message='+fehlermeldung)
            else:
              # Wenn man schon einen Bucket mit dem eingegeben Namen hat...
              fehlermeldung = "108"
              self.redirect('/s3?mobile='+str(mobile)+'&message='+fehlermeldung)


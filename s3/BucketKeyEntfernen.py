#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import logins3

class BucketKeyEntfernen(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        #self.response.out.write('posted!')
        # Den Namen des zu löschen Keys holen
        keyname = self.request.get('key')
        # Namen des Buckets holen, aus dem der Key gelöscht werden soll
        bucketname = self.request.get('bucket')
        # War es die reine S3-Darstellung oder die Komfort-Darstellung, aus der die 
        # Anfrage zu Löschen des Keys kam?
        typ = self.request.get('typ')
        # Das Verzeichnis aus dem Formular holen
        directory = self.request.get('dir')

        # Den Slash am Ende des Verzeichnisses entfernen
        directory = str(directory[:-1])

        # Den Usernamen erfahren
        username = users.get_current_user()

        # Mit S3 verbinden
        conn_s3 = logins3(username)

        bucket_instance = conn_s3.get_bucket(bucketname)
        # Liste der Keys im Bucket
        liste_keys = bucket_instance.get_all_keys()
        # Anzahl der Keys in der Liste
        laenge_liste_keys = len(liste_keys)

        for i in range(laenge_liste_keys):
          # Key-Name in einen String umwandeln
          vergleich = str(liste_keys[i].name)
          if vergleich == keyname:
          # Vergleichen
            try:
              # Versuch den Key zu löschen
              liste_keys[i].delete()
            except:
              fehlermeldung = "112"
              # Wenn es nicht klappt...
              if typ == "pur":
                if directory == "/":
                  self.redirect('/bucket_inhalt_pure?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)
                else:
                  self.redirect('/bucket_inhalt_pure?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
              else:
                if directory == "/":
                  self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)
                else:
                  self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
            else:
              fehlermeldung = "111"
              # Wenn es geklappt hat...
              if typ == "pur":
                if directory == "/":
                  self.redirect('/bucket_inhalt_pure?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)
                else:
                  self.redirect('/bucket_inhalt_pure?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
              else:
                if directory == "/":
                  self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)
                else:
                  self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)

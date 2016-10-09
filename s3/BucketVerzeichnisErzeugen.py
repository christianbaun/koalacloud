#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import re

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import logins3

class BucketVerzeichnisErzeugen(webapp.RequestHandler):
    def post(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        #self.response.out.write('posted!')
        # Die Eingabe aus dem Formular holen
        verzeichnisname = self.request.get('verzeichnisname') 
        # Den Bucketnamen aus dem Formular holen
        bucketname = self.request.get('bucket')
        # Das Verzeichnis aus dem Formular holen
        directory = self.request.get('dir')

        # Den Usernamen erfahren
        username = users.get_current_user()

        if verzeichnisname == "":
          # Testen ob ein Name für den neuen key angegeben wurde
          # Wenn kein Name angegeben wurde, kann kein Key angelegt werden
          #fehlermeldung = "Sie haben keine Namen angegeben"
          fehlermeldung = "113"
          if directory == "/":
            self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)
          else:
            # Den Slash am Ende des Verzeichnisses entfernen
            directory = str(directory[:-1])
            self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
        elif re.search(r'[^\-_a-zA-Z0-9]', verzeichnisname) != None:
          # Testen ob der Name für den neuen key nicht erlaubte Zeichen enthält
          fehlermeldung = "114"
          if directory == "/":
            self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)
          else:
            # Den Slash am Ende des Verzeichnisses entfernen
            directory = str(directory[:-1])
            self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
        else:
          # Mit S3 verbinden
          conn_s3 = logins3(username) 
          # Mit dem Bucket verbinden
          bucket_instance = conn_s3.get_bucket(bucketname)
          # Liste der Keys im Bucket
          liste_keys = bucket_instance.get_all_keys()
          # Anzahl der Keys in der Liste
          laenge_liste_keys = len(liste_keys)

          verzeichnisname = verzeichnisname+'_$folder$'

          # Variable erzeugen zum Erfassen, ob das neue Verzeichnis schon existiert
          schon_vorhanden = 0
          for i in range(laenge_liste_keys):
            # Key-Namen in einen String umwandeln
            vergleich = str(liste_keys[i].name)
            # Vergleichen
            if vergleich == verzeichnisname:
              # Verzeichnis-Name existiert schon!
              schon_vorhanden = 1
              fehlermeldung = "117"
              if directory == "/":
                self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)
              else:
                # Den Slash am Ende des Verzeichnisses entfernen
                directory = str(directory[:-1])
                self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)

          # Wenn man noch kein Verzeichnis mit dem eingegebenen Namen besitzt... 
          if schon_vorhanden == 0:
            try:
              # Versuch das Verzeichnis anzulegen
              # Mit dem Bucket sind wir schon verbunden über die Zeile
              # bucket_instance = conn_s3.get_bucket(bucketname)
              if directory == '/':
                key = bucket_instance.new_key(verzeichnisname)
                key.set_contents_from_string('')
              else:
                verzeichnisname = directory + verzeichnisname
                key = bucket_instance.new_key(verzeichnisname)
                key.set_contents_from_string('')
            except:
              # Wenn es nicht klappt...
              fehlermeldung = "116"
              if directory == "/":
                self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)
              else:
                # Den Slash am Ende des Verzeichnisses entfernen
                directory = str(directory[:-1])
                self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
            else:
              # Wenn es geklappt hat...
              fehlermeldung = "115"
              if directory == "/":
                self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung)
              else:
                # Den Slash am Ende des Verzeichnisses entfernen
                directory = str(directory[:-1])
                self.redirect('/bucket_inhalt?mobile='+str(mobile)+'&bucket='+bucketname+'&message='+fehlermeldung+'&dir='+directory)
                
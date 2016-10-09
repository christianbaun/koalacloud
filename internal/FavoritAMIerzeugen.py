#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import re

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp

from library import login

from internal.Datastore import *

from boto.ec2.connection import *
from boto.s3.connection import *

class FavoritAMIerzeugen(webapp.RequestHandler):
    def post(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        #self.response.out.write('posted!')
        ami = self.request.get('ami')
        zone = self.request.get('zone')
        # Den Usernamen erfahren
        username = users.get_current_user()

        if ami == "":
          # Testen ob die AMI-Bezeichnung angegeben wurde
          # Wenn keine AMI-Bezeichnung angegeben wurde, kann kein Favorit angelegt werden
          #fehlermeldung = "Sie haben keine AMI-Bezeichnung angegeben"
          fehlermeldung = "84"
          self.redirect('/images?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          if re.match('ami-*', ami) == None:  
            # Erst überprüfen, ob die Eingabe mit "ami-" angängt
            fehlermeldung = "85"
            self.redirect('/images?mobile='+str(mobile)+'&message='+fehlermeldung)
          elif len(ami) != 12:
            # Überprüfen, ob die Eingabe 12 Zeichen lang ist
            fehlermeldung = "86"
            self.redirect('/images?mobile='+str(mobile)+'&message='+fehlermeldung)
          elif re.search(r'[^\-a-zA-Z0-9]', ami) != None:
            # Überprüfen, ob die Eingabe nur erlaubte Zeichen enthält
            # Die Zeichen - und a-zA-Z0-9 sind erlaubt. Alle anderen nicht. Darum das ^
            fehlermeldung = "87"
            self.redirect('/images?mobile='+str(mobile)+'&message='+fehlermeldung)
          else:
            # Erst überprüfen, ob schon ein AMI-Eintrag dieses Benutzers in der Zone vorhanden ist.
            testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankFavouritenAMIs WHERE user = :username_db AND ami = :ami_db AND zone = :zone_db", username_db=username, ami_db=ami, zone_db=zone)
            # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
            results = testen.fetch(100)
            for result in results:
              result.delete()

            # Erst testen, ob es dieses AMI überhaupt gibt.
            # Eine leere Liste für das AMI erzeugen
            ami_liste = []
            # Das AMIs in die Liste einfügen
            ami_liste.append(ami)

            conn_region, regionname = login(username)
            try:
              liste_favoriten_ami_images = conn_region.get_all_images(image_ids=ami_liste)
            except EC2ResponseError:
              fehlermeldung = "88"
              self.redirect('/images?mobile='+str(mobile)+'&message='+fehlermeldung)
            except DownloadError:
                # Diese Exception hilft gegen diese beiden Fehler:
                # DownloadError: ApplicationError: 2 timed out
                # DownloadError: ApplicationError: 5
              fehlermeldung = "8"
              self.redirect('/images?mobile='+str(mobile)+'&message='+fehlermeldung)
            else:
              # Favorit erzeugen
              # Festlegen, was in den Datastore geschrieben werden soll
              favorit = KoalaCloudDatenbankFavouritenAMIs(ami=ami,
                                                          zone=zone,
                                                          user=username)
              # In den Datastore schreiben
              favorit.put()

              fehlermeldung = "83"
              self.redirect('/images?mobile='+str(mobile)+'&message='+fehlermeldung)


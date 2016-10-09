#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import re

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp

from library import login
from library import xor_crypt_string

from internal.Datastore import *

from boto.ec2.connection import *
from boto.s3.connection import *

class ZugangEinrichten(webapp.RequestHandler):
    def post(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        nameregion = self.request.get('nameregion')
        endpointurl = self.request.get('endpointurl')
        port = self.request.get('port')
        # Die projectid brauchen wir für die HP Cloud
        # We need the projectid for the HP Cloud
        projectid = self.request.get('projectid')
        accesskey = self.request.get('accesskey')
        secretaccesskey = self.request.get('secretaccesskey')
        typ = self.request.get('typ')
        # Den Usernamen erfahren
        username = users.get_current_user()
        # self.response.out.write('posted!')

        if users.get_current_user():

          # Wenn ein EC2-Zugang angelegt werden soll
          if typ == "ec2":

            if accesskey == "" and secretaccesskey == "":
              # Wenn kein Access Key und kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Access Key und keinen Secret Access Key angegeben"
              fehlermeldung = "89"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "90"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "91"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "94"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\/a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "95"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            else: # Access Key und Secret Access Key wurden angegeben
              # Prüfen, ob die Zugangsdaten für EC2 korrekt sind
              try:
                # Zugangsdaten testen
                region = RegionInfo(name="ec2", endpoint="ec2.amazonaws.com")
                connection = boto.connect_ec2(aws_access_key_id=accesskey,
                                            aws_secret_access_key=secretaccesskey,
                                            is_secure=False,
                                            validate_certs=False,
                                            region=region,
                                            #port=8773,
                                            path="/")

                liste_zonen = connection.get_all_zones()
              except EC2ResponseError:
                # Wenn die Zugangsdaten falsch sind, dann wird umgeleitet zur Regionenseite
                fehlermeldung = "98"
                self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
              else:
                # Wenn die Zugangsdaten für EC2 korrekt sind, dann wird hier weiter gemacht...
                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db="Amazon")
                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                logindaten = KoalaCloudDatenbank(regionname="us-east-1",
                                                eucalyptusname="Amazon",
                                                accesskey=accesskey,
                                                endpointurl="ec2.amazonaws.com",
                                                zugangstyp="Amazon",
                                                secretaccesskey=secretaccesskey_base64encoded,
                                                port=None,
                                                user=username)
                # In den Datastore schreiben
                logindaten.put()

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                logindaten = KoalaCloudDatenbankAktiveZone(aktivezone="us-east-1",
                                                           user=username,
                                                           zugangstyp="Amazon")
                # In den Datastore schreiben
                logindaten.put()

                self.redirect('/regionen')

          # Wenn ein HP Cloud-Zugang angelegt werden soll
          elif typ == "HP":

            if accesskey == "" and secretaccesskey == "":
              # Wenn kein Access Key und kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Access Key und keinen Secret Access Key angegeben"
              fehlermeldung = "89"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "90"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "91"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "94"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\/a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "95"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            else: # Access Key und Secret Access Key wurden angegeben
              # Prüfen, ob die Zugangsdaten für EC2 korrekt sind
              try:
                # Zugangsdaten testen
                region = RegionInfo(name="hpcloud", endpoint="az-1.region-a.geo-1.ec2-compute.hpcloudsvc.com")
                accesskey_new = projectid+':'+accesskey
                connection = boto.connect_ec2(aws_access_key_id=accesskey_new,
                                            aws_secret_access_key=secretaccesskey,
                                            is_secure=True,
                                            validate_certs=False,
                                            region=region,
                                            #port=8773,
                                            path="/services/Cloud/")

                liste_zonen = connection.get_all_zones()
              except EC2ResponseError:
                # Wenn die Zugangsdaten falsch sind, dann wird umgeleitet zur Regionenseite
                fehlermeldung = "98"
                self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
              else:
                # Wenn die Zugangsdaten für EC2 korrekt sind, dann wird hier weiter gemacht...
                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db="HP")
                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                logindaten = KoalaCloudDatenbank(regionname="us_west",
                                                eucalyptusname="HP",
                                                accesskey=accesskey_new,
                                                endpointurl="az-1.region-a.geo-1.ec2-compute.hpcloudsvc.com",
                                                zugangstyp="HP",
                                                secretaccesskey=secretaccesskey_base64encoded,
                                                port=None,
                                                user=username)
                # In den Datastore schreiben
                logindaten.put()

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                logindaten = KoalaCloudDatenbankAktiveZone(aktivezone="us_west",
                                                           user=username,
                                                           zugangstyp="HP")
                # In den Datastore schreiben
                logindaten.put()

                self.redirect('/regionen')


          # Wenn ein Google Storage-Zugang angelegt werden soll
          elif typ == "GoogleStorage":

            if accesskey == "" and secretaccesskey == "":
              # Wenn kein Access Key und kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Access Key und keinen Secret Access Key angegeben"
              fehlermeldung = "89"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "90"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "91"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "94"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\/a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "95"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            else: # Access Key und Secret Access Key wurden angegeben
              
              # Prüfen, ob die Zugangsdaten für Google Storage korrekt sind
              try:
                # Zugangsdaten testen
                calling_format=boto.s3.connection.OrdinaryCallingFormat()
                connection = boto.connect_s3(aws_access_key_id=accesskey,
                                                aws_secret_access_key=secretaccesskey,
                                                is_secure=False,
                                                validate_certs=False,
                                                host="commondatastorage.googleapis.com",
                                                calling_format=calling_format,
                                                path="/")
                
                liste_zonen = connection.get_all_buckets()


              except EC2ResponseError:
                # Wenn die Zugangsdaten falsch sind, dann wird umgeleitet zur Regionenseite
                fehlermeldung = "98"
                self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
              else:
                # Wenn die Zugangsdaten für Google Storage korrekt sind, dann wird hier weiter gemacht...
                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db="GoogleStorage")
                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()


                secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                logindaten = KoalaCloudDatenbank(regionname="GoogleStorage",
                                                eucalyptusname="GoogleStorage",
                                                accesskey=accesskey,
                                                endpointurl="commondatastorage.googleapis.com",
                                                zugangstyp="GoogleStorage",
                                                secretaccesskey=secretaccesskey_base64encoded,
                                                port=None,
                                                user=username)
                # In den Datastore schreiben
                logindaten.put()

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                logindaten = KoalaCloudDatenbankAktiveZone(aktivezone="GoogleStorage",
                                                           user=username,
                                                           zugangstyp="GoogleStorage")
                # In den Datastore schreiben
                logindaten.put()

                self.redirect('/regionen')




          # Wenn ein Host Europe Cloud Storage-Zugang angelegt werden soll
          elif typ == "HostEuropeCloudStorage":

            if accesskey == "" and secretaccesskey == "":
              # Wenn kein Access Key und kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Access Key und keinen Secret Access Key angegeben"
              fehlermeldung = "89"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "90"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "91"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "94"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\/a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "95"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            else: # Access Key und Secret Access Key wurden angegeben
              
              # Prüfen, ob die Zugangsdaten für Google Storage korrekt sind
              try:
                # Zugangsdaten testen
                calling_format=boto.s3.connection.OrdinaryCallingFormat()
                connection = boto.connect_s3(aws_access_key_id=accesskey,
                                                aws_secret_access_key=secretaccesskey,
                                                is_secure=True,
                                                validate_certs=False,
                                                host="cs.hosteurope.de",
                                                calling_format=calling_format,
                                                path="/")
                
                liste_zonen = connection.get_all_buckets()


              except EC2ResponseError:
                # Wenn die Zugangsdaten falsch sind, dann wird umgeleitet zur Regionenseite
                fehlermeldung = "98"
                self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
              else:
                # Wenn die Zugangsdaten für Google Storage korrekt sind, dann wird hier weiter gemacht...
                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db="HostEuropeCloudStorage")
                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()


                secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                logindaten = KoalaCloudDatenbank(regionname="HostEuropeCloudStorage",
                                                eucalyptusname="HostEuropeCloudStorage",
                                                accesskey=accesskey,
                                                endpointurl="cs.hosteurope.de",
                                                zugangstyp="HostEuropeCloudStorage",
                                                secretaccesskey=secretaccesskey_base64encoded,
                                                port=None,
                                                user=username)
                # In den Datastore schreiben
                logindaten.put()

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                logindaten = KoalaCloudDatenbankAktiveZone(aktivezone="HostEuropeCloudStorage",
                                                           user=username,
                                                           zugangstyp="HostEuropeCloudStorage")
                # In den Datastore schreiben
                logindaten.put()

                self.redirect('/regionen')



          # Wenn ein Host Europe Cloud Storage-Zugang angelegt werden soll
          elif typ == "DunkelCloudStorage":

            if accesskey == "" and secretaccesskey == "":
              # Wenn kein Access Key und kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Access Key und keinen Secret Access Key angegeben"
              fehlermeldung = "89"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "90"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "91"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "94"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\/a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "95"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            else: # Access Key und Secret Access Key wurden angegeben
              
              # Prüfen, ob die Zugangsdaten für Dunkel Cloud Storage korrekt sind
              try:
                # Zugangsdaten testen
                calling_format=boto.s3.connection.OrdinaryCallingFormat()
                connection = boto.connect_s3(aws_access_key_id=accesskey,
                                                aws_secret_access_key=secretaccesskey,
                                                is_secure=True,
                                                validate_certs=False,
                                                host="dcs.dunkel.de",
                                                calling_format=calling_format,
                                                path="/")
                
                liste_zonen = connection.get_all_buckets()


              except EC2ResponseError:
                # Wenn die Zugangsdaten falsch sind, dann wird umgeleitet zur Regionenseite
                fehlermeldung = "98"
                self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
              else:
                # Wenn die Zugangsdaten für Dunkel Cloud Storage korrekt sind, dann wird hier weiter gemacht...
                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db="DunkelCloudStorage")
                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()


                secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                logindaten = KoalaCloudDatenbank(regionname="DunkelCloudStorage",
                                                eucalyptusname="DunkelCloudStorage",
                                                accesskey=accesskey,
                                                endpointurl="dcs.dunkel.de",
                                                zugangstyp="DunkelCloudStorage",
                                                secretaccesskey=secretaccesskey_base64encoded,
                                                port=None,
                                                user=username)
                # In den Datastore schreiben
                logindaten.put()

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                logindaten = KoalaCloudDatenbankAktiveZone(aktivezone="DunkelCloudStorage",
                                                           user=username,
                                                           zugangstyp="DunkelCloudStorage")
                # In den Datastore schreiben
                logindaten.put()

                self.redirect('/regionen')



          # Wenn ein Nimbus-Zugang angelegt werden soll
          elif typ == "nimbus":
            if accesskey == "" and secretaccesskey == "":
              # Wenn kein Access Key und kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Access Key und keinen Secret Access Key angegeben"
              fehlermeldung = "89"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "90"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "91"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif nameregion == "": 
              # Wenn kein Name eingegeben wurde
              fehlermeldung = "92"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif endpointurl == "": 
              # Wenn keine Endpoint URL eingegeben wurde
              fehlermeldung = "93"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "94"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\/a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "95"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \-._a-zA-Z0-9]', nameregion) != None:
              # Wenn der Name nicht erlaubte Zeichen enthält
              fehlermeldung = "96"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \/\-.:_a-zA-Z0-9]', endpointurl) != None:
              # Wenn die Endpoint URL nicht erlaubte Zeichen enthält
              fehlermeldung = "97"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            else:
              # Access Key und  Secret Access Key wurden angegeben

              # Prüfen, ob die Zugangsdaten für Eucalyptus korrekt sind
              try:
                # Zugangsdaten testen
                port = int(port)
                connection = boto.connect_ec2(str(accesskey), str(secretaccesskey), port=port)
                connection.host = str(endpointurl)

                liste_zonen = connection.get_all_zones()

              except:
                # Wenn die Zugangsdaten falsch sind, dann wird umgeleitet zur Regionenseite
                fehlermeldung = "98"
                self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
              else:
                # Wenn die Zugangsdaten für Nimbus korrekt sind, dann wird hier weiter gemacht...

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND regionname = :regionname_db AND eucalyptusname = :eucalyptusname_db", username_db=username, regionname_db="nimbus", eucalyptusname_db=nameregion)
                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                port = str(port) # Sicherstellen, dass der Port ein String ist
                secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                logindaten = KoalaCloudDatenbank(regionname=typ,
                                                eucalyptusname=nameregion,
                                                accesskey=accesskey,
                                                endpointurl=endpointurl,
                                                zugangstyp="Nimbus",
                                                secretaccesskey=secretaccesskey_base64encoded,
                                                port=port,
                                                user=username)
                # In den Datastore schreiben
                logindaten.put()

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                logindaten = KoalaCloudDatenbankAktiveZone(aktivezone=nameregion,
                                                          user=username,
                                                          zugangstyp="Nimbus")
                # In den Datastore schreiben
                logindaten.put()

                self.redirect('/regionen')
                
          # Wenn ein OpenNebula-Zugang angelegt werden soll
          elif typ == "opennebula":
            if accesskey == "" and secretaccesskey == "":
              # Wenn kein Access Key und kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Access Key und keinen Secret Access Key angegeben"
              fehlermeldung = "89"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "90"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "91"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif nameregion == "": 
              # Wenn kein Name eingegeben wurde
              fehlermeldung = "92"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif endpointurl == "": 
              # Wenn keine Endpoint URL eingegeben wurde
              fehlermeldung = "93"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "94"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\/a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "95"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \-._a-zA-Z0-9]', nameregion) != None:
              # Wenn der Name nicht erlaubte Zeichen enthält
              fehlermeldung = "96"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \/\-.:_a-zA-Z0-9]', endpointurl) != None:
              # Wenn die Endpoint URL nicht erlaubte Zeichen enthält
              fehlermeldung = "97"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            else:
              # Access Key und  Secret Access Key wurden angegeben

              # Prüfen, ob die Zugangsdaten für Eucalyptus korrekt sind
              try:
                # Zugangsdaten testen
                connection = boto.connect_ec2(accesskey, secretaccesskey, is_secure=False, validate_certs=False, port=int(port))
                connection.host = endpointurl

                instances = connection.get_all_instances()

              except:
                # Wenn die Zugangsdaten falsch sind, dann wird umgeleitet zur Regionenseite
                fehlermeldung = "98"
                self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
              else:
                # Wenn die Zugangsdaten für OpenNebula korrekt sind, dann wird hier weiter gemacht...

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND regionname = :regionname_db AND eucalyptusname = :eucalyptusname_db", username_db=username, regionname_db="nimbus", eucalyptusname_db=nameregion)
                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                port = str(port) # Sicherstellen, dass der Port ein String ist
                secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                logindaten = KoalaCloudDatenbank(regionname=typ,
                                                eucalyptusname=nameregion,
                                                accesskey=accesskey,
                                                endpointurl=endpointurl,
                                                zugangstyp="OpenNebula",
                                                secretaccesskey=secretaccesskey_base64encoded,
                                                port=port,
                                                user=username)
                # In den Datastore schreiben
                logindaten.put()

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                logindaten = KoalaCloudDatenbankAktiveZone(aktivezone=nameregion,
                                                          user=username,
                                                          zugangstyp="OpenNebula")
                # In den Datastore schreiben
                logindaten.put()

                self.redirect('/regionen')

          # Wenn ein Eucalyptus-Zugang angelegt werden soll
          else:
            if accesskey == "" and secretaccesskey == "":
              # Wenn kein Access Key und kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Access Key und keinen Secret Access Key angegeben"
              fehlermeldung = "89"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif accesskey == "": 
              #fehlermeldung = "Sie haben keinen Access Key angegeben"
              fehlermeldung = "90"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif secretaccesskey == "": 
              # Wenn kein Secret Access Key angegeben wurde
              #fehlermeldung = "Sie haben keinen Secret Access Key angegeben"
              fehlermeldung = "91"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif nameregion == "": 
              # Wenn kein Name eingegeben wurde
              fehlermeldung = "92"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif endpointurl == "": 
              # Wenn keine Endpoint URL eingegeben wurde
              fehlermeldung = "93"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^a-zA-Z0-9]', accesskey) != None:
              # Wenn der Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "94"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\/a-zA-Z0-9+=]', secretaccesskey) != None:
              # Wenn der Secret Access Key nicht erlaubte Zeichen enthält
              #fehlermeldung = "Ihr eingegebener Secret Access Key enthielt nicht erlaubte Zeichen"
              fehlermeldung = "95"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \-._a-zA-Z0-9]', nameregion) != None:
              # Wenn der Name nicht erlaubte Zeichen enthält
              fehlermeldung = "96"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            elif re.search(r'[^\ \/\-.:_a-zA-Z0-9]', endpointurl) != None:
              # Wenn die Endpoint URL nicht erlaubte Zeichen enthält
              fehlermeldung = "97"
              self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
            else:
              # Access Key und  Secret Access Key wurden angegeben

              # Prüfen, ob die Zugangsdaten für Eucalyptus korrekt sind
              try:
                # Zugangsdaten testen
                port = int(port)
                region = RegionInfo(name=nameregion, endpoint=endpointurl)
                connection = boto.connect_ec2(aws_access_key_id=accesskey,
                                              aws_secret_access_key=secretaccesskey,
                                              is_secure=False,
                                              validate_certs=False,
                                              region=region,
                                              port=port,
                                              path="/services/Eucalyptus")

                liste_zonen = connection.get_all_zones()
              except:
                # Wenn die Zugangsdaten falsch sind, dann wird umgeleitet zur Regionenseite
                fehlermeldung = "98"
                self.redirect('/regionen?neuerzugang='+typ+'&message='+fehlermeldung)
              else:
                # Wenn die Zugangsdaten für Eucalyptus korrekt sind, dann wird hier weiter gemacht...

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND regionname = :regionname_db AND eucalyptusname = :eucalyptusname_db", username_db=username, regionname_db="eucalyptus", eucalyptusname_db=nameregion)
                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                # Sicherstellen, dass der Port ein String ist
                port = str(port)
                secretaccesskey_encrypted = xor_crypt_string(str(secretaccesskey), key=str(username))
                secretaccesskey_base64encoded = base64.b64encode(secretaccesskey_encrypted)
                logindaten = KoalaCloudDatenbank(regionname=typ,
                                                eucalyptusname=nameregion,
                                                accesskey=accesskey,
                                                endpointurl=endpointurl,
                                                zugangstyp="Eucalyptus",
                                                secretaccesskey=secretaccesskey_base64encoded,
                                                port=port,
                                                user=username)
                # In den Datastore schreiben
                logindaten.put()

                # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
                testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

                # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
                results = testen.fetch(100)
                for result in results:
                  result.delete()

                logindaten = KoalaCloudDatenbankAktiveZone(aktivezone=nameregion,
                                                          user=username,
                                                          zugangstyp="Eucalyptus")
                # In den Datastore schreiben
                logindaten.put()

                self.redirect('/regionen')
        else:
            self.redirect('/')
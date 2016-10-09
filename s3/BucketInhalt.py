#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os
import re

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api.urlfetch import DownloadError

from library import login
from library import aktuelle_sprache
from library import navigations_bar_funktion
from library import amazon_region
from library import zonen_liste_funktion
from library import format_error_message_green
from library import format_error_message_red
from library import logins3
from library import aws_access_key_erhalten
from library import aws_secret_access_key_erhalten
from library import endpointurl_erhalten
from library import zugangstyp_erhalten
from library import port_erhalten

from dateutil.parser import *

from error_messages import error_messages

# für die Verschlüsselung
# this is needed for the encyption
from itertools import izip, cycle
import hmac, sha
# für die Verschlüsselung
# this is needed for the encyption
import base64

class BucketInhalt(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # self.response.out.write('posted!')
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
          self.redirect('/')
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')
        # Eventuell vorhandes Verzeichnis holen
        directory = self.request.get('dir')
        # Namen des Buckets holen, dessen Inhalt angezeigt wird
        bucketname = self.request.get('bucket')


        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if not results:
          self.redirect('/')
        else:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache,mobile)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)
          zugangstyp = zugangstyp_erhalten(username) 
          
          zonen_liste = zonen_liste_funktion(username,sprache,mobile)

          AWSAccessKeyId = aws_access_key_erhalten(username,regionname)
          AWSSecretAccessKeyId = aws_secret_access_key_erhalten(username,regionname)

          input_error_message = ""

          if sprache != "de":
            sprache = "en"

          input_error_message = error_messages.get(message, {}).get(sprache)

          # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
          if input_error_message == None:
            input_error_message = ""

          # Wenn die Nachricht grün formatiert werden soll...
          if message in ("111", "115", "118", "120"):
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message in ("112", "113", "114", "116", "117", "119", "121"):
            input_error_message = format_error_message_red(input_error_message)
          else:
            input_error_message = ""

          # Mit S3 verbinden
          conn_s3 = logins3(username)
          
          try:
            # Liste der Buckets
            bucket_instance = conn_s3.get_bucket(bucketname)
          except:
            # Wenn es nicht klappt...
            if sprache == "de":
              bucket_keys_tabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
            else:
              bucket_keys_tabelle = '<font color="red">An error occured</font>'
            laenge_liste_keys = 0
          else:
          


            # Wenn die Variable "directory" gesetzt ist, also ein Verzeichnis angegeben wurde...
            if directory:
              # An das Verzeichnis ein "/" angängen
              directory = directory + '/'
              try:
                # Liste der Keys im Bucket
                liste_keys = bucket_instance.get_all_keys(prefix=directory)
              except:
                # Wenn es nicht klappt...
                if sprache == "de":
                  bucket_keys_tabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
                else:
                  bucket_keys_tabelle = '<font color="red">An error occured</font>'
                laenge_liste_keys = 0
              else:
                # Anzahl der Keys in der Liste
                laenge_liste_keys = len(liste_keys)
                # Die Variable "level" ist quasi die Ebene im Dateibaum.
                # Die Zahl in "level" ist gleich der "/" in den Key-Namen der Keys, die
                # in dem Verzeichnis drin sind.
                level = directory.count("/")
            # Wenn kein Verzeichnis angegeben wurde...
            else:
              # Dann wird die Variable "directory" gesetzt und zwar auf "/"
              directory = '/'
              try:
                # Liste der Keys im Bucket
                liste_keys = bucket_instance.get_all_keys()
              except:
                # Wenn es nicht klappt...
                if sprache == "de":
                  bucket_keys_tabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
                else:
                  bucket_keys_tabelle = '<font color="red">An error occured</font>'
                laenge_liste_keys = 0
              else:
                # Anzahl der Keys in der Liste
                laenge_liste_keys = len(liste_keys)
                # Die Variable "level" ist quasi die Ebene im Dateibaum.
                # level = 0 heißt, wir sind in der Root-Ebene.
                level = 0
  
            # Wenn wir uns im "Root"-Verzeichnis des Buckets befinden, wird aus
            # der Liste der Keys alle Keys entfernt, die einen / im Keynamen haben
            if directory == '/':
              liste_keys2 = []
              for i in range(laenge_liste_keys):
                if re.search(r'[/]', str(liste_keys[i].name)) == None:
                  liste_keys2.append(liste_keys[i])
              laenge_liste_keys2 = len(liste_keys2)
              laenge_liste_keys = laenge_liste_keys2
              liste_keys = liste_keys2
            # Wenn wir uns nicht im "Root"-Verzeichnis des Buckets befinden,
            # dann wird für jeden Key geschaut, ob er die gleiche Anzahl an "/" im
            # Namen hat, wie die Variable "level" als Zahl enthält.
            else:
              liste_keys2 = []
              for i in range(laenge_liste_keys):
                if str(liste_keys[i].name).count("/") == level:
                  liste_keys2.append(liste_keys[i])
              laenge_liste_keys2 = len(liste_keys2)
              laenge_liste_keys = laenge_liste_keys2
              liste_keys = liste_keys2
  
            # Wenn wir im Root-Verzeichnis sind und es sind keine Keys vorhanden...
            if laenge_liste_keys == 0 and directory == '/':
              if sprache == "de":
                bucket_keys_tabelle = 'Der Bucket <B>'+ bucketname+' </B>ist leer.'
              else:
                bucket_keys_tabelle = 'The bucket <B>'+ bucketname+' </B>is empty.'
            # Wenn wir nicht im Root-Verzeichnis sind und es sind keine Keys vorhanden...
            elif laenge_liste_keys == 0 and directory != '/':
              if sprache == "de":
                bucket_keys_tabelle = 'Das Verzeichnis <B>'+ directory+' </B>ist leer.'
                bucket_keys_tabelle += '<p>&nbsp;</p>'
                bucket_keys_tabelle += '<a href="/bucket_inhalt?bucket='
                bucket_keys_tabelle += str(bucketname)
                # Wenn das aktuelle Verzeichnis zwei oder mehr "/" enthält, dann müssen
                # wir eine Rücksprungmöglichkeit bauen. Dabei wird erst der
                # letzte Slash entfernt und dann der Text bis zum nächsten Slash.
                # Wenn das aktuelle Verzeichnis NICHT zwei oder mehr "/" enthält,
                # dann geben wir gar kein Verzeichnis an, weil dann wollen wir zur
                # Root-Ansicht zurückkehren.
                if str(directory).count("/") >= 2:
                  bucket_keys_tabelle += '&amp;dir='
                  bucket_keys_tabelle += str(directory)[:str(directory)[:-1].rfind('/')]
                bucket_keys_tabelle += "&amp;mobile="
                bucket_keys_tabelle += str(mobile)
                bucket_keys_tabelle += '" title="Zur&uuml;ck">'
                bucket_keys_tabelle += '<img src="bilder/left.png" width="16" height="16" border="0" alt="'
                bucket_keys_tabelle += 'Zur&uuml;ck'
                bucket_keys_tabelle += '"> '
                bucket_keys_tabelle += '</a>'
              else:
                bucket_keys_tabelle = 'The directory <B>'+ directory+' </B>is empty.'
                bucket_keys_tabelle += '<p>&nbsp;</p>'
                bucket_keys_tabelle += '<a href="/bucket_inhalt?bucket='
                bucket_keys_tabelle += str(bucketname)
                # Wenn das aktuelle Verzeichnis zwei oder mehr "/" enthält, dann müssen
                # wir eine Rücksprungmöglichkeit bauen. Dabei wird erst der
                # letzte Slash entfernt und dann der Text bis zum nächsten Slash.
                # Wenn das aktuelle Verzeichnis NICHT zwei oder mehr "/" enthält,
                # dann geben wir gar kein Verzeichnis an, weil dann wollen wir zur
                # Root-Ansicht zurückkehren.
                if str(directory).count("/") >= 2:
                  bucket_keys_tabelle += '&amp;dir='
                  bucket_keys_tabelle += str(directory)[:str(directory)[:-1].rfind('/')]
                bucket_keys_tabelle += "&amp;mobile="
                bucket_keys_tabelle += str(mobile)
                bucket_keys_tabelle += '" title="Switch back">'
                bucket_keys_tabelle += '<img src="bilder/left.png" width="16" height="16" border="0" alt="'
                bucket_keys_tabelle += 'Switch back'
                bucket_keys_tabelle += '"> '
                bucket_keys_tabelle += '</a>'
            # Wenn wir irgendwo sind und es sind Keys vorhanden...
            else:
              
              if mobile == "true":
                  # This is the mobile version
                  
                  bucket_keys_tabelle = ''
                  bucket_keys_tabelle += '<table border="0" cellspacing="0" cellpadding="5" width="300">'
                  # Wenn wir uns nicht im Root-Ordner des Buckets befinden, dann brauchen wir eine Rücksprungmöglichkeit
                  if directory != '/':
                    bucket_keys_tabelle += '<tr>'
                    bucket_keys_tabelle += '<td align="left" colspan="5">'
                    bucket_keys_tabelle += '<a href="/bucket_inhalt?bucket='
                    bucket_keys_tabelle += str(bucketname)
                    bucket_keys_tabelle += "&amp;mobile="
                    bucket_keys_tabelle += str(mobile)
                    # Wenn das aktuelle Verzeichnis zwei oder mehr "/" enthält, dann müssen
                    # wir eine Rücksprungmöglichkeit bauen. Dabei wird erst der
                    # letzte Slash entfernt und dann der Text bis zum nächsten Slash.
                    # Wenn das aktuelle Verzeichnis NICHT zwei oder mehr "/" enthält,
                    # dann geben wir gar kein Verzeichnis an, weil dann wollen wir zur
                    # Root-Ansicht zurückkehren.
                    if str(directory).count("/") >= 2:
                      bucket_keys_tabelle += '&amp;dir='
                      bucket_keys_tabelle += str(directory)[:str(directory)[:-1].rfind('/')]
    
                    if sprache == "de":
                      bucket_keys_tabelle += '" title="Zur&uuml;ck">'
                    else:
                      bucket_keys_tabelle += '" title="Switch back">'
                    # Hier wird das aktuelle Verzeichnis vom Key-Namen vorne abgeschnitten
                    #liste_keys[i].name = liste_keys[i].name.replace ( directory, '' )
                    bucket_keys_tabelle += '<img src="bilder/left.png" width="16" height="16" border="0" alt="'
                    if sprache == "de":
                      bucket_keys_tabelle += 'Zur&uuml;ck'
                    else:
                      bucket_keys_tabelle += 'Switch back'
                    bucket_keys_tabelle += '">'
                    bucket_keys_tabelle += '</a>'
                    bucket_keys_tabelle += '</td>'
                    bucket_keys_tabelle += '</tr>'

                  bucket_keys_tabelle += '<tr>'
                  bucket_keys_tabelle += '<td align="left" colspan="5"><b>'+str(directory)+'</b></td>'
                  bucket_keys_tabelle += '</tr>'

                  counter = 0
                  for i in range(laenge_liste_keys):
                    
                      if counter > 0:
                          bucket_keys_tabelle += '<tr><td colspan="4">&nbsp;</td></tr>'
                      counter += 1
                    
                      bucket_keys_tabelle += '<tr>'
                      bucket_keys_tabelle += '<td>'
                      bucket_keys_tabelle += '<a href="/bucketkeyentfernen?bucket='
                      bucket_keys_tabelle += str(bucketname)
                      bucket_keys_tabelle += '&amp;typ=kompfort'
                      bucket_keys_tabelle += '&amp;key='
                      bucket_keys_tabelle += str(liste_keys[i].name)
                      bucket_keys_tabelle += '&amp;dir='
                      bucket_keys_tabelle += str(directory)
                      bucket_keys_tabelle += "&amp;mobile="
                      bucket_keys_tabelle += str(mobile)
                      if sprache == "de":
                        bucket_keys_tabelle += '" title="Key l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Key l&ouml;schen"></a>'
                      else:
                        bucket_keys_tabelle += '" title="erase key"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase key"></a>'
                      bucket_keys_tabelle += '</td>'
    
    
                      bucket_keys_tabelle += '<td align="right">'
                      # Wenn der Name des Key mit dem String $folder$ endet, dann ist es ein Verzeichnis.
                      # Dann kommt hier ein anderes Icon hin
                      if str(liste_keys[i].name).endswith("$folder$") == True:
                        # Es ist ein Verzeichnis...
                        if sprache == "de":
                          bucket_keys_tabelle += '<img src="bilder/folder.png" width="16" height="16" border="0" alt="Verzeichnis">'
                        else:
                          bucket_keys_tabelle += '<img src="bilder/folder.png" width="16" height="16" border="0" alt="Folder">'
                      else:
                        # Ansonsten ist es eine Datei...
                        if sprache == "de":
                          bucket_keys_tabelle += '<img src="bilder/document.png" width="16" height="16" border="0" alt="Datei">'
                        else:
                          bucket_keys_tabelle += '<img src="bilder/document.png" width="16" height="16" border="0" alt="File">'
                      bucket_keys_tabelle += '</td>'
                      bucket_keys_tabelle += '<td colspan="2" align="left">'
                      # Wenn der Key ein Verzeichnis ist, werden vom Key-Namen die letzten 9 Zeichen
                      # abgeschnitten. Es wird einfach nur das "_$folder$" abgeschnitten.
                      if str(liste_keys[i].name).endswith("$folder$") == True:
                        bucket_keys_tabelle += '<a href="/bucket_inhalt?bucket='
                        bucket_keys_tabelle += str(bucketname)
                        bucket_keys_tabelle += '&amp;dir='
                        bucket_keys_tabelle += str(liste_keys[i].name[:-9])
                        bucket_keys_tabelle += "&amp;mobile="
                        bucket_keys_tabelle += str(mobile)
                        if sprache == "de":
                          bucket_keys_tabelle += '" title="In das Verzeichnis wechseln">'
                        else:
                          bucket_keys_tabelle += '" title="Switch to directory">'
                        # Hier wird das aktuelle Verzeichnis vom Key-Namen vorne abgeschnitten
                        name_tmp = liste_keys[i].name.replace( directory, '')
                        bucket_keys_tabelle += str(name_tmp[:-9])
                        bucket_keys_tabelle += '</a>'
                      # Wenn es sich nicht um ein Verzeichnis handelt
                      else:
                        # Nur wenn es nicht der None-Eintrag bei Eucalyptus ist, wird ein Link gebildet
                        # if liste_keys[i].name != None:
                       
                        bucket_keys_tabelle += '<a href="'
  
                        if regionname == "Amazon":
                          bucket_keys_tabelle += liste_keys[i].generate_url(600, method='GET', headers=None, query_auth=True, force_http=True).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
                        else:
                          port = port_erhalten(username,regionname) 
                          bucket_keys_tabelle += liste_keys[i].generate_url(600, method='GET', headers=None, query_auth=True, force_http=True).replace('&', '&amp;').replace('&amp;amp;', '&amp;').replace('/services/Walrus/', ':'+str(port)+'/services/Walrus/')
                  
                        bucket_keys_tabelle += '">'
                        # Hier wird das aktuelle Verzeichnis vom Key-Namen vorne abgeschnitten
                        name_tmp = liste_keys[i].name.replace(directory, '')
                        # Wenn der Key kein Verzeinis ist, muss hinten nichts abgeschnitten werden.
                        bucket_keys_tabelle += str(name_tmp)
                        bucket_keys_tabelle += '</a>'
                       
                        bucket_keys_tabelle += '</td>'
    
                      bucket_keys_tabelle += '</tr>'
                      bucket_keys_tabelle += '<tr>'
  
                      if sprache == "de":
                        bucket_keys_tabelle += '<td colspan="3" align="right"><b>Gr&ouml;&szlig;e:</b></td>'
                      else:
                        bucket_keys_tabelle += '<td colspan="3" align="right"><b>Size:</b></td>'
                      if str(liste_keys[i].name) != None:
                        # Wenn der Keyname auf "$folder" endet, dann wird keine Dateigröße ausgegeben.
                        if str(liste_keys[i].name).endswith("$folder$") == True:
                          bucket_keys_tabelle += '<td align="left">---</td>'
                        # Wenn der Keyname nicht auf $folder$ endet, wird die Dateigröße ausgegeben.
                        else:
                          bucket_keys_tabelle += '<td align="left">'+str(liste_keys[i].size)+'</td>'
                      else:
                        bucket_keys_tabelle += '<td align="right">&nbsp;</td>'
    
                      bucket_keys_tabelle += '</tr>'
                      bucket_keys_tabelle += '<tr>'

                      if sprache == "de":
                        bucket_keys_tabelle += '<td colspan="3" align="right"><b>Datum:</b></td>'
                      else:
                        bucket_keys_tabelle += '<td colspan="3" align="right"><b>Date:</b></td>'
                      bucket_keys_tabelle += '<td align="left">'
                      # Den ISO8601 Zeitstring umwandeln, damit es besser aussieht.
                      datum_der_letzten_aenderung = parse(liste_keys[i].last_modified)
                      bucket_keys_tabelle += str(datum_der_letzten_aenderung.strftime("%Y-%m-%d  %H:%M:%S"))
                      #bucket_keys_tabelle += str(liste_keys[i].last_modified)
                      bucket_keys_tabelle += '</td>'
    
                      bucket_keys_tabelle += '</tr>'
                      bucket_keys_tabelle += '<tr>'

                      bucket_keys_tabelle += '<td align="right" colspan="3"><b>ACL:</b></td>'
                      bucket_keys_tabelle += '<td align="left">'
                      bucket_keys_tabelle += '<a href="/acl_einsehen?bucket='
                      bucket_keys_tabelle += str(bucketname)
                      bucket_keys_tabelle += '&amp;typ=kompfort'
                      bucket_keys_tabelle += '&amp;key='+str(liste_keys[i].name)
                      bucket_keys_tabelle += '&amp;dir='+str(directory)
                      bucket_keys_tabelle += "&amp;mobile="
                      bucket_keys_tabelle += str(mobile)
                      if sprache == "de":
                        bucket_keys_tabelle += '" title="ACL einsehen/&auml;ndern">ACL einsehen/&auml;ndern</a>'
                      else:
                        bucket_keys_tabelle += '" title="view/edit ACL">view/edit ACL</a>'
                      bucket_keys_tabelle += '</td>'
                      
                      bucket_keys_tabelle += '</tr>'
                      bucket_keys_tabelle += '<tr>'

                      # In S3 and Google Storage, each MD5 checksum is enclosed by double quotes.
                      # Eliminate them with .replace('"','')
                      bucket_keys_tabelle += '<td align="right" colspan="3"><b>MD5:</b></td>'
                      bucket_keys_tabelle += '<td align="left">'+str(liste_keys[i].etag.replace('"',''))+'</td>'
                      bucket_keys_tabelle += '</tr>'
                  bucket_keys_tabelle += '</table>'
                  
              else:                 
                  # Not the mobile version
                  
                  bucket_keys_tabelle = ''
                  bucket_keys_tabelle += '<table border="0" cellspacing="0" cellpadding="5">'
                  # Wenn wir uns nicht im Root-Ordner des Buckets befinden, dann brauchen wir eine Rücksprungmöglichkeit
                  if directory != '/':
                    bucket_keys_tabelle += '<tr>'
                    bucket_keys_tabelle += '<td colspan="5">'
                    bucket_keys_tabelle += '<a href="/bucket_inhalt?bucket='
                    bucket_keys_tabelle += str(bucketname)
                    bucket_keys_tabelle += "&amp;mobile="
                    bucket_keys_tabelle += str(mobile)
                    # Wenn das aktuelle Verzeichnis zwei oder mehr "/" enthält, dann müssen
                    # wir eine Rücksprungmöglichkeit bauen. Dabei wird erst der
                    # letzte Slash entfernt und dann der Text bis zum nächsten Slash.
                    # Wenn das aktuelle Verzeichnis NICHT zwei oder mehr "/" enthält,
                    # dann geben wir gar kein Verzeichnis an, weil dann wollen wir zur
                    # Root-Ansicht zurückkehren.
                    if str(directory).count("/") >= 2:
                      bucket_keys_tabelle += '&amp;dir='
                      bucket_keys_tabelle += str(directory)[:str(directory)[:-1].rfind('/')]
    
                    if sprache == "de":
                      bucket_keys_tabelle += '" title="Zur&uuml;ck">'
                    else:
                      bucket_keys_tabelle += '" title="Switch back">'
                    # Hier wird das aktuelle Verzeichnis vom Key-Namen vorne abgeschnitten
                    #liste_keys[i].name = liste_keys[i].name.replace ( directory, '' )
                    bucket_keys_tabelle += '<img src="bilder/left.png" width="16" height="16" border="0" alt="'
                    if sprache == "de":
                      bucket_keys_tabelle += 'Zur&uuml;ck'
                    else:
                      bucket_keys_tabelle += 'Switch back'
                    bucket_keys_tabelle += '">'
                    bucket_keys_tabelle += '</a>'
                    bucket_keys_tabelle += '</td>'
                    bucket_keys_tabelle += '</tr>'

                  bucket_keys_tabelle += '<tr>'
                  bucket_keys_tabelle += '<td align="left" colspan="5"><b>'+str(directory)+'</b></td>'
                  bucket_keys_tabelle += '</tr>'

                  bucket_keys_tabelle += '<tr>'
                  bucket_keys_tabelle += '<td align="left" colspan="5">&nbsp;</td>'
                  bucket_keys_tabelle += '</tr>'
                  
                  counter = 0
                  for i in range(laenge_liste_keys):
                    
                      if counter > 0:
                          bucket_keys_tabelle += '<tr><td colspan="5">&nbsp;</td></tr>'
                      counter += 1
                    
                      bucket_keys_tabelle += '<tr>'
                      bucket_keys_tabelle += '<td align="left" bgcolor="#D4D4D4">'
                      bucket_keys_tabelle += '<a href="/bucketkeyentfernen?bucket='
                      bucket_keys_tabelle += str(bucketname)
                      bucket_keys_tabelle += '&amp;typ=kompfort'
                      bucket_keys_tabelle += '&amp;key='
                      bucket_keys_tabelle += str(liste_keys[i].name)
                      bucket_keys_tabelle += '&amp;dir='
                      bucket_keys_tabelle += str(directory)
                      bucket_keys_tabelle += "&amp;mobile="
                      bucket_keys_tabelle += str(mobile)
                      if sprache == "de":
                        bucket_keys_tabelle += '" title="Key l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Key l&ouml;schen"></a>'
                      else:
                        bucket_keys_tabelle += '" title="erase key"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase key"></a>'
                      bucket_keys_tabelle += '</td>'
    
    
                      bucket_keys_tabelle += '<td align="right" bgcolor="#D4D4D4">'
                      # Wenn der Name des Key mit dem String $folder$ endet, dann ist es ein Verzeichnis.
                      # Dann kommt hier ein anderes Icon hin
                      if str(liste_keys[i].name).endswith("$folder$") == True:
                        # Es ist ein Verzeichnis...
                        if sprache == "de":
                          bucket_keys_tabelle += '<img src="bilder/folder.png" width="16" height="16" border="0" alt="Verzeichnis">'
                        else:
                          bucket_keys_tabelle += '<img src="bilder/folder.png" width="16" height="16" border="0" alt="Folder">'
                      else:
                        # Ansonsten ist es eine Datei...
                        if sprache == "de":
                          bucket_keys_tabelle += '<img src="bilder/document.png" width="16" height="16" border="0" alt="Datei">'
                        else:
                          bucket_keys_tabelle += '<img src="bilder/document.png" width="16" height="16" border="0" alt="File">'
                      bucket_keys_tabelle += '</td>'
                      
                      bucket_keys_tabelle += '<td colspan="3" align="left" bgcolor="#D4D4D4">&nbsp;</td>'
     
                      bucket_keys_tabelle += '</tr>'
                      bucket_keys_tabelle += '<tr>'   
       
                      bucket_keys_tabelle += '<td colspan="2" align="right" bgcolor="#D4D4D4"><b>ID:</b></td>'
                                            
                      bucket_keys_tabelle += '<td colspan="3" align="left">'
                      # Wenn der Key ein Verzeichnis ist, werden vom Key-Namen die letzten 9 Zeichen
                      # abgeschnitten. Es wird einfach nur das "_$folder$" abgeschnitten.
                      if str(liste_keys[i].name).endswith("$folder$") == True:
                        bucket_keys_tabelle += '<a href="/bucket_inhalt?bucket='
                        bucket_keys_tabelle += str(bucketname)
                        bucket_keys_tabelle += '&amp;dir='
                        bucket_keys_tabelle += str(liste_keys[i].name[:-9])
                        bucket_keys_tabelle += "&amp;mobile="
                        bucket_keys_tabelle += str(mobile)
                        if sprache == "de":
                          bucket_keys_tabelle += '" title="In das Verzeichnis wechseln">'
                        else:
                          bucket_keys_tabelle += '" title="Switch to directory">'
                        # Hier wird das aktuelle Verzeichnis vom Key-Namen vorne abgeschnitten
                        name_tmp = liste_keys[i].name.replace( directory, '')
                        bucket_keys_tabelle += str(name_tmp[:-9])
                        bucket_keys_tabelle += '</a>'
                      # Wenn es sich nicht um ein Verzeichnis handelt
                      else:
                        # Nur wenn es nicht der None-Eintrag bei Eucalyptus ist, wird ein Link gebildet
                        # if liste_keys[i].name != None:
                       
                        bucket_keys_tabelle += '<a href="'
  
                        if regionname == "Amazon":
                          bucket_keys_tabelle += liste_keys[i].generate_url(600, method='GET', headers=None, query_auth=True, force_http=True).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
                        else:
                          port = port_erhalten(username,regionname) 
                          bucket_keys_tabelle += liste_keys[i].generate_url(600, method='GET', headers=None, query_auth=True, force_http=True).replace('&', '&amp;').replace('&amp;amp;', '&amp;').replace('/services/Walrus/', ':'+str(port)+'/services/Walrus/')
                  
                        bucket_keys_tabelle += '">'
                        # Hier wird das aktuelle Verzeichnis vom Key-Namen vorne abgeschnitten
                        name_tmp = liste_keys[i].name.replace(directory, '')
                        # Wenn der Key kein Verzeinis ist, muss hinten nichts abgeschnitten werden.
                        bucket_keys_tabelle += str(name_tmp)
                        bucket_keys_tabelle += '</a>'
                       
                        bucket_keys_tabelle += '</td>'
    
                      bucket_keys_tabelle += '</tr>'
                      bucket_keys_tabelle += '<tr>'
  
                      if sprache == "de":
                        bucket_keys_tabelle += '<td colspan="2" align="right" bgcolor="#D4D4D4"><b>Gr&ouml;&szlig;e:</b></td>'
                      else:
                        bucket_keys_tabelle += '<td colspan="2" align="right" bgcolor="#D4D4D4"><b>Size:</b></td>'
                      if str(liste_keys[i].name) != None:
                        # Wenn der Keyname auf "$folder" endet, dann wird keine Dateigröße ausgegeben.
                        if str(liste_keys[i].name).endswith("$folder$") == True:
                          bucket_keys_tabelle += '<td align="left">---</td>'
                        # Wenn der Keyname nicht auf $folder$ endet, wird die Dateigröße ausgegeben.
                        else:
                          bucket_keys_tabelle += '<td align="left">'+str(liste_keys[i].size)+'</td>'
                      else:
                        bucket_keys_tabelle += '<td align="right">&nbsp;</td>'

                      if sprache == "de":
                        bucket_keys_tabelle += '<td align="right" bgcolor="#D4D4D4"><b>Datum:</b></td>'
                      else:
                        bucket_keys_tabelle += '<td align="right" bgcolor="#D4D4D4"><b>Date:</b></td>'
                      bucket_keys_tabelle += '<td align="left">'
                      # Den ISO8601 Zeitstring umwandeln, damit es besser aussieht.
                      datum_der_letzten_aenderung = parse(liste_keys[i].last_modified)
                      bucket_keys_tabelle += str(datum_der_letzten_aenderung.strftime("%Y-%m-%d  %H:%M:%S"))
                      #bucket_keys_tabelle += str(liste_keys[i].last_modified)
                      bucket_keys_tabelle += '</td>'
                      
                      bucket_keys_tabelle += '</tr>'
                      bucket_keys_tabelle += '<tr>'
                      
                      bucket_keys_tabelle += '<td align="right" colspan="2" bgcolor="#D4D4D4"><b>ACL:</b></td>'
                      bucket_keys_tabelle += '<td align="left">'
                      bucket_keys_tabelle += '<a href="/acl_einsehen?bucket='
                      bucket_keys_tabelle += str(bucketname)
                      bucket_keys_tabelle += '&amp;typ=kompfort'
                      bucket_keys_tabelle += '&amp;key='+str(liste_keys[i].name)
                      bucket_keys_tabelle += '&amp;dir='+str(directory)
                      bucket_keys_tabelle += "&amp;mobile="
                      bucket_keys_tabelle += str(mobile)
                      if sprache == "de":
                        bucket_keys_tabelle += '" title="ACL einsehen/&auml;ndern">ACL einsehen/&auml;ndern</a>'
                      else:
                        bucket_keys_tabelle += '" title="view/edit ACL">view/edit ACL</a>'
                      bucket_keys_tabelle += '</td>'
 
                      # In S3 and Google Storage, each MD5 checksum is enclosed by double quotes.
                      # Eliminate them with .replace('"','') 
                      bucket_keys_tabelle += '<td align="right" bgcolor="#D4D4D4"><b>MD5:</b></td>'
                      bucket_keys_tabelle += '<td align="left">'+str(liste_keys[i].etag.replace('"',''))+'</td>'
                      bucket_keys_tabelle += '</tr>'
                  bucket_keys_tabelle += '</table>'
                  

          # "Verzeichnisse" gehen nur bei Amazon S3
          # Der Grund ist, dass das _$folder$ nicht in Walrus gespeichert werden kann.
          # In Walrus wird das so gespeichert: _%24folder%24
          if regionname in ("Amazon", "GoogleStorage"):
            if mobile == "true":
              # mobile version...
              if sprache == "de":
                eingabeformular_neues_verzeichnis = ''
                eingabeformular_neues_verzeichnis += '<form action="/bucketverzeichniserzeugen" method="post" accept-charset="utf-8">\n'
                eingabeformular_neues_verzeichnis += '<input type="hidden" name="bucket" value="'+str(bucketname)+'">\n'
                eingabeformular_neues_verzeichnis += '<input type="hidden" name="dir" value="'+directory+'">\n'
                eingabeformular_neues_verzeichnis += '<input type="hidden" name="mobile" value="'+mobile+'">'
                eingabeformular_neues_verzeichnis += '<table border="0" cellspacing="0" cellpadding="5">'
                eingabeformular_neues_verzeichnis += '<tr>'
                eingabeformular_neues_verzeichnis += '<td>'
                eingabeformular_neues_verzeichnis += '<input name="verzeichnisname" type="text" size="20" maxlength="25"> '
                eingabeformular_neues_verzeichnis += '</td>'
                eingabeformular_neues_verzeichnis += '</tr>'
                eingabeformular_neues_verzeichnis += '<tr>'
                eingabeformular_neues_verzeichnis += '<td>'
                eingabeformular_neues_verzeichnis += '<input type="submit" value="Neues Verzeichnis erzeugen">\n'
                eingabeformular_neues_verzeichnis += '</td>'
                eingabeformular_neues_verzeichnis += '</tr>'
                eingabeformular_neues_verzeichnis += '</table>'
                eingabeformular_neues_verzeichnis += '</form>\n'
              else:
                eingabeformular_neues_verzeichnis = ''
                eingabeformular_neues_verzeichnis += '<form action="/bucketverzeichniserzeugen" method="post" accept-charset="utf-8">\n'
                eingabeformular_neues_verzeichnis += '<input type="hidden" name="bucket" value="'+str(bucketname)+'">\n'
                eingabeformular_neues_verzeichnis += '<input type="hidden" name="dir" value="'+directory+'">\n'
                eingabeformular_neues_verzeichnis += '<input type="hidden" name="mobile" value="'+mobile+'">'
                eingabeformular_neues_verzeichnis += '<table border="0" cellspacing="0" cellpadding="5">'
                eingabeformular_neues_verzeichnis += '<tr>'
                eingabeformular_neues_verzeichnis += '<td>'
                eingabeformular_neues_verzeichnis += '<input name="verzeichnisname" type="text" size="20" maxlength="25"> '
                eingabeformular_neues_verzeichnis += '</td>'
                eingabeformular_neues_verzeichnis += '</tr>'
                eingabeformular_neues_verzeichnis += '<tr>'
                eingabeformular_neues_verzeichnis += '<td>'
                eingabeformular_neues_verzeichnis += '<input type="submit" value="create new directory">\n'
                eingabeformular_neues_verzeichnis += '</td>'
                eingabeformular_neues_verzeichnis += '</tr>'
                eingabeformular_neues_verzeichnis += '</table>'
                eingabeformular_neues_verzeichnis += '</form>\n'
            else:
              # not the mobile version...
              if sprache == "de":
                eingabeformular_neues_verzeichnis = ''
                eingabeformular_neues_verzeichnis += '<form action="/bucketverzeichniserzeugen" method="post" accept-charset="utf-8">\n'
                eingabeformular_neues_verzeichnis += '<input type="hidden" name="bucket" value="'+str(bucketname)+'">\n'
                eingabeformular_neues_verzeichnis += '<input type="hidden" name="dir" value="'+directory+'">\n'
                eingabeformular_neues_verzeichnis += '<input name="verzeichnisname" type="text" size="25" maxlength="25"> '
                eingabeformular_neues_verzeichnis += '<input type="submit" value="Neues Verzeichnis erzeugen">\n'
                eingabeformular_neues_verzeichnis += '</form>\n'
              else:
                eingabeformular_neues_verzeichnis = ''
                eingabeformular_neues_verzeichnis += '<form action="/bucketverzeichniserzeugen" method="post" accept-charset="utf-8">\n'
                eingabeformular_neues_verzeichnis += '<input type="hidden" name="bucket" value="'+str(bucketname)+'">\n'
                eingabeformular_neues_verzeichnis += '<input type="hidden" name="dir" value="'+directory+'">\n'
                eingabeformular_neues_verzeichnis += '<input name="verzeichnisname" type="text" size="25" maxlength="25"> '
                eingabeformular_neues_verzeichnis += '<input type="submit" value="create new directory">\n'
                eingabeformular_neues_verzeichnis += '</form>\n'
          else: 
            if sprache == "de":
              eingabeformular_neues_verzeichnis = 'Das Erzeugen von Verzeichnissen funktioniert unter Eucalyptus noch nicht'
            else:
              eingabeformular_neues_verzeichnis = 'The creation of directories is still not working with Eucaplyptus'

          if sprache == "de":
            verzeichnis_warnung = 'In S3 existieren keine Verzeichnisse, sondern nur Keys. S3 ist ein flacher Namensraum. <a href="http://www.s3fox.net" style="color:blue">S3Fox</a> z.B. simuliert Verzeichnisse dadurch, dass bestimmte Keys als Platzhalter f&uuml;r das Verzeichnis dienen. Diese enden auf den Namen <b>_&#36;folder&#36;</b>. Ein Key, der einem Verzeichnis zugeordnet werden soll, hat das folgende Namensschema: <b>verzeichnis/unterverzeichnis/dateiname</b>'
          else:
            verzeichnis_warnung = 'There are no folders within a S3 bucket. S3 is a completely flat name space. However, you can simulate hierarchical folders with clever use of key names. <a href="http://www.s3fox.net" style="color:blue">S3Fox</a> for instance uses keys that end with <b>_&#36;folder&#36;</b> as directory placeholders and. A key that is meant staying inside are folder has a name following this schema <b>folder/subfolder/filename</b>'


          # Hier wird das Policy-Dokument erzeugt
          policy_document = ''
          policy_document = policy_document + '{'
          policy_document = policy_document + '"expiration": "2100-01-01T00:00:00Z",'
          policy_document = policy_document + '"conditions": ['
          policy_document = policy_document + '{"bucket": "'+bucketname+'"},'
          policy_document = policy_document + '["starts-with", "$acl", ""],'
          if mobile == "true":
            if directory == '/':
              policy_document = policy_document + '{"success_action_redirect": "http://koalacloud.appspot.com/bucket_inhalt?mobile=true"},'
            else:
              policy_document = policy_document + '{"success_action_redirect": "http://koalacloud.appspot.com/bucket_inhalt?mobile=true&dir='+directory[:-1]+'"},'
          else:
            if directory == '/':
              policy_document = policy_document + '{"success_action_redirect": "http://koalacloud.appspot.com/bucket_inhalt"},'
            else:
              policy_document = policy_document + '{"success_action_redirect": "http://koalacloud.appspot.com/bucket_inhalt?dir='+directory[:-1]+'"},'
          if directory == '/':
            policy_document = policy_document + '["starts-with", "$key", ""],'
          else:
            policy_document = policy_document + '["starts-with", "$key", "'+directory+'"],'
          policy_document = policy_document + '["starts-with", "$Content-Type", ""]'
          policy_document = policy_document + ']'
          policy_document = policy_document + '}'

          policy = base64.b64encode(policy_document)

          signature = base64.b64encode(hmac.new(AWSSecretAccessKeyId, policy, sha).digest())


#          keys_upload_formular = ''
#          if zugangstyp == "Eucalyptus":
#            endpointurl = endpointurl_erhalten(username,regionname)
#            port = port_erhalten(username,regionname)
#            keys_upload_formular = keys_upload_formular + '<form action="http://'+str(endpointurl)+':'+str(port)+'/services/Walrus/'
#          elif zugangstyp == "GoogleStorage":
#            keys_upload_formular = keys_upload_formular + '<form action="http://commondatastorage.googleapis.com/'
#          else:
#            keys_upload_formular = keys_upload_formular + '<form action="http://s3.amazonaws.com/'
#          keys_upload_formular = keys_upload_formular + bucketname
#          keys_upload_formular = keys_upload_formular + '" method="post" enctype="multipart/form-data">\n'

          keys_upload_formular = ''
          if zugangstyp == "Eucalyptus":
            endpointurl = endpointurl_erhalten(username,regionname)
            port = port_erhalten(username,regionname) 
            keys_upload_formular += '<form action="http://'+str(endpointurl)+':'+str(port)+'/services/Walrus/'
            keys_upload_formular += bucketname
            keys_upload_formular += '" method="post" enctype="multipart/form-data">\n'
          elif zugangstyp == "GoogleStorage":
            keys_upload_formular += '<form action="http://commondatastorage.googleapis.com/'
            keys_upload_formular += bucketname
            keys_upload_formular += '" method="post" enctype="multipart/form-data">\n'
          elif zugangstyp == "HostEuropeCloudStorage":
            keys_upload_formular += '<form action="http://'+bucketname+'.cs.hosteurope.de'
            keys_upload_formular += '" method="post" enctype="multipart/form-data">\n'
          else:
            keys_upload_formular += '<form action="http://s3.amazonaws.com/'
            keys_upload_formular += bucketname
            keys_upload_formular += '" method="post" enctype="multipart/form-data">\n'

          
          if mobile == "true":
            # mobile version...
            keys_upload_formular += '<table border="0" cellspacing="0" cellpadding="5">'
            keys_upload_formular += '<tr>'
            keys_upload_formular += '<td>'
            if directory == '/':
              keys_upload_formular += '<input type="hidden" name="key" value="${filename}">\n'
            else:
              keys_upload_formular += '<input type="hidden" name="key" value="'+directory+'${filename}">\n'            
            keys_upload_formular += '<select name="acl" size="1">\n'
            keys_upload_formular += '<option selected="selected">public-read</option>\n'
            keys_upload_formular += '<option>private</option>\n'
            keys_upload_formular += '<option>public-read-write</option>\n'
            keys_upload_formular += '<option>authenticated-read</option>\n'
            keys_upload_formular += '</select>\n'
            keys_upload_formular += '</td>'
            keys_upload_formular += '</tr>'
            keys_upload_formular += '<tr>'
            keys_upload_formular += '<td>'
            keys_upload_formular += '<select name="Content-Type" size="1">\n'
            keys_upload_formular += '<option selected="selected">application/octet-stream</option>\n'
            keys_upload_formular += '<option>application/pdf</option>\n'
            keys_upload_formular += '<option>application/zip</option>\n'
            keys_upload_formular += '<option>audio/mp4</option>\n'
            keys_upload_formular += '<option>audio/mpeg</option>\n'
            keys_upload_formular += '<option>audio/ogg</option>\n'
            keys_upload_formular += '<option>audio/vorbis</option>\n'
            keys_upload_formular += '<option>image/gif</option>\n'
            keys_upload_formular += '<option>image/jpeg</option>\n'
            keys_upload_formular += '<option>image/png</option>\n'
            keys_upload_formular += '<option>image/tiff</option>\n'
            keys_upload_formular += '<option>text/html</option>\n'
            keys_upload_formular += '<option>text/plain</option>\n'
            keys_upload_formular += '<option>video/mp4</option>\n'
            keys_upload_formular += '<option>video/mpeg</option>\n'
            keys_upload_formular += '<option>video/ogg</option>\n'
            keys_upload_formular += '</select>\n'
            keys_upload_formular += '</td>'
            keys_upload_formular += '</tr>'
            keys_upload_formular += '<tr>'
            keys_upload_formular += '<td>\n'
            if directory == '/':
              keys_upload_formular += '<input type="hidden" name="success_action_redirect" value="http://koalacloud.appspot.com/bucket_inhalt?mobile=true">\n'
            else:
              keys_upload_formular += '<input type="hidden" name="success_action_redirect" value="http://koalacloud.appspot.com/bucket_inhalt?mobile=true&dir='+directory[:-1]+'">\n'     
            keys_upload_formular += '<input type="hidden" name="AWSAccessKeyId" value="'+AWSAccessKeyId+'">\n'
            keys_upload_formular += '<input type="hidden" name="policy" value="'+policy+'">\n'
            keys_upload_formular += '<input type="hidden" name="signature" value="'+signature+'">\n'
            keys_upload_formular += '<input type="file" name="file" size="20">\n'
            keys_upload_formular += '</td>'
            keys_upload_formular += '</tr>'
            keys_upload_formular += '<tr>'
            keys_upload_formular += '<td>'
            if sprache == "de":
              keys_upload_formular += '<input type="submit" value="Objekt in den Bucket hochladen">\n'
            else:
              keys_upload_formular += '<input type="submit" value="upload object into bucket">\n'
            keys_upload_formular += '</td>'
            keys_upload_formular += '</tr>'
            keys_upload_formular += '</table>'
            keys_upload_formular += '</form>'
          else: 
            # Not the mobile version
            keys_upload_formular += '<table border="0" cellspacing="0" cellpadding="5">'
            keys_upload_formular += '<tr>'
            keys_upload_formular += '<td>'
            if directory == '/':
              keys_upload_formular += '<input type="hidden" name="key" value="${filename}">\n'
            else:
              keys_upload_formular += '<input type="hidden" name="key" value="'+directory+'${filename}">\n'  
            keys_upload_formular += '<select name="acl" size="1">\n'
            keys_upload_formular += '<option selected="selected">public-read</option>\n'
            keys_upload_formular += '<option>private</option>\n'
            keys_upload_formular += '<option>public-read-write</option>\n'
            keys_upload_formular += '<option>authenticated-read</option>\n'
            keys_upload_formular += '</select>\n'
            keys_upload_formular += '<select name="Content-Type" size="1">\n'
            keys_upload_formular += '<option selected="selected">application/octet-stream</option>\n'
            keys_upload_formular += '<option>application/pdf</option>\n'
            keys_upload_formular += '<option>application/zip</option>\n'
            keys_upload_formular += '<option>audio/mp4</option>\n'
            keys_upload_formular += '<option>audio/mpeg</option>\n'
            keys_upload_formular += '<option>audio/ogg</option>\n'
            keys_upload_formular += '<option>audio/vorbis</option>\n'
            keys_upload_formular += '<option>image/gif</option>\n'
            keys_upload_formular += '<option>image/jpeg</option>\n'
            keys_upload_formular += '<option>image/png</option>\n'
            keys_upload_formular += '<option>image/tiff</option>\n'
            keys_upload_formular += '<option>text/html</option>\n'
            keys_upload_formular += '<option>text/plain</option>\n'
            keys_upload_formular += '<option>video/mp4</option>\n'
            keys_upload_formular += '<option>video/mpeg</option>\n'
            keys_upload_formular += '<option>video/ogg</option>\n'
            keys_upload_formular += '</select>\n'
            keys_upload_formular += '</td>'
            keys_upload_formular += '</tr>'
            keys_upload_formular += '<tr>'
            keys_upload_formular += '<td>\n'
            if directory == '/':
              keys_upload_formular += '<input type="hidden" name="success_action_redirect" value="http://koalacloud.appspot.com/bucket_inhalt">\n'
            else:
              keys_upload_formular += '<input type="hidden" name="success_action_redirect" value="http://koalacloud.appspot.com/bucket_inhalt?dir='+directory[:-1]+'">\n'
            keys_upload_formular += '<input type="hidden" name="AWSAccessKeyId" value="'+AWSAccessKeyId+'">\n'
            keys_upload_formular += '<input type="hidden" name="policy" value="'+policy+'">\n'
            keys_upload_formular += '<input type="hidden" name="signature" value="'+signature+'">\n'
            keys_upload_formular += '<input type="file" name="file" size="60">\n'
            keys_upload_formular += '</td>'
            keys_upload_formular += '</tr>'
            keys_upload_formular += '<tr>'
            keys_upload_formular += '<td>'
            if sprache == "de":
              keys_upload_formular += '<input type="submit" value="Objekt in den Bucket hochladen">\n'
            else:
              keys_upload_formular += '<input type="submit" value="upload objekt into bucket">\n'
            keys_upload_formular += '</td>'
            keys_upload_formular += '</tr>'
            keys_upload_formular += '</table>'
            keys_upload_formular += '</form>'

          path = '&amp;path=bucket_inhalt&amp;bucket='+bucketname+'&amp;mobile='+mobile

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonen_liste': zonen_liste,
          'bucket_keys_tabelle': bucket_keys_tabelle,
          'input_error_message': input_error_message,
          'bucketname': bucketname,
          'eingabeformular_neues_verzeichnis': eingabeformular_neues_verzeichnis,
          'keys_upload_formular': keys_upload_formular,
          'verzeichnis_warnung': verzeichnis_warnung,
          #'eucalyptus_warnung': eucalyptus_warnung,
          'mobile': mobile,
          'path': path,
          }

          if mobile == "true":
              path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "s3_keys.html")
          else:
              path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "s3_keys.html")
          self.response.out.write(template.render(path,template_values))



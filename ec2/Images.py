#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os

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

from internal.Datastore import *

from dateutil.parser import *

from error_messages import error_messages

from boto.ec2.connection import *

class Images(webapp.RequestHandler):
    def get(self):
        # self.response.out.write('posted!')
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Den Usernamen erfahren
        username = users.get_current_user()
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')
        if not username:
          self.redirect('/')

        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if not results:
          self.redirect('/')
        else:
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache,mobile)
          # So wird der HTML-Code korrekt
          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          #url = users.create_logout_url(self.request.uri)
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache,mobile)
          
          
          # It is Google Storage and not am IaaS  
          if regionname == "GoogleStorage":
            
            path = '&amp;path=images&amp;mobile='+mobile
            
            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'zonen_liste': zonen_liste,
            'path': path,
            }

            if mobile == "true":
                path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "not_implemente_with_google_storage.html")
            else:
                path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "not_implemente_with_google_storage.html")
            self.response.out.write(template.render(path,template_values))


          # It is Host Europe Cloud Storage and not am IaaS  
          elif regionname == "HostEuropeCloudStorage":
            
            path = '&amp;path=zonen&amp;mobile='+mobile
            
            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'zonen_liste': zonen_liste,
            'path': path,
            }

            if mobile == "true":
                path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "not_implemente_with_host_europe_storage.html")
            else:
                path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "not_implemente_with_host_europe_storage.html")
            self.response.out.write(template.render(path,template_values))
            

            
          # It is not Google Storage. It is an IaaS
          else:          
          
          
            # Herausfinden, in welcher Zone wird gerade sind
            # Die Ergebnisse des SELECT durchlaufen (ist nur eins) 
            for result in results:
              zone_in_der_wir_uns_befinden = result.aktivezone
  
            if regionname == "Amazon":
  
              if sprache != "de":
                sprache = "en"
  
              input_error_message = error_messages.get(message, {}).get(sprache)
  
              # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
              if input_error_message == None:
                input_error_message = ""
  
              # Wenn die Nachricht grün formatiert werden soll...
              if message in ("83"):
                # wird sie hier, in der Hilfsfunktion grün formatiert
                input_error_message = format_error_message_green(input_error_message)
              # Ansonsten wird die Nachricht rot formatiert
              elif message in ("84", "85", "86", "87", "88"):
                input_error_message = format_error_message_red(input_error_message)
              else:
                input_error_message = ""
  
              # Nachsehen, ob schon Quick Start Images existieren
              aktivezone = db.GqlQuery("SELECT * FROM KoalaQuickStartAMIs WHERE zone = :zone_db", zone_db=zone_in_der_wir_uns_befinden)
              results = aktivezone.fetch(1000)
              
              
############ Quick Start Images ############              
#              if results:                  
#                # Eine leere Liste mit den AMIs der Quick Start Images erzeugen
#                liste_quickstart_amis = []
#                # Die Ergebnisse des SELECT durchlaufen
#                for result in results:
#                  # Die AMIs der Quick Start Images in die Liste einfügen
#                  liste_quickstart_amis.append(result.ami)
#  
#                liste_quickstart_amis_images = conn_region.get_all_images(image_ids=liste_quickstart_amis)
#                laenge_liste_quickstart_amis_images = len(liste_quickstart_amis_images)
#                
#              else:
#                # Quick Start Images erzeugen
#                # Festlegen, was in den Datastore geschrieben werden soll
#                ami = []
#                zone_temp = "us-east-1"
#                ami.append("ami-4a0df923") # Ubuntu 10.04 LTS 64-bit ebs 
#                ami.append("ami-da0cf8b3") # Ubuntu 10.04 LTS 64-bit instance store 
#                ami.append("ami-480df921") # Ubuntu 10.04 LTS 32-bit ebs 
#                ami.append("ami-a403f7cd") # Ubuntu 10.04 LTS 32-bit instance store  
#                ami.append("ami-548c783d") # Ubuntu 10.10 LTS 64-bit ebs 
#                ami.append("ami-688c7801") # Ubuntu 10.10 LTS 64-bit instance store 
#                ami.append("ami-508c7839") # Ubuntu 10.10 LTS 32-bit ebs 
#                ami.append("ami-1a837773") # Ubuntu 10.10 LTS 32-bit instance store  
#                laenge_liste_ami = len(ami)
#                for i in range(laenge_liste_ami):
#                  quickstart = KoalaQuickStartAMIs(ami=ami[i],
#                                                 zone=zone_temp,
#                                                 user=username)
#                  # In den Datastore schreiben
#                  quickstart.put()
#                  
#                ami = []
#                zone_temp = "eu-west-1"                
#                ami.append("ami-f6340182") # Ubuntu 10.04 LTS 64-bit ebs 
#                ami.append("ami-1e34016a") # Ubuntu 10.04 LTS 64-bit instance store 
#                ami.append("ami-f4340180") # Ubuntu 10.04 LTS 32-bit ebs 
#                ami.append("ami-4a34013e") # Ubuntu 10.04 LTS 32-bit instance store  
#                ami.append("ami-405c6934") # Ubuntu 10.10 LTS 64-bit ebs 
#                ami.append("ami-505c6924") # Ubuntu 10.10 LTS 64-bit instance store 
#                ami.append("ami-465c6932") # Ubuntu 10.10 LTS 32-bit ebs 
#                ami.append("ami-7e5c690a") # Ubuntu 10.10 LTS 32-bit instance store  
#                laenge_liste_ami = len(ami)
#                for i in range(laenge_liste_ami):
#                  quickstart = KoalaQuickStartAMIs(ami=ami[i],
#                                                 zone=zone_temp,
#                                                 user=username)
#                  # In den Datastore schreiben
#                  quickstart.put()
#
#                ami = []
#                zone_temp = "us-west-1"   
#                ami.append("ami-880c5ccd") # Ubuntu 10.04 LTS 64-bit ebs 
#                ami.append("ami-860c5cc3") # Ubuntu 10.04 LTS 64-bit instance store 
#                ami.append("ami-8c0c5cc9") # Ubuntu 10.04 LTS 32-bit ebs 
#                ami.append("ami-e80c5cad") # Ubuntu 10.04 LTS 32-bit instance store  
#                ami.append("ami-ca1f4f8f") # Ubuntu 10.10 LTS 64-bit ebs 
#                ami.append("ami-cc1f4f89") # Ubuntu 10.10 LTS 64-bit instance store 
#                ami.append("ami-c81f4f8d") # Ubuntu 10.10 LTS 32-bit ebs 
#                ami.append("ami-2a1f4f6f") # Ubuntu 10.10 LTS 32-bit instance store  
#                laenge_liste_ami = len(ami)
#                for i in range(laenge_liste_ami):
#                  quickstart = KoalaQuickStartAMIs(ami=ami[i],
#                                                 zone=zone_temp,
#                                                 user=username)
#                  # In den Datastore schreiben
#                  quickstart.put()
#
#                ami = []
#                zone_temp = "ap-southeast-1"   
#                ami.append("ami-06067854") # Ubuntu 10.04 LTS 64-bit ebs 
#                ami.append("ami-14067846") # Ubuntu 10.04 LTS 64-bit instance store 
#                ami.append("ami-00067852") # Ubuntu 10.04 LTS 32-bit ebs 
#                ami.append("ami-60067832") # Ubuntu 10.04 LTS 32-bit instance store 
#                ami.append("ami-68136d3a") # Ubuntu 10.10 LTS 64-bit ebs 
#                ami.append("ami-64136d36") # Ubuntu 10.10 LTS 64-bit instance store 
#                ami.append("ami-6a136d38") # Ubuntu 10.10 LTS 32-bit ebs 
#                ami.append("ami-7c136d2e") # Ubuntu 10.10 LTS 32-bit instance store  
#                laenge_liste_ami = len(ami)
#                for i in range(laenge_liste_ami):
#                  quickstart = KoalaQuickStartAMIs(ami=ami[i],
#                                                 zone=zone_temp,
#                                                 user=username)
#                  
#                ami = []
#                zone_temp = "ap-northeast-1"   
#                ami.append("ami-8e08a38f") # Basic 32-bit Amazon Linux AMI 2010.11.1 Beta
#                ami.append("ami-9008a391") # Basic 64-bit Amazon Linux AMI 2010.11.1 Beta
#                laenge_liste_ami = len(ami)
#                for i in range(laenge_liste_ami):
#                  quickstart = KoalaQuickStartAMIs(ami=ami[i],
#                                                 zone=zone_temp,
#                                                 user=username)
#                  
#                  # In den Datastore schreiben
#                  quickstart.put()
#                  
#                aktivezone = db.GqlQuery("SELECT * FROM KoalaQuickStartAMIs WHERE zone = :zone_db", zone_db=zone_in_der_wir_uns_befinden)
#                results = aktivezone.fetch(1000)
#
#                # Eine leere Liste mit den AMIs der Quick Start Images erzeugen
#                liste_quickstart_amis = []
#                # Die Ergebnisse des SELECT durchlaufen
#                for result in results:
#                  # Die AMIs der Quick Start Images in die Liste einfügen
#                  liste_quickstart_amis.append(result.ami)
#  
#                liste_quickstart_amis_images = conn_region.get_all_images(image_ids=liste_quickstart_amis)
#                laenge_liste_quickstart_amis_images = len(liste_quickstart_amis_images)

                
                
              # Nachsehen, ob schon AMI-Favoriten existieren
              aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankFavouritenAMIs WHERE user = :username_db AND zone = :zone_db", username_db=username, zone_db=zone_in_der_wir_uns_befinden)
              results = aktivezone.fetch(100)
              if not results:
                if sprache == "de":
                  liste_favouriten = 'Sie haben noch keine Favoriten in der Zone '
                  liste_favouriten += zone_in_der_wir_uns_befinden+' festgelegt'
                else:
                  liste_favouriten = 'You have still no favourite AMIs inside the zone '
                  liste_favouriten += zone_in_der_wir_uns_befinden
              else:
                # Eine leere Liste mit den AMIs der Favoriten erzeugen
                liste_ami_favoriten = []
                # Die Ergebnisse des SELECT durchlaufen
                for result in results:
                  
                  try:
                    # Liste mit den Images
                    liste_images = conn_region.get_all_images(image_ids=str(result.ami))
                  except:
                    # Wenn es nicht klappt...
                    # Favorit aus dem Datastore holen
                    holen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankFavouritenAMIs WHERE user = :username_db AND ami = :ami_db AND zone = :zone_db", username_db=username, ami_db=str(result.ami), zone_db=zone_in_der_wir_uns_befinden)
                    holenresults = holen.fetch(100)
                    for holenresult in holenresults:
                      # Favorit aus dem Datastore löschen
                      holenresult.delete()
                  else:
                    # Wenn es geklappt hat...                                
                  
                    # Die AMIs in die Liste einfügen
                    liste_ami_favoriten.append(result.ami)
                    
                
                # Wenn die Liste vollständig ist... 
                liste_favoriten_ami_images = conn_region.get_all_images(image_ids=liste_ami_favoriten)
                laenge_liste_favoriten_ami_images = len(liste_favoriten_ami_images)
  
                if mobile == "true":
                  # mobile version
                  liste_favouriten = ''
                  liste_favouriten += '<table border="0" cellspacing="0" cellpadding="5" width="300">'
                  
                  counter = 0
                  for i in range(laenge_liste_favoriten_ami_images):
                      if counter > 0:
                          liste_favouriten += '<tr><td colspan="4">&nbsp;</td></tr>'
                      counter += 1
                      
                      liste_favouriten += '<tr>'
                      #liste_favouriten += '<td>&nbsp;</td>'
                      liste_favouriten += '<td>'
                      if liste_favoriten_ami_images[i].type == u'machine':
                        if sprache == "de":
                          liste_favouriten += '<a href="/imagestarten?image='
                          liste_favouriten += liste_favoriten_ami_images[i].id
                          liste_favouriten += '&amp;arch='
                          liste_favouriten += liste_favoriten_ami_images[i].architecture
                          liste_favouriten += '&amp;root='
                          liste_favouriten += liste_favoriten_ami_images[i].root_device_type
                          liste_favouriten += "&amp;mobile="
                          liste_favouriten +=  str(mobile)
                          liste_favouriten += '"title="Instanz starten"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Instanz starten"></a>'
                        else:
                          liste_favouriten += '<a href="/imagestarten?image='
                          liste_favouriten += liste_favoriten_ami_images[i].id
                          liste_favouriten += '&amp;arch='
                          liste_favouriten += liste_favoriten_ami_images[i].architecture
                          liste_favouriten += '&amp;root='
                          liste_favouriten += liste_favoriten_ami_images[i].root_device_type
                          liste_favouriten += "&amp;mobile="
                          liste_favouriten +=  str(mobile)
                          liste_favouriten += '"title="start instance"><img src="bilder/plus.png" width="16" height="16" border="0" alt="start instance"></a>'
                      else:
                        # Wenn es kein Machine-Image ist, dann das Feld leer lassen
                        liste_favouriten += '&nbsp;'
                      liste_favouriten += '</td>'
                      
                      liste_favouriten += '<td align="center">'
                      beschreibung_in_kleinbuchstaben = liste_favoriten_ami_images[i].location.lower()
                      if beschreibung_in_kleinbuchstaben.find('fedora') != -1:
                        liste_favouriten += '<img src="bilder/fedora_icon_48.png" width="24" height="24" border="0" alt="Fedora">'
                      elif beschreibung_in_kleinbuchstaben.find('ubuntu') != -1:
                        liste_favouriten += '<img src="bilder/ubuntu_icon_48.png" width="24" height="24" border="0" alt="Ubuntu">'
                      elif beschreibung_in_kleinbuchstaben.find('debian') != -1:
                        liste_favouriten += '<img src="bilder/debian_icon_48.png" width="24" height="24" border="0" alt="Debian">'
                      elif beschreibung_in_kleinbuchstaben.find('gentoo') != -1:
                        liste_favouriten += '<img src="bilder/gentoo_icon_48.png" width="24" height="24" border="0" alt="Gentoo">'
                      elif beschreibung_in_kleinbuchstaben.find('suse') != -1:
                        liste_favouriten += '<img src="bilder/suse_icon_48.png" width="24" height="24" border="0" alt="SUSE">'
                      elif beschreibung_in_kleinbuchstaben.find('centos') != -1:
                        liste_favouriten += '<img src="bilder/centos_icon_48.png" width="24" height="24" border="0" alt="CentOS">'
                      elif beschreibung_in_kleinbuchstaben.find('redhat') != -1:
                        liste_favouriten += '<img src="bilder/redhat_icon_48.png" width="24" height="24" border="0" alt="RedHat">'
                      elif beschreibung_in_kleinbuchstaben.find('windows') != -1:
                        liste_favouriten += '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                      elif beschreibung_in_kleinbuchstaben.find('win') != -1:
                        liste_favouriten += '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                      elif beschreibung_in_kleinbuchstaben.find('opensolaris') != -1:
                        liste_favouriten += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                      elif beschreibung_in_kleinbuchstaben.find('solaris') != -1:
                        liste_favouriten += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                      elif beschreibung_in_kleinbuchstaben.find('osol') != -1:
                        liste_favouriten += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                      else:
                        liste_favouriten += '<img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Other Linux">'
                      liste_favouriten += '</td>'

                      liste_favouriten += '<td align="right">'
                      if sprache == "de":
                        liste_favouriten += '<a href="/favoritentfernen?ami='
                        liste_favouriten += liste_favoriten_ami_images[i].id
                        liste_favouriten += '&amp;zone='
                        liste_favouriten += zone_in_der_wir_uns_befinden
                        liste_favouriten += "&amp;mobile="
                        liste_favouriten +=  str(mobile)
                        liste_favouriten += '"title="Favorit entfernen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Favorit entfernen"></a>'
                      else:
                        liste_favouriten += '<a href="/favoritentfernen?ami='
                        liste_favouriten += liste_favoriten_ami_images[i].id
                        liste_favouriten += '&amp;zone='
                        liste_favouriten += zone_in_der_wir_uns_befinden
                        liste_favouriten += "&amp;mobile="
                        liste_favouriten +=  str(mobile)
                        liste_favouriten += '"title="erase from list"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase from list"></a>'
                      liste_favouriten += '</td>'

                      # Hier kommt die Spalte mit der Image-ID
                      liste_favouriten += '<td align="center">'+str(liste_favoriten_ami_images[i].id)+'</td>'

   
                      liste_favouriten += '</tr>'
                      liste_favouriten += '<tr>'
    
                      if sprache == "de":
                        liste_favouriten += '<td align="right" colspan="3"><b>Typ:</b></td>'
                      else:
                        liste_favouriten += '<td align="right" colspan="3"><b>Type:</b></td>'
                      # Hier kommt die Spalte mit dem Instanztyp
                      liste_favouriten += '<td align="center">'+str(liste_favoriten_ami_images[i].type)+'</td>'
                    
                      liste_favouriten += '</tr>'
                      liste_favouriten += '<tr>'
                    
                      liste_favouriten += '<td align="right" colspan="3"><b>Manifest:</b></td>'
                      # Hier kommt die Spalte mit der Manifest-Datei
                      liste_favouriten += '<td align="center">'+str(liste_favoriten_ami_images[i].location)+'</td>'
                      
                      liste_favouriten += '</tr>'
                      liste_favouriten += '<tr>'
                      
                      if sprache == "de":
                        liste_favouriten += '<td align="right" colspan="3"><b>Architektur:</b></td>'
                      else:
                        liste_favouriten += '<td align="right" colspan="3"><b>Architecture:</b></td>'
                      liste_favouriten += '<td align="center">'+str(liste_favoriten_ami_images[i].architecture)+'</td>'
                      
                      liste_favouriten += '</tr>'
                      liste_favouriten += '<tr>'
                      
                      liste_favouriten += '<td align="right" colspan="3"><b>Status:</b></td>'                         
                      if liste_favoriten_ami_images[i].state == u'available':
                        liste_favouriten += '<td bgcolor="#c3ddc3" align="center" colspan="2">'+str(liste_favoriten_ami_images[i].state)+'</td>'
                      else:
                        liste_favouriten += '<td align="center">'+str(liste_favoriten_ami_images[i].state)+'</td>'
                      
                      liste_favouriten += '</tr>'
                      liste_favouriten += '<tr>'
                      
                      liste_favouriten += '<td align="right" colspan="3"><b>Root:</b></td>'     
                      liste_favouriten += '<td align="center">'+liste_favoriten_ami_images[i].root_device_type+'</td>'                  
                      
                      liste_favouriten += '</tr>'
                      liste_favouriten += '<tr>'
                      
                      if sprache == "de":
                        liste_favouriten += '<td align="right" colspan="3"><b>Besitzer:</b></td>'
                      else:
                        liste_favouriten += '<td align="right" colspan="3"><b>Owner:</b></td>'
                      liste_favouriten += '<td align="center">'+str(liste_favoriten_ami_images[i].ownerId)+'</td>'
                      liste_favouriten += '</tr>'
                  liste_favouriten += '</table>'
                  
                else:
                  # not the mobile version
                  liste_favouriten = ''
                  liste_favouriten += '<table border="0" cellspacing="0" cellpadding="5" width="600">'
                  
                  counter = 0
                  for i in range(laenge_liste_favoriten_ami_images):
                      if counter > 0:
                          liste_favouriten += '<tr><td colspan="6">&nbsp;</td></tr>'
                      counter += 1
                      
                      liste_favouriten += '<tr>'
                      #liste_favouriten += '<td>&nbsp;</td>'
                      liste_favouriten += '<td bgcolor="#D4D4D4">'
                      if liste_favoriten_ami_images[i].type == u'machine':
                        if sprache == "de":
                          liste_favouriten += '<a href="/imagestarten?image='
                          liste_favouriten += liste_favoriten_ami_images[i].id
                          liste_favouriten += '&amp;arch='
                          liste_favouriten += liste_favoriten_ami_images[i].architecture
                          liste_favouriten += '&amp;root='
                          liste_favouriten += liste_favoriten_ami_images[i].root_device_type
                          liste_favouriten += "&amp;mobile="
                          liste_favouriten +=  str(mobile)
                          liste_favouriten += '"title="Instanz starten"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Instanz starten"></a>'
                        else:
                          liste_favouriten += '<a href="/imagestarten?image='
                          liste_favouriten += liste_favoriten_ami_images[i].id
                          liste_favouriten += '&amp;arch='
                          liste_favouriten += liste_favoriten_ami_images[i].architecture
                          liste_favouriten += '&amp;root='
                          liste_favouriten += liste_favoriten_ami_images[i].root_device_type
                          liste_favouriten += "&amp;mobile="
                          liste_favouriten +=  str(mobile)
                          liste_favouriten += '"title="start instance"><img src="bilder/plus.png" width="16" height="16" border="0" alt="start instance"></a>'
                      else:
                        # Wenn es kein Machine-Image ist, dann das Feld leer lassen
                        liste_favouriten += '&nbsp;'
                      liste_favouriten += '</td>'
                      
                      liste_favouriten += '<td align="center" bgcolor="#D4D4D4">'
                      beschreibung_in_kleinbuchstaben = liste_favoriten_ami_images[i].location.lower()
                      if beschreibung_in_kleinbuchstaben.find('fedora') != -1:
                        liste_favouriten += '<img src="bilder/fedora_icon_48.png" width="24" height="24" border="0" alt="Fedora">'
                      elif beschreibung_in_kleinbuchstaben.find('ubuntu') != -1:
                        liste_favouriten += '<img src="bilder/ubuntu_icon_48.png" width="24" height="24" border="0" alt="Ubuntu">'
                      elif beschreibung_in_kleinbuchstaben.find('debian') != -1:
                        liste_favouriten += '<img src="bilder/debian_icon_48.png" width="24" height="24" border="0" alt="Debian">'
                      elif beschreibung_in_kleinbuchstaben.find('gentoo') != -1:
                        liste_favouriten += '<img src="bilder/gentoo_icon_48.png" width="24" height="24" border="0" alt="Gentoo">'
                      elif beschreibung_in_kleinbuchstaben.find('suse') != -1:
                        liste_favouriten += '<img src="bilder/suse_icon_48.png" width="24" height="24" border="0" alt="SUSE">'
                      elif beschreibung_in_kleinbuchstaben.find('centos') != -1:
                        liste_favouriten += '<img src="bilder/centos_icon_48.png" width="24" height="24" border="0" alt="CentOS">'
                      elif beschreibung_in_kleinbuchstaben.find('redhat') != -1:
                        liste_favouriten += '<img src="bilder/redhat_icon_48.png" width="24" height="24" border="0" alt="RedHat">'
                      elif beschreibung_in_kleinbuchstaben.find('windows') != -1:
                        liste_favouriten += '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                      elif beschreibung_in_kleinbuchstaben.find('win') != -1:
                        liste_favouriten += '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                      elif beschreibung_in_kleinbuchstaben.find('opensolaris') != -1:
                        liste_favouriten += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                      elif beschreibung_in_kleinbuchstaben.find('solaris') != -1:
                        liste_favouriten += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                      elif beschreibung_in_kleinbuchstaben.find('osol') != -1:
                        liste_favouriten += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                      else:
                        liste_favouriten += '<img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Other Linux">'
                      liste_favouriten += '</td>'

                      liste_favouriten += '<td align="right" bgcolor="#D4D4D4">'
                      if sprache == "de":
                        liste_favouriten += '<a href="/favoritentfernen?ami='
                        liste_favouriten += liste_favoriten_ami_images[i].id
                        liste_favouriten += '&amp;zone='
                        liste_favouriten += zone_in_der_wir_uns_befinden
                        liste_favouriten += "&amp;mobile="
                        liste_favouriten +=  str(mobile)
                        liste_favouriten += '"title="Favorit entfernen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Favorit entfernen"></a>'
                      else:
                        liste_favouriten += '<a href="/favoritentfernen?ami='
                        liste_favouriten += liste_favoriten_ami_images[i].id
                        liste_favouriten += '&amp;zone='
                        liste_favouriten += zone_in_der_wir_uns_befinden
                        liste_favouriten += "&amp;mobile="
                        liste_favouriten +=  str(mobile)
                        liste_favouriten += '"title="erase from list"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase from list"></a>'
                      liste_favouriten += '</td>'
                      
                      liste_favouriten += '<td colspan="3" bgcolor="#D4D4D4">&nbsp;</td>'
   
                      liste_favouriten += '</tr>'
                      liste_favouriten += '<tr>'
                      
                      liste_favouriten += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>ID:</b></td>'  
                      # Hier kommt die Spalte mit der Image-ID
                      liste_favouriten += '<td align="left">'+str(liste_favoriten_ami_images[i].id)+'</td>'

                      liste_favouriten += '<td align="right" bgcolor="#D4D4D4"><b>Status:</b></td>'                         
                      if liste_favoriten_ami_images[i].state == u'available':
                        liste_favouriten += '<td bgcolor="#c3ddc3" align="left" colspan="2">'+str(liste_favoriten_ami_images[i].state)+'</td>'
                      else:
                        liste_favouriten += '<td align="left">'+str(liste_favoriten_ami_images[i].state)+'</td>'
   
                      liste_favouriten += '</tr>'
                      liste_favouriten += '<tr>'
                                            
                      if sprache == "de":
                        liste_favouriten += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Architektur:</b></td>'
                      else:
                        liste_favouriten += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Architecture:</b></td>'
                      liste_favouriten += '<td align="left">'+str(liste_favoriten_ami_images[i].architecture)+'</td>'
                                           
                      if sprache == "de":
                        liste_favouriten += '<td align="right" bgcolor="#D4D4D4"><b>Typ:</b></td>'
                      else:
                        liste_favouriten += '<td align="right" bgcolor="#D4D4D4"><b>Type:</b></td>'
                      # Hier kommt die Spalte mit dem Instanztyp
                      liste_favouriten += '<td align="left">'+str(liste_favoriten_ami_images[i].type)+'</td>'
                    
                      liste_favouriten += '</tr>'
                      liste_favouriten += '<tr>'
                      
                      liste_favouriten += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Root:</b></td>'     
                      liste_favouriten += '<td align="left">'+liste_favoriten_ami_images[i].root_device_type+'</td>'                  
                      
                      if sprache == "de":
                        liste_favouriten += '<td align="right" bgcolor="#D4D4D4"><b>Besitzer:</b></td>'
                      else:
                        liste_favouriten += '<td align="right" bgcolor="#D4D4D4"><b>Owner:</b></td>'
                      liste_favouriten += '<td align="left">'+str(liste_favoriten_ami_images[i].ownerId)+'</td>'

                      liste_favouriten += '</tr>'
                      liste_favouriten += '<tr>'
                      
                      liste_favouriten += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Manifest:</b></td>'
                      # Hier kommt die Spalte mit der Manifest-Datei
                      liste_favouriten += '<td align="left" colspan="3">'+str(liste_favoriten_ami_images[i].location)+'</td>'

                      liste_favouriten += '</tr>'
                  liste_favouriten += '</table>'
                  

############ Quick Start Images ############    
#              if mobile == "true":
#                # mobile version
#                quickstart_tabelle = ''
#                quickstart_tabelle += '<table border="0" cellspacing="0" cellpadding="5" width="300">'
#                
#                counter = 0
#                for i in range(laenge_liste_quickstart_amis_images):
#                    if counter > 0:
#                        quickstart_tabelle += '<tr><td colspan="4">&nbsp;</td></tr>'
#                    counter += 1
#                    
#                    quickstart_tabelle += '<tr>'
#                    #quickstart_tabelle += '<td>&nbsp;</td>'
#                    quickstart_tabelle += '<td>'
#                    if liste_quickstart_amis_images[i].type == u'machine':
#                      if sprache == "de":
#                        quickstart_tabelle += '<a href="/imagestarten?image='
#                        quickstart_tabelle += liste_quickstart_amis_images[i].id
#                        quickstart_tabelle += '&amp;arch='
#                        quickstart_tabelle += liste_quickstart_amis_images[i].architecture
#                        quickstart_tabelle += '&amp;root='
#                        quickstart_tabelle += liste_quickstart_amis_images[i].root_device_type
#                        quickstart_tabelle += "&amp;mobile="
#                        quickstart_tabelle +=  str(mobile)
#                        quickstart_tabelle += '"title="Instanz starten"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Instanz starten"></a>'
#                      else:
#                        quickstart_tabelle += '<a href="/imagestarten?image='
#                        quickstart_tabelle += liste_quickstart_amis_images[i].id
#                        quickstart_tabelle += '&amp;arch='
#                        quickstart_tabelle += liste_quickstart_amis_images[i].architecture
#                        quickstart_tabelle += '&amp;root='
#                        quickstart_tabelle += liste_quickstart_amis_images[i].root_device_type
#                        quickstart_tabelle += "&amp;mobile="
#                        quickstart_tabelle +=  str(mobile)
#                        quickstart_tabelle += '"title="start instance"><img src="bilder/plus.png" width="16" height="16" border="0" alt="start instance"></a>'
#                    else:
#                      # Wenn es kein Machine-Image ist, dann das Feld leer lassen
#                      quickstart_tabelle += '&nbsp;'
#                    quickstart_tabelle += '</td>'
#                    
#                    quickstart_tabelle += '<td align="center">'
#                    beschreibung_in_kleinbuchstaben = liste_quickstart_amis_images[i].location.lower()
#                    if beschreibung_in_kleinbuchstaben.find('fedora') != -1:
#                      quickstart_tabelle += '<img src="bilder/fedora_icon_48.png" width="24" height="24" border="0" alt="Fedora">'
#                    elif beschreibung_in_kleinbuchstaben.find('ubuntu') != -1:
#                      quickstart_tabelle += '<img src="bilder/ubuntu_icon_48.png" width="24" height="24" border="0" alt="Ubuntu">'
#                    elif beschreibung_in_kleinbuchstaben.find('debian') != -1:
#                      quickstart_tabelle += '<img src="bilder/debian_icon_48.png" width="24" height="24" border="0" alt="Debian">'
#                    elif beschreibung_in_kleinbuchstaben.find('gentoo') != -1:
#                      quickstart_tabelle += '<img src="bilder/gentoo_icon_48.png" width="24" height="24" border="0" alt="Gentoo">'
#                    elif beschreibung_in_kleinbuchstaben.find('suse') != -1:
#                      quickstart_tabelle += '<img src="bilder/suse_icon_48.png" width="24" height="24" border="0" alt="SUSE">'
#                    elif beschreibung_in_kleinbuchstaben.find('centos') != -1:
#                      quickstart_tabelle += '<img src="bilder/centos_icon_48.png" width="24" height="24" border="0" alt="CentOS">'
#                    elif beschreibung_in_kleinbuchstaben.find('redhat') != -1:
#                      quickstart_tabelle += '<img src="bilder/redhat_icon_48.png" width="24" height="24" border="0" alt="RedHat">'
#                    elif beschreibung_in_kleinbuchstaben.find('windows') != -1:
#                      quickstart_tabelle += '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
#                    elif beschreibung_in_kleinbuchstaben.find('win') != -1:
#                      quickstart_tabelle += '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
#                    elif beschreibung_in_kleinbuchstaben.find('opensolaris') != -1:
#                      quickstart_tabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
#                    elif beschreibung_in_kleinbuchstaben.find('solaris') != -1:
#                      quickstart_tabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
#                    elif beschreibung_in_kleinbuchstaben.find('osol') != -1:
#                      quickstart_tabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
#                    else:
#                      quickstart_tabelle += '<img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Other Linux">'
#                    quickstart_tabelle += '</td>'
#
#                    quickstart_tabelle += '<td align="right">'
#                    if sprache == "de":
#                      quickstart_tabelle += '<a href="/favoritentfernen?ami='
#                      quickstart_tabelle += liste_quickstart_amis_images[i].id
#                      quickstart_tabelle += '&amp;zone='
#                      quickstart_tabelle += zone_in_der_wir_uns_befinden
#                      quickstart_tabelle += "&amp;mobile="
#                      quickstart_tabelle +=  str(mobile)
#                      quickstart_tabelle += '"title="Favorit entfernen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Favorit entfernen"></a>'
#                    else:
#                      quickstart_tabelle += '<a href="/favoritentfernen?ami='
#                      quickstart_tabelle += liste_quickstart_amis_images[i].id
#                      quickstart_tabelle += '&amp;zone='
#                      quickstart_tabelle += zone_in_der_wir_uns_befinden
#                      quickstart_tabelle += "&amp;mobile="
#                      quickstart_tabelle +=  str(mobile)
#                      quickstart_tabelle += '"title="erase from list"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase from list"></a>'
#                    quickstart_tabelle += '</td>'
#
#                    # Hier kommt die Spalte mit der Image-ID
#                    quickstart_tabelle += '<td align="center">'+str(liste_quickstart_amis_images[i].id)+'</td>'
#
# 
#                    quickstart_tabelle += '</tr>'
#                    quickstart_tabelle += '<tr>'
#  
#                    if sprache == "de":
#                      quickstart_tabelle += '<td align="right" colspan="3"><b>Typ:</b></td>'
#                    else:
#                      quickstart_tabelle += '<td align="right" colspan="3"><b>Type:</b></td>'
#                    # Hier kommt die Spalte mit dem Instanztyp
#                    quickstart_tabelle += '<td align="center">'+str(liste_quickstart_amis_images[i].type)+'</td>'
#                  
#                    quickstart_tabelle += '</tr>'
#                    quickstart_tabelle += '<tr>'
#                  
#                    quickstart_tabelle += '<td align="right" colspan="3"><b>Manifest:</b></td>'
#                    # Hier kommt die Spalte mit der Manifest-Datei
#                    quickstart_tabelle += '<td align="center">'+str(liste_quickstart_amis_images[i].location)+'</td>'
#                    
#                    quickstart_tabelle += '</tr>'
#                    quickstart_tabelle += '<tr>'
#                    
#                    if sprache == "de":
#                      quickstart_tabelle += '<td align="right" colspan="3"><b>Architektur:</b></td>'
#                    else:
#                      quickstart_tabelle += '<td align="right" colspan="3"><b>Architecture:</b></td>'
#                    quickstart_tabelle += '<td align="center">'+str(liste_quickstart_amis_images[i].architecture)+'</td>'
#                    
#                    quickstart_tabelle += '</tr>'
#                    quickstart_tabelle += '<tr>'
#                    
#                    quickstart_tabelle += '<td align="right" colspan="3"><b>Status:</b></td>'                         
#                    if liste_quickstart_amis_images[i].state == u'available':
#                      quickstart_tabelle += '<td bgcolor="#c3ddc3" align="center" colspan="2">'+str(liste_quickstart_amis_images[i].state)+'</td>'
#                    else:
#                      quickstart_tabelle += '<td align="center">'+str(liste_quickstart_amis_images[i].state)+'</td>'
#                    
#                    quickstart_tabelle += '</tr>'
#                    quickstart_tabelle += '<tr>'
#                    
#                    quickstart_tabelle += '<td align="right" colspan="3"><b>Root:</b></td>'     
#                    quickstart_tabelle += '<td align="center">'+liste_quickstart_amis_images[i].root_device_type+'</td>'                  
#                    
#                    quickstart_tabelle += '</tr>'
#                    quickstart_tabelle += '<tr>'
#                    
#                    if sprache == "de":
#                      quickstart_tabelle += '<td align="right" colspan="3"><b>Besitzer:</b></td>'
#                    else:
#                      quickstart_tabelle += '<td align="right" colspan="3"><b>Owner:</b></td>'
#                    quickstart_tabelle += '<td align="center">'+str(liste_quickstart_amis_images[i].ownerId)+'</td>'
#                    quickstart_tabelle += '</tr>'
#                quickstart_tabelle += '</table>'
#                
#              else:
#                # not the mobile version
#                quickstart_tabelle = ''
#                quickstart_tabelle += '<table border="0" cellspacing="0" cellpadding="5" width="600">'
#                
#                counter = 0
#                for i in range(laenge_liste_quickstart_amis_images):
#                    if counter > 0:
#                        quickstart_tabelle += '<tr><td colspan="6">&nbsp;</td></tr>'
#                    counter += 1
#                    
#                    quickstart_tabelle += '<tr>'
#                    #quickstart_tabelle += '<td>&nbsp;</td>'
#                    quickstart_tabelle += '<td bgcolor="#D4D4D4">'
#                    if liste_quickstart_amis_images[i].type == u'machine':
#                      if sprache == "de":
#                        quickstart_tabelle += '<a href="/imagestarten?image='
#                        quickstart_tabelle += liste_quickstart_amis_images[i].id
#                        quickstart_tabelle += '&amp;arch='
#                        quickstart_tabelle += liste_quickstart_amis_images[i].architecture
#                        quickstart_tabelle += '&amp;root='
#                        quickstart_tabelle += liste_quickstart_amis_images[i].root_device_type
#                        quickstart_tabelle += "&amp;mobile="
#                        quickstart_tabelle +=  str(mobile)
#                        quickstart_tabelle += '"title="Instanz starten"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Instanz starten"></a>'
#                      else:
#                        quickstart_tabelle += '<a href="/imagestarten?image='
#                        quickstart_tabelle += liste_quickstart_amis_images[i].id
#                        quickstart_tabelle += '&amp;arch='
#                        quickstart_tabelle += liste_quickstart_amis_images[i].architecture
#                        quickstart_tabelle += '&amp;root='
#                        quickstart_tabelle += liste_quickstart_amis_images[i].root_device_type
#                        quickstart_tabelle += "&amp;mobile="
#                        quickstart_tabelle +=  str(mobile)
#                        quickstart_tabelle += '"title="start instance"><img src="bilder/plus.png" width="16" height="16" border="0" alt="start instance"></a>'
#                    else:
#                      # Wenn es kein Machine-Image ist, dann das Feld leer lassen
#                      quickstart_tabelle += '&nbsp;'
#                    quickstart_tabelle += '</td>'
#                    
#                    quickstart_tabelle += '<td align="center" bgcolor="#D4D4D4">'
#                    beschreibung_in_kleinbuchstaben = liste_quickstart_amis_images[i].location.lower()
#                    if beschreibung_in_kleinbuchstaben.find('fedora') != -1:
#                      quickstart_tabelle += '<img src="bilder/fedora_icon_48.png" width="24" height="24" border="0" alt="Fedora">'
#                    elif beschreibung_in_kleinbuchstaben.find('ubuntu') != -1:
#                      quickstart_tabelle += '<img src="bilder/ubuntu_icon_48.png" width="24" height="24" border="0" alt="Ubuntu">'
#                    elif beschreibung_in_kleinbuchstaben.find('debian') != -1:
#                      quickstart_tabelle += '<img src="bilder/debian_icon_48.png" width="24" height="24" border="0" alt="Debian">'
#                    elif beschreibung_in_kleinbuchstaben.find('gentoo') != -1:
#                      quickstart_tabelle += '<img src="bilder/gentoo_icon_48.png" width="24" height="24" border="0" alt="Gentoo">'
#                    elif beschreibung_in_kleinbuchstaben.find('suse') != -1:
#                      quickstart_tabelle += '<img src="bilder/suse_icon_48.png" width="24" height="24" border="0" alt="SUSE">'
#                    elif beschreibung_in_kleinbuchstaben.find('centos') != -1:
#                      quickstart_tabelle += '<img src="bilder/centos_icon_48.png" width="24" height="24" border="0" alt="CentOS">'
#                    elif beschreibung_in_kleinbuchstaben.find('redhat') != -1:
#                      quickstart_tabelle += '<img src="bilder/redhat_icon_48.png" width="24" height="24" border="0" alt="RedHat">'
#                    elif beschreibung_in_kleinbuchstaben.find('windows') != -1:
#                      quickstart_tabelle += '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
#                    elif beschreibung_in_kleinbuchstaben.find('win') != -1:
#                      quickstart_tabelle += '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
#                    elif beschreibung_in_kleinbuchstaben.find('opensolaris') != -1:
#                      quickstart_tabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
#                    elif beschreibung_in_kleinbuchstaben.find('solaris') != -1:
#                      quickstart_tabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
#                    elif beschreibung_in_kleinbuchstaben.find('osol') != -1:
#                      quickstart_tabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
#                    else:
#                      quickstart_tabelle += '<img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Other Linux">'
#                    quickstart_tabelle += '</td>'
#                
#                    quickstart_tabelle += '<td align="right" bgcolor="#D4D4D4">'
#                    quickstart_tabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0" alt="">'
#                    quickstart_tabelle += '</td>'
#                    
#                    quickstart_tabelle += '<td colspan="3" bgcolor="#D4D4D4">&nbsp;</td>'
#                
#                    quickstart_tabelle += '</tr>'
#                    quickstart_tabelle += '<tr>'
#                    
#                    quickstart_tabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>ID:</b></td>'  
#                    # Hier kommt die Spalte mit der Image-ID
#                    quickstart_tabelle += '<td align="left">'+str(liste_quickstart_amis_images[i].id)+'</td>'
#                
#                    quickstart_tabelle += '<td align="right" bgcolor="#D4D4D4"><b>Status:</b></td>'                         
#                    if liste_quickstart_amis_images[i].state == u'available':
#                      quickstart_tabelle += '<td bgcolor="#c3ddc3" align="left" colspan="2">'+str(liste_quickstart_amis_images[i].state)+'</td>'
#                    else:
#                      quickstart_tabelle += '<td align="left">'+str(liste_quickstart_amis_images[i].state)+'</td>'
#                
#                    quickstart_tabelle += '</tr>'
#                    quickstart_tabelle += '<tr>'
#                                          
#                    if sprache == "de":
#                      quickstart_tabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Architektur:</b></td>'
#                    else:
#                      quickstart_tabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Architecture:</b></td>'
#                    quickstart_tabelle += '<td align="left">'+str(liste_quickstart_amis_images[i].architecture)+'</td>'
#                                         
#                    if sprache == "de":
#                      quickstart_tabelle += '<td align="right" bgcolor="#D4D4D4"><b>Typ:</b></td>'
#                    else:
#                      quickstart_tabelle += '<td align="right" bgcolor="#D4D4D4"><b>Type:</b></td>'
#                    # Hier kommt die Spalte mit dem Instanztyp
#                    quickstart_tabelle += '<td align="left">'+str(liste_quickstart_amis_images[i].type)+'</td>'
#                  
#                    quickstart_tabelle += '</tr>'
#                    quickstart_tabelle += '<tr>'
#                    
#                    quickstart_tabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Root:</b></td>'     
#                    quickstart_tabelle += '<td align="left">'+liste_quickstart_amis_images[i].root_device_type+'</td>'                  
#                    
#                    if sprache == "de":
#                      quickstart_tabelle += '<td align="right" bgcolor="#D4D4D4"><b>Besitzer:</b></td>'
#                    else:
#                      quickstart_tabelle += '<td align="right" bgcolor="#D4D4D4"><b>Owner:</b></td>'
#                    quickstart_tabelle += '<td align="left">'+str(liste_quickstart_amis_images[i].ownerId)+'</td>'
#                
#                    quickstart_tabelle += '</tr>'
#                    quickstart_tabelle += '<tr>'
#                    
#                    quickstart_tabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Manifest:</b></td>'
#                    # Hier kommt die Spalte mit der Manifest-Datei
#                    quickstart_tabelle += '<td align="left" colspan="3">'+str(liste_quickstart_amis_images[i].location)+'</td>'
#                
#                    quickstart_tabelle += '</tr>'
#                quickstart_tabelle += '</table>'
                  

              path = '&amp;path=images&amp;mobile='+mobile

  
              template_values = {
              'navigations_bar': navigations_bar,
              'url': url,
              'url_linktext': url_linktext,
              'zone': regionname,
              'zone_amazon': zone_amazon,
              'zonen_liste': zonen_liste,
              'liste_favouriten': liste_favouriten,
              'zone_in_der_wir_uns_befinden': zone_in_der_wir_uns_befinden,
              'input_error_message': input_error_message,
#              'quickstart_tabelle': quickstart_tabelle,
              'mobile': mobile,
              'path': path,
              }
  
              if mobile == "true":
                  path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "images_amazon.html")
              else:
                  path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "images_amazon.html")
              self.response.out.write(template.render(path,template_values))
  
            # Die Region ist Eucalyptus oder Nimbus
            else:
  
              try:
                # Liste mit den Images
                liste_images = conn_region.get_all_images()
              except EC2ResponseError:
                # Wenn es nicht klappt...
                if sprache == "de":
                  imagestabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
                else:
                  imagestabelle = '<font color="red">An error occured</font>'
              except DownloadError:
                # Diese Exception hilft gegen diese beiden Fehler:
                # DownloadError: ApplicationError: 2 timed out
                # DownloadError: ApplicationError: 5
                if sprache == "de":
                  imagestabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
                else:
                  imagestabelle = '<font color="red">A timeout error occured</font>'
              else:
                # Wenn es geklappt hat...
                # Anzahl der Images in der Liste
                laenge_liste_images = len(liste_images)
  
                #self.response.out.write(laenge_liste_images)
  
                if laenge_liste_images == 0:
                  # Wenn noch keine Images in der Region existieren
                  if sprache == "de":
                    imagestabelle = 'Es sind keine Images in der Region vorhanden.'
                  else:
                    imagestabelle = 'Still no images exist inside this region.'
                else:                  
                  # Wenn schon Images in der Region existieren
                  
                  if mobile == "true":
                    # This is the mobile version
                    imagestabelle = ''
                    imagestabelle += '<table border="0" cellspacing="0" cellpadding="5" width="300">'
                    
                    counter = 0
                    
                    for i in range(laenge_liste_images):
                      if counter > 0:
                          imagestabelle += '<tr><td colspan="4">&nbsp;</td></tr>'
                      counter += 1
                      
                      imagestabelle += '<tr>'
                      #liste_favouriten += '<td>&nbsp;</td>'
                      imagestabelle += '<td>'
                      if liste_images[i].type == u'machine':
                        if sprache == "de":
                          imagestabelle += '<a href="/imagestarten?image='
                          imagestabelle += liste_images[i].id
                          imagestabelle += "&amp;mobile="
                          imagestabelle +=  str(mobile)
                          imagestabelle += '"title="Instanz starten"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Instanz starten"></a>'
                        else:
                          imagestabelle += '<a href="/imagestarten?image='
                          imagestabelle += liste_images[i].id
                          imagestabelle += "&amp;mobile="
                          imagestabelle +=  str(mobile)
                          imagestabelle += '"title="start instance"><img src="bilder/plus.png" width="16" height="16" border="0" alt="start instance"></a>'
                      else:
                        # Wenn es kein Machine-Image ist, dann das Feld leer lassen
                        imagestabelle += '&nbsp;'
                      imagestabelle += '</td>'
                      
                      imagestabelle += '<td align="center">'
                      beschreibung_in_kleinbuchstaben = liste_images[i].location.lower()
                      if str(liste_images[i].type) == "kernel":
                        imagestabelle += '<img src="bilder/1pixel.gif" width="24" height="24" border="0" alt="">'
                      elif str(liste_images[i].type) == "ramdisk":
                        imagestabelle += '<img src="bilder/1pixel.gif" width="24" height="24" border="0" alt="">'
                      elif str(liste_images[i].type) == "machine":
                        if beschreibung_in_kleinbuchstaben.find('fedora') != -1:
                          imagestabelle += '<img src="bilder/fedora_icon_48.png" width="24" height="24" border="0" alt="Fedora">'
                        elif beschreibung_in_kleinbuchstaben.find('ubuntu') != -1:
                          imagestabelle += '<img src="bilder/ubuntu_icon_48.png" width="24" height="24" border="0" alt="Ubuntu">'
                        elif beschreibung_in_kleinbuchstaben.find('debian') != -1:
                          imagestabelle += '<img src="bilder/debian_icon_48.png" width="24" height="24" border="0" alt="Debian">'
                        elif beschreibung_in_kleinbuchstaben.find('gentoo') != -1:
                          imagestabelle += '<img src="bilder/gentoo_icon_48.png" width="24" height="24" border="0" alt="Gentoo">'
                        elif beschreibung_in_kleinbuchstaben.find('suse') != -1:
                          imagestabelle += '<img src="bilder/suse_icon_48.png" width="24" height="24" border="0" alt="SUSE">'
                        elif beschreibung_in_kleinbuchstaben.find('centos') != -1:
                          imagestabelle += '<img src="bilder/centos_icon_48.png" width="24" height="24" border="0" alt="CentOS">'
                        elif beschreibung_in_kleinbuchstaben.find('redhat') != -1:
                          imagestabelle += '<img src="bilder/redhat_icon_48.png" width="24" height="24" border="0" alt="RedHat">'
                        elif beschreibung_in_kleinbuchstaben.find('windows') != -1:
                          imagestabelle += '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                        elif beschreibung_in_kleinbuchstaben.find('win') != -1:
                          imagestabelle += '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                        elif beschreibung_in_kleinbuchstaben.find('opensolaris') != -1:
                          imagestabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                        elif beschreibung_in_kleinbuchstaben.find('solaris') != -1:
                          imagestabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                        elif beschreibung_in_kleinbuchstaben.find('osol') != -1:
                          imagestabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                        else:
                          imagestabelle += '<img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Other Linux">'
                      else:
                        imagestabelle += '<img src="bilder/1pixel.gif" width="24" height="24" border="0" alt="">'

                      imagestabelle += '<td>&nbsp;</td>'

                      # Hier kommt die Spalte mit der Image-ID
                      imagestabelle += '<td align="center"><tt>'+str(liste_images[i].id)+'</tt></td>'

                      imagestabelle += '<tr>'

                      if sprache == "de":
                        imagestabelle += '<td align="right" colspan="3"><b>Typ:</b></td>'
                      else:
                        imagestabelle += '<td align="right" colspan="3"><b>Type:</b></td>'
                      # Hier kommt die Spalte mit dem Instanztyp
                      imagestabelle += '<td align="center">'+str(liste_images[i].type)+'</td>'
                    
                      imagestabelle += '</tr>'
                      imagestabelle += '<tr>'
                    
                      imagestabelle += '<td align="right" colspan="3"><b>Manifest:</b></td>'
                      # Hier kommt die Spalte mit der Manifest-Datei
                      imagestabelle += '<td><tt>'+str(liste_images[i].location)+'</tt></td>'
                      
                      imagestabelle += '</tr>'
                      imagestabelle += '<tr>'
                      
                      if sprache == "de":
                        imagestabelle += '<td align="right" colspan="3"><b>Architektur:</b></td>'
                      else:
                        imagestabelle += '<td align="right" colspan="3"><b>Architecture:</b></td>'
                      imagestabelle += '<td align="center"><tt>'+str(liste_images[i].architecture)+'</tt></td>'
                      
                      imagestabelle += '</tr>'
                      imagestabelle += '<tr>'
                      
                      imagestabelle += '<td align="right" colspan="3"><b>Status:</b></td>'        
                      if liste_images[i].state == u'available':
                        imagestabelle += '<td bgcolor="#c3ddc3" align="center">'+str(liste_images[i].state)+'</td>'
                      else:
                        imagestabelle += '<td align="center">'+str(liste_images[i].state)+'</td>'
  
                      imagestabelle += '</tr>'
                      imagestabelle += '<tr>'
                      
                      if sprache == "de":
                        imagestabelle += '<td align="right" colspan="3"><b>Besitzer:</b></td>'
                      else:
                        imagestabelle += '<td align="right" colspan="3"><b>Owner:</b></td>'
                      imagestabelle += '<td align="center">'+str(liste_images[i].ownerId)+'</td>'
                      imagestabelle += '</tr>'
                    imagestabelle += '</table>'
                  
                  
                  else:
                    # not the mobile version
                    imagestabelle = ''
                    imagestabelle += '<table border="0" cellspacing="0" cellpadding="5" width="600">'
                    
                    counter = 0
                    
                    for i in range(laenge_liste_images):
                      if counter > 0:
                          imagestabelle += '<tr><td colspan="6">&nbsp;</td></tr>'
                      counter += 1
                      
                      imagestabelle += '<tr>'
                      #liste_favouriten += '<td>&nbsp;</td>'
                      imagestabelle += '<td bgcolor="#D4D4D4">'
                      if liste_images[i].type == u'machine':
                        if sprache == "de":
                          imagestabelle += '<a href="/imagestarten?image='
                          imagestabelle += liste_images[i].id
                          imagestabelle += "&amp;mobile="
                          imagestabelle +=  str(mobile)
                          imagestabelle += '"title="Instanz starten"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Instanz starten"></a>'
                        else:
                          imagestabelle += '<a href="/imagestarten?image='
                          imagestabelle += liste_images[i].id
                          imagestabelle += "&amp;mobile="
                          imagestabelle +=  str(mobile)
                          imagestabelle += '"title="start instance"><img src="bilder/plus.png" width="16" height="16" border="0" alt="start instance"></a>'
                      else:
                        # Wenn es kein Machine-Image ist, dann das Feld leer lassen
                        imagestabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0" alt="">'
                      imagestabelle += '</td>'
                      
                      imagestabelle += '<td align="center" bgcolor="#D4D4D4">'
                      beschreibung_in_kleinbuchstaben = liste_images[i].location.lower()
                      if str(liste_images[i].type) == "kernel":
                        imagestabelle += '<img src="bilder/1pixel.gif" width="24" height="24" border="0" alt="">'
                      elif str(liste_images[i].type) == "ramdisk":
                        imagestabelle += '<img src="bilder/1pixel.gif" width="24" height="24" border="0" alt="">'
                      elif str(liste_images[i].type) == "machine":
                        if beschreibung_in_kleinbuchstaben.find('fedora') != -1:
                          imagestabelle += '<img src="bilder/fedora_icon_48.png" width="24" height="24" border="0" alt="Fedora">'
                        elif beschreibung_in_kleinbuchstaben.find('ubuntu') != -1:
                          imagestabelle += '<img src="bilder/ubuntu_icon_48.png" width="24" height="24" border="0" alt="Ubuntu">'
                        elif beschreibung_in_kleinbuchstaben.find('debian') != -1:
                          imagestabelle += '<img src="bilder/debian_icon_48.png" width="24" height="24" border="0" alt="Debian">'
                        elif beschreibung_in_kleinbuchstaben.find('gentoo') != -1:
                          imagestabelle += '<img src="bilder/gentoo_icon_48.png" width="24" height="24" border="0" alt="Gentoo">'
                        elif beschreibung_in_kleinbuchstaben.find('suse') != -1:
                          imagestabelle += '<img src="bilder/suse_icon_48.png" width="24" height="24" border="0" alt="SUSE">'
                        elif beschreibung_in_kleinbuchstaben.find('centos') != -1:
                          imagestabelle += '<img src="bilder/centos_icon_48.png" width="24" height="24" border="0" alt="CentOS">'
                        elif beschreibung_in_kleinbuchstaben.find('redhat') != -1:
                          imagestabelle += '<img src="bilder/redhat_icon_48.png" width="24" height="24" border="0" alt="RedHat">'
                        elif beschreibung_in_kleinbuchstaben.find('windows') != -1:
                          imagestabelle += '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                        elif beschreibung_in_kleinbuchstaben.find('win') != -1:
                          imagestabelle += '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                        elif beschreibung_in_kleinbuchstaben.find('opensolaris') != -1:
                          imagestabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                        elif beschreibung_in_kleinbuchstaben.find('solaris') != -1:
                          imagestabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                        elif beschreibung_in_kleinbuchstaben.find('osol') != -1:
                          imagestabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                        else:
                          imagestabelle += '<img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Other Linux">'
                      else:
                        imagestabelle += '<img src="bilder/1pixel.gif" width="24" height="24" border="0" alt="">'

                      imagestabelle += '<td bgcolor="#D4D4D4"><img src="bilder/platzhalter.png" width="16" height="16" border="0" alt=""></td>'

                      imagestabelle += '<td align="left" colspan="3" bgcolor="#D4D4D4">&nbsp;</td>'

                      imagestabelle += '</tr>'
                      imagestabelle += '<tr>'
                      
                      # Hier kommt die Spalte mit der Image-ID
                      imagestabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>ID:</b></td>'
                      imagestabelle += '<td align="left">'+str(liste_images[i].id)+'</td>'

                      imagestabelle += '<td align="right" bgcolor="#D4D4D4"><b>Status:</b></td>'        
                      if liste_images[i].state == u'available':
                        imagestabelle += '<td bgcolor="#c3ddc3" align="left">'+str(liste_images[i].state)+'</td>'
                      else:
                        imagestabelle += '<td align="left">'+str(liste_images[i].state)+'</td>'

                      imagestabelle += '</tr>'
                      imagestabelle += '<tr>'

                      if sprache == "de":
                        imagestabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Architektur:</b></td>'
                      else:
                        imagestabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Architecture:</b></td>'
                      imagestabelle += '<td align="left">'+str(liste_images[i].architecture)+'</td>'

                      if sprache == "de":
                        imagestabelle += '<td align="right" bgcolor="#D4D4D4"><b>Typ:</b></td>'
                      else:
                        imagestabelle += '<td align="right" bgcolor="#D4D4D4"><b>Type:</b></td>'
                      # Hier kommt die Spalte mit dem Instanztyp
                      imagestabelle += '<td align="left">'+str(liste_images[i].type)+'</td>'
                      
                      imagestabelle += '</tr>'
                      imagestabelle += '<tr>'
                      
                      if sprache == "de":
                        imagestabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Besitzer:</b></td>'
                      else:
                        imagestabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Owner:</b></td>'
                      imagestabelle += '<td align="left" colspan="3">'+str(liste_images[i].ownerId)+'</td>'
                      
                      imagestabelle += '</tr>'
                      imagestabelle += '<tr>'
                    
                      imagestabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Manifest:</b></td>'
                      # Hier kommt die Spalte mit der Manifest-Datei
                      imagestabelle += '<td align="left" colspan="3">'+str(liste_images[i].location)+'</td>'

                      imagestabelle += '</tr>'
                    imagestabelle += '</table>'
  
              path = '&amp;path=images&amp;mobile='+mobile
  
              template_values = {
              'navigations_bar': navigations_bar,
              'url': url,
              'url_linktext': url_linktext,
              'zone': regionname,
              'zone_amazon': zone_amazon,
              'imagestabelle': imagestabelle,
              'zonen_liste': zonen_liste,
              'mobile': mobile,
              'path': path,
              }
  
              if mobile == "true":
                  path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "images.html")
              else:
                  path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "images.html")
              self.response.out.write(template.render(path,template_values))

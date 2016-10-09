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

from dateutil.parser import *

from error_messages import error_messages

from boto.ec2.connection import *

class Elastic_IPs(webapp.RequestHandler):
    def get(self):
        # self.response.out.write('posted!')
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
          self.redirect('/')
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')

        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if not results:
          self.redirect('/')
        else:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache,mobile)

          # So ist der HTML-Code korrekt
          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          # So ist der HTML-Code nicht korrekt
          #url = users.create_logout_url(self.request.uri)
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache,mobile)

          # It is Google Storage and not am IaaS  
          if regionname == "GoogleStorage":
            
            path = '&amp;path=elastic_ips&amp;mobile='+mobile
            
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
            
            if sprache != "de":
              sprache = "en"
  
            input_error_message = error_messages.get(message, {}).get(sprache)
  
            # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
            if input_error_message == None:
              input_error_message = ""
  
            # Wenn die Nachricht grün formatiert werden soll...
            if message in ("0", "3", "5", "7"):
              # wird sie hier, in der Hilfsfunktion grün formatiert
              input_error_message = format_error_message_green(input_error_message)
            # Ansonsten wird die Nachricht rot formatiert
            elif message in ("1", "2", "4", "6", "8", "9", "10"):
              input_error_message = format_error_message_red(input_error_message)
            else:
              input_error_message = ""
  
            try:
              # Liste mit den Adressen
              liste_adressen = conn_region.get_all_addresses()
            except EC2ResponseError:
              # Wenn es nicht klappt...
              if sprache == "de":
                adressentabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
              else:
                adressentabelle = '<font color="red">An error occured</font>'
            except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              if sprache == "de":
                adressentabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
              else:
                adressentabelle = '<font color="red">A timeout error occured</font>'
            else:
              # Wenn es geklappt hat...
              # Anzahl der Elemente in der Liste
              laenge_liste_adressen = len(liste_adressen)
  
              if laenge_liste_adressen == 0:
                if sprache == "de":
                  adressentabelle = 'Sie haben keine elastischen IPs in dieser Region.'
                else:
                  adressentabelle = 'You have no elastic IPs inside this region.'
              else:
                adressentabelle = ''
                adressentabelle += '<table border="0" cellspacing="0" cellpadding="5">'
                
                counter = 0
                for i in range(laenge_liste_adressen):
                  
                    if counter > 0:
                        adressentabelle += '<tr><td colspan="4">&nbsp;</td></tr>'
                    counter += 1
                  
                    adressentabelle += '<tr>'
                    adressentabelle += '<td>'
                    adressentabelle += '<a href="/release_address?address='
                    adressentabelle += liste_adressen[i].public_ip
                    adressentabelle += "&amp;mobile="
                    adressentabelle += str(mobile)
                    if sprache == "de":
                      adressentabelle += '" title="Elastische IP freigeben">'
                      adressentabelle += '<img src="bilder/stop.png" width="16" height="16" border="0" alt="Elastische IP freigeben"></a>'
                    else:
                      adressentabelle += '" title="release elastic IP">'
                      adressentabelle += '<img src="bilder/stop.png" width="16" height="16" border="0" alt="release elastic IP"></a>'
                    adressentabelle += '</td>'

                    adressentabelle += '<td>'+liste_adressen[i].public_ip+'</td>'

                    if liste_adressen[i].instance_id == "" or liste_adressen[i].instance_id == "nobody":
                      adressentabelle += '<td>'
                      adressentabelle += '<a href="/associate_address?address='
                      adressentabelle += liste_adressen[i].public_ip
                      adressentabelle += "&amp;mobile="
                      adressentabelle += str(mobile)
                      if sprache == "de":
                        adressentabelle += '" title="Elastische IP mit Instanz verkn&uuml;pfen">'
                        adressentabelle += '<img src="bilder/attach2.png" width="16" height="16" border="0" alt="Elastische IP mit Instanz verkn&uuml;pfen"></a>'
                      else:
                        adressentabelle += '" title="associate elastic IP with instance">'
                        adressentabelle += '<img src="bilder/attach2.png" width="16" height="16" border="0" alt="associate elastic IP with instance"></a>'
                      adressentabelle += '</td>'
                    else:
                      adressentabelle += '<td>'
                      adressentabelle += '<a href="/disassociate_address?address='
                      adressentabelle += liste_adressen[i].public_ip
                      adressentabelle += "&amp;mobile="
                      adressentabelle += str(mobile)
                      if sprache == "de":
                        adressentabelle += '" title="Elastische IP von der Instanz l&ouml;sen">'
                        adressentabelle += '<img src="bilder/detach2.png" width="16" height="16" border="0" alt="Elastische IP mit Instanz verkn&uuml;pfen"></a>'
                      else:
                        adressentabelle += '" title="disassociate elastic IP from instance">'
                        adressentabelle += '<img src="bilder/detach2.png" width="16" height="16" border="0" alt="associate elastic IP with instance"></a>'
                      adressentabelle += '</td>'
                      

                    if liste_adressen[i].instance_id:
                      adressentabelle += '<td align="center">'+liste_adressen[i].instance_id+'</td>'
                    else:
                      adressentabelle += '<td align="center"><tt>---</tt></td>'
                      
                    adressentabelle += '</tr>'
                adressentabelle += '</table>'
  
            path = '&amp;path=elastic_ips&amp;mobile='+mobile
  
            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'adressentabelle': adressentabelle,
            'zonen_liste': zonen_liste,
            'input_error_message': input_error_message,
            'mobile': mobile,
            'path': path,
            }

            if mobile == "true":
                path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "adressen.html")
            else:  
                path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "adressen.html")
            self.response.out.write(template.render(path,template_values))

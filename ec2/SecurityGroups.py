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

class SecurityGroups(webapp.RequestHandler):
    def get(self):
        # self.response.out.write('posted!')
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')
        # Den Usernamen erfahren 
        username = users.get_current_user()
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
          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache,mobile)

          # It is Google Storage and not am IaaS  
          if regionname == "GoogleStorage":
  
            path = '&amp;path=securitygroups&amp;mobile='+mobile
            
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
            if message in ("40", "48"):
              # wird sie hier, in der Hilfsfunktion grün formatiert
              input_error_message = format_error_message_green(input_error_message)
            # Ansonsten wird die Nachricht rot formatiert
            elif message in ("8", "41", "42", "43", "44", "45", "46", "47", "49"):
              input_error_message = format_error_message_red(input_error_message)
            else:
              input_error_message = ""
  
            try:
              # Liste mit den Security Groups
              liste_security_groups = conn_region.get_all_security_groups()
            except EC2ResponseError:
              # Wenn es nicht klappt...
              if sprache == "de":
                gruppentabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
              else:
                gruppentabelle = '<font color="red">An error occured</font>'
            except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              if sprache == "de":
                gruppentabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
              else:
                gruppentabelle = '<font color="red">A timeout error occured</font>'
            else:
              # Wenn es geklappt hat...
              # Anzahl der Elemente in der Liste
              laenge_liste_security_groups = len(liste_security_groups)
  
              if laenge_liste_security_groups == 0:
                gruppentabelle = 'Es sind keine Sicherheitsgruppen in der Zone vorhanden.'
              else:
                
                if mobile == "true":
                  gruppentabelle = ''
                  gruppentabelle += '<table border="0" cellspacing="0" cellpadding="5" width="300">'
                  counter = 0
                  for i in range(laenge_liste_security_groups):
                    
                      if counter > 0:
                          gruppentabelle += '<tr><td colspan="3">&nbsp;</td></tr>'
                      counter += 1
                    
                      gruppentabelle += '<tr>'
                      gruppentabelle += '<td width="75">'
                      gruppentabelle += '<a href="/gruppenentfernen?gruppe='
                      gruppentabelle += liste_security_groups[i].name
                      gruppentabelle += "&amp;mobile="
                      gruppentabelle += str(mobile)
                      if sprache == "de":
                        gruppentabelle += '" title=" Sicherheitsgruppe l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Security Gruppe l&ouml;schen"></a>'
                      else:
                        gruppentabelle += '" title="erase security group"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase security group"></a>'
                      gruppentabelle += '</td>'
                      gruppentabelle += '<td align="left">'
                      gruppentabelle += '<a href="/gruppenaendern?gruppe='
                      gruppentabelle += liste_security_groups[i].name
                      gruppentabelle += "&amp;mobile="
                      gruppentabelle += str(mobile)
                      if sprache == "de":
                        gruppentabelle += '" title="Regeln einsehen/&auml;ndern"><img src="bilder/einstellungen.png" width="58" height="18" border="0" alt="Regeln einsehen/&auml;ndern"></a>'
                      else:
                        gruppentabelle += '" title="check/alter rules"><img src="bilder/einstellungen.png" width="58" height="18" border="0" alt="check/alter rules"></a>'
                      gruppentabelle += '</td>'
                      gruppentabelle += '</tr>'
                      gruppentabelle += '<tr>'
                      gruppentabelle += '<td align="right"><b>ID:</b></td>'
                      gruppentabelle += '<td>'+liste_security_groups[i].name+'</td>'
                      gruppentabelle += '</tr>'
                      gruppentabelle += '<tr>'
                      if sprache == "de":
                        gruppentabelle += '<td align="right"><b>Beschreibung:</b></td>'
                      else:
                        gruppentabelle += '<td align="right"><b>Description:</b></td>'
                      
                      gruppentabelle += '<td>'+liste_security_groups[i].description+'</td>'
                      gruppentabelle += '</tr>'
                      gruppentabelle += '<tr>'
                      if sprache == "de":
                        gruppentabelle += '<td align="right"><b>Besitzer:</b></td>'
                      else:
                        gruppentabelle += '<td align="right"><b>Owner:</b></td>'
                      
                      gruppentabelle += '<td>'+liste_security_groups[i].owner_id+'</td>'
                      gruppentabelle += '</tr>'
                  gruppentabelle += '</table>'  
                else:
                  gruppentabelle = ''
                  gruppentabelle += '<table border="0" cellspacing="0" cellpadding="5">'
                  counter = 0
                  for i in range(laenge_liste_security_groups):
                    
                      if counter > 0:
                          gruppentabelle += '<tr><td colspan="2">&nbsp;</td></tr>'
                      counter += 1
                    
                      gruppentabelle += '<tr>'
                      gruppentabelle += '<td align="left" bgcolor="#D4D4D4">'
                      gruppentabelle += '<a href="/gruppenentfernen?gruppe='
                      gruppentabelle += liste_security_groups[i].name
                      gruppentabelle += "&amp;mobile="
                      gruppentabelle += str(mobile)
                      if sprache == "de":
                        gruppentabelle += '" title=" Sicherheitsgruppe l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Security Gruppe l&ouml;schen"></a>'
                      else:
                        gruppentabelle += '" title="erase security group"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase security group"></a>'
                      gruppentabelle += '</td>'
                      gruppentabelle += '<td align="left">'
                      gruppentabelle += '<a href="/gruppenaendern?gruppe='
                      gruppentabelle += liste_security_groups[i].name
                      gruppentabelle += "&amp;mobile="
                      gruppentabelle += str(mobile)
                      if sprache == "de":
                        gruppentabelle += '" title="Regeln einsehen/&auml;ndern"><img src="bilder/einstellungen.png" width="58" height="18" border="0" alt="Regeln einsehen/&auml;ndern"></a>'
                      else:
                        gruppentabelle += '" title="check/alter rules"><img src="bilder/einstellungen.png" width="58" height="18" border="0" alt="check/alter rules"></a>'
                      gruppentabelle += '</td>'
                      
                      gruppentabelle += '</tr>'
                      gruppentabelle += '<tr>'
                      gruppentabelle += '<td align="right" bgcolor="#D4D4D4"><b>ID:</b></td>'
                      gruppentabelle += '<td align="left">'+liste_security_groups[i].name+'</td>'
                      gruppentabelle += '</tr>'
                      gruppentabelle += '<tr>'
                      if sprache == "de":
                        gruppentabelle += '<td align="right" bgcolor="#D4D4D4"><b>Beschreibung:</b></td>'
                      else:
                        gruppentabelle += '<td align="right" bgcolor="#D4D4D4"><b>Description:</b></td>'
                      
                      gruppentabelle += '<td align="left">'+liste_security_groups[i].description+'</td>'
                      gruppentabelle += '</tr>'
                      gruppentabelle += '<tr>'
                      if sprache == "de":
                        gruppentabelle += '<td align="right" bgcolor="#D4D4D4"><b>Besitzer:</b></td>'
                      else:
                        gruppentabelle += '<td align="right" bgcolor="#D4D4D4"><b>Owner:</b></td>'
                      
                      gruppentabelle += '<td align="left">'+liste_security_groups[i].owner_id+'</td>'
                      gruppentabelle += '</tr>'
                  gruppentabelle += '</table>'  
  
            path = '&amp;path=securitygroups&amp;mobile='+mobile
  
            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'securitygroupsliste': gruppentabelle,
            'input_error_message': input_error_message,
            'zonen_liste': zonen_liste,
            'mobile': mobile,
            'path': path,
            }
  
            if mobile == "true":
                path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "securitygroups.html")
            else:
                path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "securitygroups.html")
            self.response.out.write(template.render(path,template_values))

          
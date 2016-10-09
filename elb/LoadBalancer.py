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
from library import loginelb

from dateutil.parser import *

from error_messages import error_messages

from boto.ec2.connection import *
from boto.ec2.elb import ELBConnection

class LoadBalancer(webapp.RequestHandler):
    def get(self):
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

        for db_eintrag in aktivezone:
          zugangstyp = db_eintrag.zugangstyp

        if not results:
          self.redirect('/')
        else:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache,mobile)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')  
          #url = users.create_logout_url(self.request.uri)
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          #self.response.out.write(regionname)

          zonen_liste = zonen_liste_funktion(username,sprache,mobile)

          # It is Google Storage and not am IaaS  
          if regionname == "GoogleStorage":
            
            path = '&amp;path=loadbalancer&amp;mobile='+mobile
            
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
            
          # It is not Google Storage. It is an IaaS
          else:   
            
            if regionname != 'Amazon':
            #if zugangstyp != 'Amazon':
  
              template_values = {
              'navigations_bar': navigations_bar,
              'url': url,
              'url_linktext': url_linktext,
              'zone': regionname,
              'zone_amazon': zone_amazon,
              'zonen_liste': zonen_liste,
              }
  
              if mobile == "true":
                  path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "loadbalancer_non_aws.html")
              else:
                  path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "loadbalancer_non_aws.html")
              self.response.out.write(template.render(path,template_values))
            else:
  
              if sprache != "de":
                sprache = "en"
  
              input_error_message = error_messages.get(message, {}).get(sprache)
  
              # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
              if input_error_message == None:
                input_error_message = ""
  
              # Wenn die Nachricht grün formatiert werden soll...
              if message in ("9", "70", "72"):
                # wird sie hier, in der Hilfsfunktion grün formatiert
                input_error_message = format_error_message_green(input_error_message)
              # Ansonsten wird die Nachricht rot formatiert
              elif message in ("8", "10", "71"):
                input_error_message = format_error_message_red(input_error_message)
              else:
                input_error_message = ""
  
              # Mit ELB verbinden
              conn_elb = loginelb(username)
  
              try:
                # Liste mit den LoadBalancern
                liste_load_balancers = conn_elb.get_all_load_balancers()
              except EC2ResponseError:
                # Wenn es nicht klappt...
                if sprache == "de":
                  loadbalancertabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
                else:
                  loadbalancertabelle = '<font color="red">An error occured</font>'
              except DownloadError:
                # Diese Exception hilft gegen diese beiden Fehler:
                # DownloadError: ApplicationError: 2 timed out
                # DownloadError: ApplicationError: 5
                if sprache == "de":
                  loadbalancertabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
                else:
                  loadbalancertabelle = '<font color="red">A timeout error occured</font>'
              else:
                # Wenn es geklappt hat...
  
                # Anzahl der Elemente in der Liste
                laenge_liste_load_balancers = len(liste_load_balancers)
  
                if laenge_liste_load_balancers == 0:
                  if sprache == "de":
                    loadbalancertabelle = 'Sie haben keine Lastverteiler in dieser Region.'
                  else:
                    loadbalancertabelle = 'You have no load balancers inside this region.'
                else:
                  
                  if mobile == "true":
                    loadbalancertabelle = ''
                    loadbalancertabelle += '<table border="0" cellspacing="0" cellpadding="5" width="300">'
                    
                    counter = 0
                    
                    for i in range(laenge_liste_load_balancers):
                    
                        if counter > 0:
                            loadbalancertabelle += '<tr><td colspan="3">&nbsp;</td></tr>'
                        counter += 1
                        loadbalancertabelle += '<tr>'
                        loadbalancertabelle += '<td>'
                        loadbalancertabelle += '<a href="/delete_load_balancer?name='
                        loadbalancertabelle += liste_load_balancers[i].name
                        loadbalancertabelle += "&amp;mobile="
                        loadbalancertabelle += str(mobile)
                        if sprache == "de":
                          loadbalancertabelle += '" title="Load Balancer l&ouml;schen">'
                          loadbalancertabelle += '<img src="bilder/stop.png" width="16" height="16" border="0" alt="Load Balancer l&ouml;schen"></a>'
                        else:
                          loadbalancertabelle += '" title="delete load balancer">'
                          loadbalancertabelle += '<img src="bilder/stop.png" width="16" height="16" border="0" alt="delete load balancer"></a>'
                        loadbalancertabelle += '</td>'
                        
                        loadbalancertabelle += '<td colspan="2" align="center">'
                        loadbalancertabelle += '<a href="/loadbalanceraendern?name='
                        loadbalancertabelle += liste_load_balancers[i].name
                        loadbalancertabelle += "&amp;mobile="
                        loadbalancertabelle += str(mobile)
                        if sprache == "de":
                          loadbalancertabelle += '" title="Load Balancer einsehen/&auml;ndern"><img src="bilder/einstellungen.png" width="58" height="18" border="0" alt="Load Balancer einsehen/&auml;ndern"></a>'
                        else:
                          loadbalancertabelle += '" title="check/alter load balancer"><img src="bilder/einstellungen.png" width="58" height="18" border="0" alt="check/alter load balancer"></a>'
                        loadbalancertabelle += '</td>'
                        loadbalancertabelle += '</tr>'
                        
                        loadbalancertabelle += '<tr>'
                        loadbalancertabelle += '<td align="right"><b>ID:</b></td>'  
                        loadbalancertabelle += '<td colspan="2" align="center">'+liste_load_balancers[i].name+'</td>'
                        loadbalancertabelle += '</tr>'
                        
                        loadbalancertabelle += '<tr>'
                        loadbalancertabelle += '<td align="right"><b>DNS:</b></td>'
                        loadbalancertabelle += '<td colspan="2" align="center">'+liste_load_balancers[i].dns_name+'</td>'
                        loadbalancertabelle += '</tr>'
                        
                        loadbalancertabelle += '<tr>'
                        if sprache == "de":
                          loadbalancertabelle += '<td align="right"><b>Zonen:</b></td>'
                        else:
                          loadbalancertabelle += '<td align="right"><b>Zones:</b></td>'
                        loadbalancertabelle += '<td colspan="2" align="center">'
                        for x in range(len(liste_load_balancers[i].availability_zones)):
                          loadbalancertabelle += str(liste_load_balancers[i].availability_zones[x])
                          loadbalancertabelle += '&nbsp;'
                        loadbalancertabelle += '</td>'
                        loadbalancertabelle += '</tr>'
                        
                        loadbalancertabelle += '<tr>'
                        if sprache == "de":
                          loadbalancertabelle += '<td align="right"><b>Datum:</b></td>'
                        else:
                          loadbalancertabelle += '<td align="right"><b>Creation Date:</b></td>'
                        loadbalancertabelle += '<td colspan="2" align="center">'
                        datum_der_erzeugung = parse(liste_load_balancers[i].created_time)
                        loadbalancertabelle += str(datum_der_erzeugung.strftime("%Y-%m-%d  %H:%M:%S"))
                        loadbalancertabelle += '</td>'
                        loadbalancertabelle += '</tr>'
                        
                        loadbalancertabelle += '<tr>'
                        if sprache == "de":
                          loadbalancertabelle += '<td align="right"><b>Instanzen:</b></td>'
                        else:
                          loadbalancertabelle += '<td align="right"><b>Instances:</b></td>'
                        loadbalancertabelle += '<td colspan="2" align="center">'+str(len(liste_load_balancers[i].instances))+'</td>'
                        loadbalancertabelle += '</tr>'
                        
                        loadbalancertabelle += '<tr>'
                        loadbalancertabelle += '<td align="right"><b>Ports:</b></td>'
                        loadbalancertabelle += '<td colspan="2" align="center">'
                        for x in range(len(liste_load_balancers[i].listeners)):
                          loadbalancertabelle += str(liste_load_balancers[i].listeners[x])
                        loadbalancertabelle += '</td>'
                        loadbalancertabelle += '</tr>'
                    loadbalancertabelle += '</table>'
                    
                  else:
                    
                    loadbalancertabelle = ''
                    loadbalancertabelle += '<table border="0" cellspacing="0" cellpadding="5">'
                    
                    counter = 0
                    
                    for i in range(laenge_liste_load_balancers):
                    
                        if counter > 0:
                            loadbalancertabelle += '<tr><td colspan="2">&nbsp;</td></tr>'
                        counter += 1
                        loadbalancertabelle += '<tr>'
                        loadbalancertabelle += '<td align="left" bgcolor="#D4D4D4">'
                        loadbalancertabelle += '<a href="/delete_load_balancer?name='
                        loadbalancertabelle += liste_load_balancers[i].name
                        loadbalancertabelle += "&amp;mobile="
                        loadbalancertabelle += str(mobile)
                        if sprache == "de":
                          loadbalancertabelle += '" title="Load Balancer l&ouml;schen">'
                          loadbalancertabelle += '<img src="bilder/stop.png" width="16" height="16" border="0" alt="Load Balancer l&ouml;schen"></a>'
                        else:
                          loadbalancertabelle += '" title="delete load balancer">'
                          loadbalancertabelle += '<img src="bilder/stop.png" width="16" height="16" border="0" alt="delete load balancer"></a>'
                        loadbalancertabelle += '</td>'
                        
                        loadbalancertabelle += '<td align="left">'
                        loadbalancertabelle += '<a href="/loadbalanceraendern?name='
                        loadbalancertabelle += liste_load_balancers[i].name
                        loadbalancertabelle += "&amp;mobile="
                        loadbalancertabelle += str(mobile)
                        if sprache == "de":
                          loadbalancertabelle += '" title="Load Balancer einsehen/&auml;ndern"><img src="bilder/einstellungen.png" width="58" height="18" border="0" alt="Load Balancer einsehen/&auml;ndern"></a>'
                        else:
                          loadbalancertabelle += '" title="check/alter load balancer"><img src="bilder/einstellungen.png" width="58" height="18" border="0" alt="check/alter load balancer"></a>'
                        loadbalancertabelle += '</td>'
                        loadbalancertabelle += '</tr>'
                        
                        loadbalancertabelle += '<tr>'
                        loadbalancertabelle += '<td align="right" bgcolor="#D4D4D4"><b>ID:</b></td>'
                        loadbalancertabelle += '<td align="left">'+liste_load_balancers[i].name+'</td>'
                        loadbalancertabelle += '</tr>'
                                               
                        loadbalancertabelle += '<tr>'
                        if sprache == "de":
                          loadbalancertabelle += '<td align="right" bgcolor="#D4D4D4"><b>Zonen:</b></td>'
                        else:
                          loadbalancertabelle += '<td align="right" bgcolor="#D4D4D4"><b>Zones:</b></td>'
                        loadbalancertabelle += '<td align="left">'
                        for x in range(len(liste_load_balancers[i].availability_zones)):
                          loadbalancertabelle += str(liste_load_balancers[i].availability_zones[x])
                          loadbalancertabelle += '&nbsp;'
                        loadbalancertabelle += '</td>'
                        loadbalancertabelle += '</tr>'
                        
                        loadbalancertabelle += '<tr>'
                        if sprache == "de":
                          loadbalancertabelle += '<td align="right" bgcolor="#D4D4D4"><b>Datum:</b></td>'
                        else:
                          loadbalancertabelle += '<td align="right" bgcolor="#D4D4D4"><b>Creation Date:</b></td>'
                        loadbalancertabelle += '<td align="left">'
                        datum_der_erzeugung = parse(liste_load_balancers[i].created_time)
                        loadbalancertabelle += str(datum_der_erzeugung.strftime("%Y-%m-%d  %H:%M:%S"))
                        loadbalancertabelle += '</td>'
                        loadbalancertabelle += '</tr>'
                        
                        loadbalancertabelle += '<tr>'
                        if sprache == "de":
                          loadbalancertabelle += '<td align="right" bgcolor="#D4D4D4"><b>Instanzen:</b></td>'
                        else:
                          loadbalancertabelle += '<td align="right" bgcolor="#D4D4D4"><b>Instances:</b></td>'
                        loadbalancertabelle += '<td align="left">'+str(len(liste_load_balancers[i].instances))+'</td>'
                        loadbalancertabelle += '</tr>'
                        
                        loadbalancertabelle += '<tr>'
                        loadbalancertabelle += '<td align="right" bgcolor="#D4D4D4"><b>Ports:</b></td>'
                        loadbalancertabelle += '<td align="left">'
                        for x in range(len(liste_load_balancers[i].listeners)):
                          loadbalancertabelle += str(liste_load_balancers[i].listeners[x])
                        loadbalancertabelle += '</td>'
                        loadbalancertabelle += '</tr>'
                        
                        loadbalancertabelle += '<tr>'
                        loadbalancertabelle += '<td align="right" bgcolor="#D4D4D4"><b>DNS:</b></td>'
                        loadbalancertabelle += '<td align="left">'+liste_load_balancers[i].dns_name+'</td>'
                        loadbalancertabelle += '</tr>'
                    loadbalancertabelle += '</table>'
                    
              path = '&amp;path=loadbalancer&amp;mobile='+mobile
  
              template_values = {
              'navigations_bar': navigations_bar,
              'url': url,
              'url_linktext': url_linktext,
              'zone': regionname,
              'zone_amazon': zone_amazon,
              'loadbalancertabelle': loadbalancertabelle,
              'zonen_liste': zonen_liste,
              'input_error_message': input_error_message,
              'mobile': mobile,
              'path': path,
              }
  
              if mobile == "true":
                  path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "loadbalancer.html")
              else:
                  path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "loadbalancer.html")
              self.response.out.write(template.render(path,template_values))

          
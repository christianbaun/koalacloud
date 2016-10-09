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

class Zonen(webapp.RequestHandler):
    def get(self):
        # self.response.out.write('posted!')
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
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
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache,mobile)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache,mobile)

          # It is Google Storage and not am IaaS  
          if regionname == "GoogleStorage":
            
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
            
            try:
              # Liste mit den Zonen
              liste_zonen = conn_region.get_all_zones()
            except EC2ResponseError:
              # Wenn es nicht klappt...
              if sprache == "de":
                zonentabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
              else:
                zonentabelle = '<font color="red">An error occured</font>'
            except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              if sprache == "de":
                zonentabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
              else:
                zonentabelle = '<font color="red">A timeout error occured</font>'
            else:
              # Wenn es geklappt hat...
              # Anzahl der Elemente in der Liste
              laenge_liste_zonen = len(liste_zonen)
  
              zonentabelle = ''
              zonentabelle += '<table border="0" cellspacing="0" cellpadding="5">'
              for i in range(laenge_liste_zonen):
                  zonentabelle += '<tr>'
                  zonentabelle += '<td>'+str(liste_zonen[i].name)+'</td>'
                  if liste_zonen[i].state == u'available':
                    zonentabelle += '<td bgcolor="#c3ddc3" align="center">'
                    if sprache == "de":
                      zonentabelle += 'verf&uuml;gbar'
                    else:
                      zonentabelle += str(liste_zonen[i].state)
                  else:
                    zonentabelle += '<td align="center">'
                    zonentabelle += str(liste_zonen[i].state)
                  zonentabelle += '</td>'
                  zonentabelle += '</tr>'
              zonentabelle += '</table>'

            path = '&amp;path=zonen&amp;mobile='+mobile
  
            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'zonenliste': zonentabelle,
            'zonen_liste': zonen_liste,
            'path': path,
            }
  
            if mobile == "true":
                path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "zonen.html")
            else:
                path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "zonen.html")
            self.response.out.write(template.render(path,template_values))
          
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

class Associate_IP(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        #self.response.out.write('posted!')
        # Anzuhängende Elastic IP-Adresse holen
        address = self.request.get('address')
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
          #url = users.create_logout_url(self.request.uri)
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache,mobile)

          try:
            # Liste mit den Instanzen
            # Man kann nicht direkt versuchen mit get_all_security_groups(gruppen_liste)
            # die anzulegende Gruppe zu erzeugen. Wenn die Gruppe noch nicht existiert,
            # gibt es eine Fehlermeldung
            liste_reservations = conn_region.get_all_instances()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            fehlermeldung = "10"
            self.redirect('/elastic_ips?message='+fehlermeldung)
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            fehlermeldung = "9"
            self.redirect('/elastic_ips?message='+fehlermeldung)
          else:
            # Wenn es geklappt hat und die Liste geholt wurde...
            # Anzahl der Elemente in der Liste
            laenge_liste_reservations = len(liste_reservations)

            if laenge_liste_reservations == "0":
              # Wenn es keine laufenden Instanzen gibt
              instanzen_in_region = 0
            else:
              # Wenn es laufenden Instanzen gibt
              instanzen_in_region = 0
              for i in liste_reservations:
                for x in i.instances:
                  # Für jede Instanz wird geschaut...
                  # ...ob die Instanz in der Region des Volumes liegt und läuft
                  if x.state == u'running':
                    instanzen_in_region = instanzen_in_region + 1

            tabelle_instanz_anhaengen = ''
            tabelle_instanz_anhaengen += '<form action="/ip_definitiv_anhaengen?address='
            tabelle_instanz_anhaengen += address
            tabelle_instanz_anhaengen += '" method="post" accept-charset="utf-8">'
            tabelle_instanz_anhaengen += '\n'
            tabelle_instanz_anhaengen += '<input type="hidden" name="mobile" value="'+mobile+'">\n'
            tabelle_instanz_anhaengen += '<table border="0" cellspacing="0" cellpadding="5">'
            tabelle_instanz_anhaengen += '<tr>'
            if sprache == "de":
              tabelle_instanz_anhaengen += '<td align="right"><B>Elastische IP:</B></td>'
            else:
              tabelle_instanz_anhaengen += '<td align="right"><B>Elastic IP:</B></td>'
            tabelle_instanz_anhaengen += '<td>'+address+'</td>'
            tabelle_instanz_anhaengen += '</tr>'
            tabelle_instanz_anhaengen += '<tr>'
            if sprache == "de":
              tabelle_instanz_anhaengen += '<td align="right"><B>Instanz:</B></td>'
            else:
              tabelle_instanz_anhaengen += '<td align="right"><B>Instance:</B></td>'
            tabelle_instanz_anhaengen += '<td>'
            if instanzen_in_region == 0:
              if sprache == "de":
                tabelle_instanz_anhaengen += 'Sie haben keine Instanz in dieser Region'
              else:
                tabelle_instanz_anhaengen += 'You still have no instance inside this region'
            else:
              if instanzen_in_region > 0:
                tabelle_instanz_anhaengen += '<select name="instanzen" size="1">'
                for i in liste_reservations:
                  for x in i.instances:
                    if x.state == u'running':
                      tabelle_instanz_anhaengen += '<option>'
                      tabelle_instanz_anhaengen += x.id
                      tabelle_instanz_anhaengen += '</option>'
                tabelle_instanz_anhaengen += '</select>'
            tabelle_instanz_anhaengen += '</td>'
            tabelle_instanz_anhaengen += '</tr>'
            tabelle_instanz_anhaengen += '<tr>'
            if sprache == "de":
              tabelle_instanz_anhaengen += '<td align="left" colspan="2"><input type="submit" value="verkn&uuml;pfen"></td>\n'
            else:
              tabelle_instanz_anhaengen += '<td align="left" colspan="2"><input type="submit" value="associate"></td>\n'
            tabelle_instanz_anhaengen += '</tr>\n'
            tabelle_instanz_anhaengen += '</table>\n'
            tabelle_instanz_anhaengen += '</form>\n'

            path = '&amp;path=associate_address&amp;address='+address+'&amp;mobile='+mobile

            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'zonen_liste': zonen_liste,
            'tabelle_instanz_anhaengen': tabelle_instanz_anhaengen,
            'mobile': mobile,
            'path': path,
            }

            if mobile == "true":
                path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "ip_anhaengen.html")
            else:  
                path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "ip_anhaengen.html")
            self.response.out.write(template.render(path,template_values))

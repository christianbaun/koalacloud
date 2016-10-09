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

class LoadBalancer_Aendern(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')
        # Name des zu löschenden Load Balancers holen
        loadbalancer_name = self.request.get('name')
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

          if sprache != "de":
            sprache = "en"

          input_error_message = error_messages.get(message, {}).get(sprache)

          # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
          if input_error_message == None:
            input_error_message = ""

          # Wenn die Nachricht grün formatiert werden soll...
          if message in ("61", "63", "66", "68"):
            # wird sie hier, in der Hilfsfunktion grün formatiert
            input_error_message = format_error_message_green(input_error_message)
          # Ansonsten wird die Nachricht rot formatiert
          elif message in ("8", "62", "64", "65", "67", "69"):
            input_error_message = format_error_message_red(input_error_message)
          else:
            input_error_message = ""

          try:
            # Liste mit den Instanzen
            # Man kann nicht direkt versuchen mit get_all_security_groups(gruppen_liste)
            # die anzulegende Gruppe zu erzeugen. Wenn die Gruppe noch nicht existiert,
            # gibt es eine Fehlermeldung
            liste_reservations = conn_region.get_all_instances()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            fehlermeldung = "10"
            self.redirect('/loadbalancer?mobile='+str(mobile)+'&message='+fehlermeldung)
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            fehlermeldung = "9"
            self.redirect('/loadbalancer?mobile='+str(mobile)+'&message='+fehlermeldung)
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

            # Mit ELB verbinden
            conn_elb = loginelb(username)

            try:
              # Liste mit den LoadBalancern
              liste_load_balancers = conn_elb.get_all_load_balancers(load_balancer_names=str(loadbalancer_name))
            except EC2ResponseError:
              # Wenn es nicht klappt...
              fehlermeldung = "10"
              self.redirect('/loadbalancer?mobile='+str(mobile)+'&message='+fehlermeldung)
            except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              fehlermeldung = "9"
              self.redirect('/loadbalancer?mobile='+str(mobile)+'&message='+fehlermeldung)
            else:
              # Wenn es geklappt hat...

              tabelle_instanz_anhaengen = ''
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<form action="/loadbalancer_instanz_zuordnen?loadbalancer='
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + loadbalancer_name
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + "&amp;mobile="
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + str(mobile)
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '" method="post" accept-charset="utf-8">'
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '\n'
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<table border="0" cellspacing="0" cellpadding="5">\n'

              # Wenn dem Load Balancer noch keine Instanzen zugewiesen wurden...
              if len(liste_load_balancers[0].instances) == 0:
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<tr>\n'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td colspan="2">\n'
                if sprache == "de":
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + 'Es wurden noch keine Instanzen zugewiesen'
                else:
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + 'No instances asigned yet'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</td>\n'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</tr>\n'
              # Wenn dem Load Balancer schon Instanzen zugewiesen wurden...
              else:
                for z in range(len(liste_load_balancers[0].instances)):
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<tr>\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td>\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<a href="/loadbalancer_deregister_instance?loadbalancer='
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + loadbalancer_name
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '&amp;instanz='
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + liste_load_balancers[0].instances[z].id
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + "&amp;mobile="
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + str(mobile)
                  if sprache == "de":
                    tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '" title="Instanz deregistrieren">'
                    tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="Instanz deregistrieren"></a>'
                  else:
                    tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '" title="deregister instance">'
                    tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="deregister instance"></a>'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</td>\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td colspan="2">\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + liste_load_balancers[0].instances[z].id
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</td>\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</tr>\n'
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<tr>\n'
              # Wenn mehr als eine Instanz dem Load Balancer zugewiesen ist, dann muss hier ein 
              # leeres Feld hin. Sonst sieht die Tabelle nicht gut aus!
              if len(liste_load_balancers[0].instances) != 0:
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td>&nbsp;</td>\n'

              if instanzen_in_region == 0:
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td align="center" colspan="2">\n'
                if sprache == "de":
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + 'Sie haben keine Instanzen'
                else:
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + 'You have no instances'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</td>\n'
              else:
                if instanzen_in_region > 0:
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td align="center">\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<select name="instanzen" size="1">\n'
                  for i in liste_reservations:
                    for x in i.instances:
                      if x.state == u'running':
                        tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<option>'
                        tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + x.id
                        tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</option>\n'
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</select>\n'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</td>\n'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<td align="center">\n'
                if sprache == "de":
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<input type="submit" value="verkn&uuml;pfen">'
                else:
                  tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '<input type="submit" value="associate">'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '\n'
                tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</td>\n'
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</tr>\n'
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</table>\n'
              tabelle_instanz_anhaengen = tabelle_instanz_anhaengen + '</form>'


              try:
                # Liste mit den Zonen
                liste_zonen = conn_region.get_all_zones()
              except EC2ResponseError:
                # Wenn es nicht geklappt hat...
                if sprache == "de":
                  tabelle_zonen_aendern = '<font color="red">Es ist zu einem Fehler gekommen</font>'
                else:
                  tabelle_zonen_aendern = '<font color="red">An error occured</font>'
              except DownloadError:
                # Diese Exception hilft gegen diese beiden Fehler:
                # DownloadError: ApplicationError: 2 timed out
                # DownloadError: ApplicationError: 5
                if sprache == "de":
                  tabelle_zonen_aendern = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
                else:
                  tabelle_zonen_aendern = '<font color="red">A timeout error occured</font>'
              else:
                # Wenn es geklappt hat...
                # Anzahl der Elemente in der Liste
                laenge_liste_zonen = len(liste_zonen)

                tabelle_zonen_aendern = ''
                tabelle_zonen_aendern = tabelle_zonen_aendern + '<form action="/loadbalancer_zone_zuordnen?loadbalancer='
                tabelle_zonen_aendern = tabelle_zonen_aendern + loadbalancer_name
                tabelle_zonen_aendern = tabelle_zonen_aendern + "&amp;mobile="
                tabelle_zonen_aendern = tabelle_zonen_aendern + str(mobile)
                tabelle_zonen_aendern = tabelle_zonen_aendern + '" method="post" accept-charset="utf-8">'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '<table border="0" cellspacing="0" cellpadding="5">\n'

                for z in range(len(liste_load_balancers[0].availability_zones)):
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<tr>\n'
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<td>\n'
                  # Wenn dem Load Balancer nur eine Zone zugewiesen ist...
                  if len(liste_load_balancers[0].availability_zones) == 1:
                    tabelle_zonen_aendern = tabelle_zonen_aendern + '<a href="/loadbalanceraendern?loadbalancer='
                    tabelle_zonen_aendern = tabelle_zonen_aendern + loadbalancer_name
                    tabelle_zonen_aendern = tabelle_zonen_aendern + '&amp;message=67'
                    tabelle_zonen_aendern = tabelle_zonen_aendern + "&amp;mobile="
                    tabelle_zonen_aendern = tabelle_zonen_aendern + str(mobile)
                    if sprache == "de":
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '" title="Zone deregistrieren">'
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="Zone deregistrieren"></a>'
                    else:
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '" title="deregister zone">'
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="deregister zone"></a>'
                  # Wenn dem Load Balancer mehr als nur eine Zone zugewiesen ist...
                  else:
                    tabelle_zonen_aendern = tabelle_zonen_aendern + '<a href="/loadbalancer_deregister_zone?loadbalancer='
                    tabelle_zonen_aendern = tabelle_zonen_aendern + loadbalancer_name
                    tabelle_zonen_aendern = tabelle_zonen_aendern + '&amp;zone='
                    tabelle_zonen_aendern = tabelle_zonen_aendern + liste_load_balancers[0].availability_zones[z]
                    tabelle_zonen_aendern = tabelle_zonen_aendern + "&amp;mobile="
                    tabelle_zonen_aendern = tabelle_zonen_aendern + str(mobile)
                    if sprache == "de":
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '" title="Zone deregistrieren">'
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="Zone deregistrieren"></a>'
                    else:
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '" title="deregister zone">'
                      tabelle_zonen_aendern = tabelle_zonen_aendern + '<img src="bilder/stop.png" width="16" height="16" border="0" alt="deregister zone"></a>'
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '</td>\n'
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<td colspan="2">\n'
                  tabelle_zonen_aendern = tabelle_zonen_aendern + liste_load_balancers[0].availability_zones[z]
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '</td>\n'
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '</tr>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '<tr>\n'
                # Wenn mehr als eine Instanz dem Load Balancer zugewiesen ist, dann muss hier ein 
                # leeres Feld hin. Sonst sieht die Tabelle nicht gut aus!
                if len(liste_load_balancers[0].availability_zones) != 0:
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<td>&nbsp;</td>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '<td align="center">\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '<select name="zonen" size="1">\n'
                for i in range(laenge_liste_zonen):
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<option>'
                  tabelle_zonen_aendern = tabelle_zonen_aendern + liste_zonen[i].name
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '</option>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '</select>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '</td>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '<td align="center">\n'
                if sprache == "de":
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<input type="submit" value="verkn&uuml;pfen">'
                else:
                  tabelle_zonen_aendern = tabelle_zonen_aendern + '<input type="submit" value="associate">'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '</td>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '</tr>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '</table>\n'
                tabelle_zonen_aendern = tabelle_zonen_aendern + '</form>'


              path = '&amp;path=loadbalanceraendern&amp;name='+loadbalancer_name+'&amp;mobile='+mobile
              
              template_values = {
              'navigations_bar': navigations_bar,
              'url': url,
              'url_linktext': url_linktext,
              'zone': regionname,
              'zone_amazon': zone_amazon,
              'zonen_liste': zonen_liste,
              'load_balancer_name': loadbalancer_name,
              'tabelle_instanz_anhaengen': tabelle_instanz_anhaengen,
              'tabelle_zonen_aendern': tabelle_zonen_aendern,
              'input_error_message': input_error_message,
              'path': path,
              }

              if mobile == "true":
                  path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "loadbalancer_change.html")
              else:
                  path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "loadbalancer_change.html")
              self.response.out.write(template.render(path,template_values))

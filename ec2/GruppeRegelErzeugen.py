#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class GruppeRegelErzeugen(webapp.RequestHandler):
    def post(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        #self.response.out.write('posted!')
        gruppe = self.request.get('gruppe')
        protokoll_input = self.request.get('protokoll')
        # Die Methode authorize will den Protokoll-Namen in Kleinbuchstaben
        if protokoll_input == 'TCP':  protokoll = 'tcp'
        if protokoll_input == 'UDP':  protokoll = 'udp'
        if protokoll_input == 'ICMP': protokoll = 'icmp'
        port_from = self.request.get('port_from')
        port_to = self.request.get('port_to')
        cidr_ip = '0.0.0.0/0'

        username = users.get_current_user()      # Den Usernamen erfahren

        conn_region, regionname = login(username)


        # Schauen, ob die Regel folgende ist: From -1 To -1 (ICMP) für Ping
        if port_from == '-1' and port_to == '-1':
          ausnahme = 1
        else:
          ausnahme = 0

        # Testen ob der Port FROM und der Port TO angegeben wurde
        if port_from == "" and port_to == "" and ausnahme == 0:
          # Wenn die Ports nicht angegeben wurden, kann keine Regel angelegt werden
          fehlermeldung = "29"
          self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)
        # Testen ob der Port FROM angegeben wurde
        elif port_from == "" and ausnahme == 0:
          # Wenn der Port nicht angegeben wurde, kann keine Regel angelegt werden
          fehlermeldung = "30"
          self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)
        elif port_to == "" and ausnahme == 0:   # Testen ob der Port TO angegeben wurde
          # Wenn der Port nicht angegeben wurde, kann keine Regel angelegt werden
          fehlermeldung = "31"
          self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)
        elif port_from.isdigit() == False and port_to.isdigit() == False and ausnahme == 0:
          # Testen ob der Port FROM und Port TO eine Zahl ist
          # Wenn nicht ausschließlich eine Zahl eingegeben wurde sondern evtl. Buchstaben oder Sonderzeichen
          fehlermeldung = "32"
          self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)
        elif port_from.isdigit() == False and ausnahme == 0:
          # Testen ob der Port FROM eine Zahl ist
          # Wenn nicht ausschließlich eine Zahl eingegeben wurde sondern evtl. Buchstaben oder Sonderzeichen
          fehlermeldung = "33"
          self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)
        elif port_to.isdigit() == False and ausnahme == 0:
          # Testen ob der Port TO eine Zahl ist
          # Wenn nicht ausschließlich eine Zahl eingegeben wurde sondern evtl. Buchstaben oder Sonderzeichen
          fehlermeldung = "34"
          self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)
        else:

          try:
            # Liste mit den Security Groups
            # Man kann nicht direkt versuchen mit get_all_security_groups(gruppen_liste)
            # die anzulegende Gruppe zu erzeugen. Wenn die Gruppe noch nicht existiert,
            # gibt es eine Fehlermeldung
            liste_security_groups = conn_region.get_all_security_groups()
          except EC2ResponseError:
            # Wenn es nicht klappt...
            fehlermeldung = "35"
            self.redirect('/securitygroups?mobile='+str(mobile)+'&message='+fehlermeldung)
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            fehlermeldung = "35"
            self.redirect('/securitygroups?mobile='+str(mobile)+'&message='+fehlermeldung)
          else:
            # Wenn es geklappt hat und die Liste geholt wurde...

            # Anzahl der Elemente in der Liste
            laenge_liste_security_groups = len(liste_security_groups)

            for i in range(laenge_liste_security_groups):
              # Vergleichen
              if liste_security_groups[i].name == gruppe:
                # Jetzt ist die Richtige Security Group gefunden.

                # Liste mit den Regeln der Security Group
                liste_regeln = liste_security_groups[i].rules
                # Anzahl der Elemente in der Liste mit den Regeln
                laenge_liste_regeln = len(liste_regeln)

                # Es sind noch keine Regeln in der Security Group vorhanden
                if laenge_liste_regeln == 0:
                  #self.response.out.write('leer')
                  try:
                    #Jetzt anlegen
                    liste_security_groups[i].authorize(ip_protocol=protokoll, from_port=port_from, to_port=port_to, cidr_ip=cidr_ip, src_group=None)
                  except EC2ResponseError:
                    fehlermeldung = "39"
                    self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)
                  except DownloadError:
                    # Diese Exception hilft gegen diese beiden Fehler:
                    # DownloadError: ApplicationError: 2 timed out
                    # DownloadError: ApplicationError: 5
                    fehlermeldung = "8"
                    self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)
                  else:
                    fehlermeldung = "28"
                    self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)
                else:
                  for i in range(laenge_liste_regeln):
                    # self.response.out.write('nicht leer ')
                    # Hier muss die neue Regel mit den bestehenden Regeln verglichen werden
                    # Variable erzeugen zum Erfassen, ob die neue Regel schon existiert
                    schon_vorhanden = 0
                    regel = 'IPPermissions:'+protokoll+'('+port_from+'-'+port_to+')'
                    for k in range(laenge_liste_regeln):
                      # Vergleichen
                      if str(liste_regeln[k]) == regel:
                        schon_vorhanden = 1
                        fehlermeldung = "35"
                        self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)
                  if schon_vorhanden == 0:
                    for z in range(laenge_liste_security_groups):
                      # Vergleichen
                      if liste_security_groups[z].name == gruppe:
                        try:
                          #Jetzt die Regel anlegen
                          liste_security_groups[z].authorize(ip_protocol=protokoll, from_port=port_from, to_port=port_to, cidr_ip=cidr_ip, src_group=None)
                        except EC2ResponseError:
                          fehlermeldung = "39"
                          self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)
                        except DownloadError:
                          # Diese Exception hilft gegen diese beiden Fehler:
                          # DownloadError: ApplicationError: 2 timed out
                          # DownloadError: ApplicationError: 5
                          fehlermeldung = "8"
                          self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)
                        else:
                          fehlermeldung = "28"
                          self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)


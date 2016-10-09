#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class GruppeRegelEntfernen(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Den Namen der betreffenden Gruppe holen
        gruppe = self.request.get('gruppe')
        # Den Namen der zu löschenden Gruppe holen
        regel = self.request.get('regel')
        cidr_ip = '0.0.0.0/0'
        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

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
  
          # Mit dieser Variable wird überprüft, ob die Regel gleich gefunden wird
          # Wenn die Regel nicht gefunden wird, braucht auch nichts entfernt zu werden
          gefunden = 0
          for i in range(laenge_liste_security_groups):
            # Vergleichen
            if liste_security_groups[i].name == gruppe:
              # Jetzt ist die Richtige Security Group gefunden.
              # Liste mit den Regeln der Security Group holen
              liste_regeln = liste_security_groups[i].rules
              # Anzahl der Elemente in der Liste mit den Regeln
              laenge_liste_regeln = len(liste_regeln)

              for k in range(laenge_liste_regeln):
                vergleich = str(liste_regeln[k])         # Regel in einen String umwandeln
                if vergleich == regel:                   # Vergleichen
                  # Die Regel wurde gefunden!
                  gefunden = 1
                  try:
                    liste_security_groups[i].revoke(ip_protocol=liste_regeln[k].ip_protocol,
                                                    from_port=liste_regeln[k].from_port,
                                                    to_port=liste_regeln[k].to_port,
                                                    cidr_ip=cidr_ip,
                                                    src_group=None)
                  except EC2ResponseError:
                    fehlermeldung = "36"
                    self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)
                  except DownloadError:
                    # Diese Exception hilft gegen diese beiden Fehler:
                    # DownloadError: ApplicationError: 2 timed out
                    # DownloadError: ApplicationError: 5
                    fehlermeldung = "8"
                    self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)
                  else:
                    fehlermeldung = "37"
                    self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)

          # Wenn die Instanz nicht gefunden werden konnte
          if gefunden == 0:
            fehlermeldung = "38"
            self.redirect('/gruppenaendern?mobile='+str(mobile)+'&gruppe='+gruppe+'&message='+fehlermeldung)


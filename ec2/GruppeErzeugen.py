#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import re

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class GruppeErzeugen(webapp.RequestHandler):
    def post(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        #self.response.out.write('posted!')
        neuergruppenname = self.request.get('gruppenname')
        neuegruppenbeschreibung = self.request.get('gruppenbeschreibung')

        username = users.get_current_user()      # Den Usernamen erfahren

        conn_region, regionname = login(username)

        if neuergruppenname == "" and neuegruppenbeschreibung == "":
            # Wenn kein Name und keine Beschreibung angegeben wurde
            #fehlermeldung = "Sie haben keinen Namen und keine Beschreibung angegeben"
            fehlermeldung = "41"
            self.redirect('/securitygroups?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif neuergruppenname == "":
            # Testen ob ein Name für die neue Gruppe angegeben wurde
            #fehlermeldung = "Sie haben keinen Namen angegeben"
            fehlermeldung = "42"
            self.redirect('/securitygroups?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif neuegruppenbeschreibung == "":
            # Testen ob eine Beschreibung für die neue Gruppe angegeben wurde
            #fehlermeldung = "Sie haben keine Beschreibung angegeben"
            fehlermeldung = "43"
            self.redirect('/securitygroups?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif re.search(r'[^\-_a-zA-Z0-9]', neuergruppenname) != None:
            # Testen ob für den neuen Gruppennamen nur erlaubte Zeichen verwendet wurden
            fehlermeldung = "45"
            self.redirect('/securitygroups?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif re.search(r'[^\ \-_a-zA-Z0-9]', neuegruppenbeschreibung) != None:
            # Testen ob für die Beschreibung der den neuen Gruppe nur erlaubte Zeichen verwendet wurden
            # Leerzeichen sind in der Gruppenbezeichnung ok
            fehlermeldung = "46"
            self.redirect('/securitygroups?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
            try:
                # Liste mit den Security Groups
                # Man kann nicht direkt versuchen mit get_all_security_groups(gruppen_liste)
                # die anzulegende Gruppe zu erzeugen. Wenn die Gruppe noch nicht existiert,
                # gibt es eine Fehlermeldung
                liste_security_groups = conn_region.get_all_security_groups()
            except EC2ResponseError:
                # Wenn es nicht klappt...
                fehlermeldung = "47"
                self.redirect('/securitygroups?mobile='+str(mobile)+'&message='+fehlermeldung)
            except DownloadError:
                # Diese Exception hilft gegen diese beiden Fehler:
                # DownloadError: ApplicationError: 2 timed out
                # DownloadError: ApplicationError: 5
                fehlermeldung = "47"
                self.redirect('/securitygroups?mobile='+str(mobile)+'&message='+fehlermeldung)
            else:
                # Wenn es geklappt hat und die Liste geholt wurde...

                # Anzahl der Elemente in der Liste
                laenge_liste_security_groups = len(liste_security_groups)

                # Variable erzeugen zum Erfassen, ob die neu Gruppe schon existiert
                schon_vorhanden = 0
                for i in range(laenge_liste_security_groups):
                    # Vergleichen
                    # Für jede existierende Gruppe den Namen der Gruppe
                    # mit dem neuen Gruppennamen vergleichen
                    if liste_security_groups[i].name == neuergruppenname:
                        # Security Gruppe existiert schon!
                        schon_vorhanden = 1
                        fehlermeldung = "44"
                        self.redirect('/securitygroups?mobile='+str(mobile)+'&message='+fehlermeldung)

                # Wenn der Schlüssel noch nicht existiert...anlegen!
                if schon_vorhanden == 0:
                    try:
                        # Security Group anlegen
                        conn_region.create_security_group(neuergruppenname, neuegruppenbeschreibung)
                    except EC2ResponseError:
                        fehlermeldung = "47"
                        self.redirect('/securitygroups?mobile='+str(mobile)+'&message='+fehlermeldung)
                    except DownloadError:
                        # Diese Exception hilft gegen diese beiden Fehler:
                        # DownloadError: ApplicationError: 2 timed out
                        # DownloadError: ApplicationError: 5
                        fehlermeldung = "8"
                        self.redirect('/securitygroups?mobile='+str(mobile)+'&message='+fehlermeldung)
                    else:
                        fehlermeldung = "40"
                        self.redirect('/securitygroups?mobile='+str(mobile)+'&message='+fehlermeldung)

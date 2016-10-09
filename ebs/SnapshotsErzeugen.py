#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template

from library import login

from library import login
from library import aktuelle_sprache
from library import navigations_bar_funktion
from library import amazon_region
from library import zonen_liste_funktion
from library import format_error_message_green
from library import format_error_message_red

class SnapshotsErzeugen(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Den Namen des Volumes holen
        # Get the name of the volume
        volume = self.request.get('volume')
        # Name der Zone holen
        volume_zone  = self.request.get('zone')
        # Den Usernamen erfahren
        # Get the username
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


          tabelle_snapshot = ''
          tabelle_snapshot += '<form action="/snapshoterzeugendefinitiv" method="post" accept-charset="utf-8"> \n'
          tabelle_snapshot += '<input type="hidden" name="mobile" value="'+mobile+'">\n'
          tabelle_snapshot += '<input type="hidden" name="volume" value="'+volume+'">\n'
          tabelle_snapshot += '<table border="0" cellspacing="0" cellpadding="5">\n'
          tabelle_snapshot += '<tr><td align="left"><B>Volume: </B>'+volume+'</td></tr>\n'
          if sprache == "de":
            tabelle_snapshot += '<tr><td align="left"><B>Beschreibung:</B></td></tr>\n'
          else:
            tabelle_snapshot += '<tr><td align="left"><B>Description:</B></td></tr>\n'
            
          if mobile == "true":
              tabelle_snapshot += '<tr><td><input name="beschreibung" type="text" size="40" maxlength="40"></td></tr>\n'              
          else:
              tabelle_snapshot += '<tr><td><input name="beschreibung" type="text" size="60" maxlength="60"></td></tr>\n'

          if sprache == "de":
            tabelle_snapshot += '<tr><td align="left"><input type="submit" value="Snapshot erzeugen"></td></tr>\n'
          else:
            tabelle_snapshot += '<tr><td align="left"><input type="submit" value="create snapshot"></td></tr>\n'

          tabelle_snapshot += '</table>'
          tabelle_snapshot += '</form>'

          # path = '&amp;path=volumes'
          path = '&amp;path=snapshoterzeugen&amp;volume='+volume+'&amp;mobile='+mobile
 
          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonen_liste': zonen_liste,
          'tabelle_snapshot': tabelle_snapshot,
          'mobile': mobile,
          'path': path,
          }

          if mobile == "true":
              path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "snapshot_erzeugen.html")
          else:
              path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "snapshot_erzeugen.html")
          self.response.out.write(template.render(path,template_values))

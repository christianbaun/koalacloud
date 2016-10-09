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

class Info(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        # Den Usernamen erfahren
        username = users.get_current_user()

        if users.get_current_user():
            # Nachsehen, ob eine Region/Zone ausgewählte wurde
            aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
            results = aktivezone.fetch(100)

            if not results:
              regionname = '---'
              zone_amazon = ""
            else:
              conn_region, regionname = login(username)
              zone_amazon = amazon_region(username)

            # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
            sprache = aktuelle_sprache(username)
            navigations_bar = navigations_bar_funktion(sprache,mobile)

            url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
            url_linktext = 'Logout'

            # Get the pull-down menu with the users regions he has already configured             
            zonen_liste = zonen_liste_funktion(username,sprache,mobile)
            
            # If the user has still no credentials for cloud services
            if zonen_liste == '':
              if sprache == "de":
                zonen_liste = '<p><font color="red"><b>Sie m&uuml;ssen nun ihre Zugangsdaten (Regionen) einrichten</b></font></p>'            
              else:
                zonen_liste = '<p><font color="red"><b>Now, you need to configure your Region data</b></font></p>'            

        else:
            sprache = "en"
            navigations_bar = navigations_bar_funktion(sprache)
            url = users.create_login_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
            url_linktext = 'Login'
            regionname = '---'
            zone_amazon = ""

            zonen_liste = '<p><font color="red"><b><=== You need to login first with your Google account!</b></font></p>'

        template_values = {
        'navigations_bar': navigations_bar,
        'zone': regionname,
        'zone_amazon': zone_amazon,
        'url': url,
        'url_linktext': url_linktext,
        'zonen_liste': zonen_liste,
        }

        if mobile == "true":
            path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "info.html")
        else:
            path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "info.html")
        self.response.out.write(template.render(path,template_values))

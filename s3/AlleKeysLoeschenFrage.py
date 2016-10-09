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

class AlleKeysLoeschenFrage(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
          self.redirect('/')
        # Den Namen des Buckets erfahren
        bucketname = self.request.get('bucket_name')
        # Die S3-Ansicht (pur oder Komfort) erfahren
        s3_ansicht = self.request.get('s3_ansicht')

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

          path = '&amp;path=alle_keys_loeschen&amp;mobile='+mobile+'&amp;s3_ansicht='+s3_ansicht+'&amp;bucket_name='+bucketname
          
          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonen_liste': zonen_liste,
          'bucketname': bucketname,
          's3_ansicht': s3_ansicht,
          'mobile': mobile,
          'path': path,
          }

          if mobile == "true":
              path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "alle_keys_loeschen_frage.html")
          else:
              path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "alle_keys_loeschen_frage.html")
          self.response.out.write(template.render(path,template_values))


#######################################
### WHY IS THIS NOT WORKING !?!?!?! ###
#######################################

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

class ConsoleOutput(webapp.RequestHandler):
    def get(self):
        # self.response.out.write('posted!')
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Den Usernamen erfahren
        username = users.get_current_user()  
        if not username:
          self.redirect('/')
        # Die ID der Instanz holen
        instance_id = self.request.get('id')

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
          fehlermeldung = ""

          try:
            console_output = conn_region.get_console_output(str(instance_id))
          except EC2ResponseError:
            # Wenn es nicht klappt...
            if sprache == "de":
              fehlermeldung = '<p>&nbsp;</p> <font color="red">Beim Versuch die Konsolenausgabe der Instanz zu holen, kam es zu einem Fehler</font>'
            else:
              fehlermeldung = '<p>&nbsp;</p> <font color="red">While the system tried to get the console output, an error occured</font>'
            console_ausgabe = ''

            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'instance_id': instance_id,
            'zone': regionname,
            'fehlermeldung': fehlermeldung,
            'zone_amazon': zone_amazon,
            'console_ausgabe': console_ausgabe,
            'zonen_liste': zonen_liste,
            }

            if mobile == "true":
                path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "console_output.html")
            else:
                path = os.path.join(os.path.dirname(__file__), "templates", sprache, "console_output.html")
            self.response.out.write(template.render(path,template_values))
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            if sprache == "de":
              fehlermeldung = '<p>&nbsp;</p> <font color="red">Beim Versuch die Konsolenausgabe der Instanz zu holen, kam es zu einem Timeout-Fehler.</font>'
            else:
              fehlermeldung = '<p>&nbsp;</p> <font color="red">While the system tried to get the console output, a timeout error occured.</font>'
            console_ausgabe = ''

            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'instance_id': instance_id,
            'zone': regionname,
            'fehlermeldung': fehlermeldung,
            'zone_amazon': zone_amazon,
            'console_ausgabe': console_ausgabe,
            'zonen_liste': zonen_liste,
            }

            if mobile == "true":
                path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "console_output.html")
            else:
                path = os.path.join(os.path.dirname(__file__), "templates", sprache, "console_output.html")
            self.response.out.write(template.render(path,template_values))
          else:
            # Wenn es geklappt hat...

            if console_output.output == '':
              if sprache == "de":
                console_ausgabe = '<font color="green">Es liegt noch keine Konsolenausgabe vor</font>'
              else:
                console_ausgabe = '<font color="green">Still no console output exists</font>'
            else:
              console_ausgabe = ''
              console_ausgabe = console_ausgabe + '<tt>'
              console_ausgabe = console_ausgabe + console_output.output.replace("\n","<BR>").replace(" ", "&nbsp;").replace("", "&nbsp;")
              console_ausgabe = console_ausgabe + '</tt>'

            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'instance_id': instance_id,
            'zone': regionname,
            'fehlermeldung': fehlermeldung,
            'zone_amazon': zone_amazon,
            'console_ausgabe': console_ausgabe,
            'zonen_liste': zonen_liste,
            }

            if mobile == "true":
                path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "console_output.html")
            else:
                path = os.path.join(os.path.dirname(__file__), "templates", sprache, "console_output.html")
            self.response.out.write(template.render(path,template_values))

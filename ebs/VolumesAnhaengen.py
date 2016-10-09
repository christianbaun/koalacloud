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

class VolumesAnhaengen(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Name des zu anzuhängenden Volumes holen
        volume = self.request.get('volume')
        # Name der Zone holen
        volume_zone  = self.request.get('zone')
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
  
          liste_reservations = conn_region.get_all_instances()
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
                if x.placement == volume_zone and x.state == u'running':
                  instanzen_in_region = instanzen_in_region + 1
  
          tabelle_anhaengen = ''
          tabelle_anhaengen = tabelle_anhaengen + '<form action="/volumedefinitivanhaengen?volume='
          tabelle_anhaengen = tabelle_anhaengen + volume
          tabelle_anhaengen = tabelle_anhaengen + '" method="post" accept-charset="utf-8">\n'
          tabelle_anhaengen = tabelle_anhaengen + '<input type="hidden" name="mobile" value="'+mobile+'">\n'
          tabelle_anhaengen = tabelle_anhaengen + '<table border="0" cellspacing="0" cellpadding="5">'
          tabelle_anhaengen += '<tr>'
          if sprache == "de":
            tabelle_anhaengen += '<td align="right"><B>Volumen:</B></td>'
          else:
            tabelle_anhaengen += '<td align="right"><B>Volume:</B></td>'
          tabelle_anhaengen += '<td>'+volume+'</td>'
          tabelle_anhaengen += '</tr>'
          tabelle_anhaengen += '<tr>'
          if sprache == "de":
            tabelle_anhaengen = tabelle_anhaengen + '<td align="right"><B>Instanzen:</B></td>'
          else:
            tabelle_anhaengen = tabelle_anhaengen + '<td align="right"><B>Instances:</B></td>'
          tabelle_anhaengen = tabelle_anhaengen + '<td>'
          if instanzen_in_region == 0:
            if sprache == "de":
              tabelle_anhaengen += 'Sie haben keine Instanzen in dieser Region <b>'+volume_zone+'</b></td>'
            else:
              tabelle_anhaengen += 'You have still no instances in this region <b>'+volume_zone+'</b></td>'
          else:
            if instanzen_in_region > 0:
              tabelle_anhaengen = tabelle_anhaengen + '<select name="instanzen" size="1">'
              for i in liste_reservations:
                for x in i.instances:
                  if x.placement == volume_zone and x.state == u'running':
                    tabelle_anhaengen = tabelle_anhaengen + '<option>'
                    tabelle_anhaengen = tabelle_anhaengen + x.id
                    tabelle_anhaengen = tabelle_anhaengen + '</option>'
              tabelle_anhaengen = tabelle_anhaengen + '</select>'
            tabelle_anhaengen = tabelle_anhaengen + '</td>'
          tabelle_anhaengen = tabelle_anhaengen + '</tr>'
          tabelle_anhaengen = tabelle_anhaengen + '<tr>'
          if sprache == "de":
            tabelle_anhaengen = tabelle_anhaengen + '<td align="right"><B>Ger&auml;t:</B></td>'
          else:
            tabelle_anhaengen = tabelle_anhaengen + '<td align="right"><B>Device:</B></td>'
          tabelle_anhaengen = tabelle_anhaengen + '<td>'
          tabelle_anhaengen = tabelle_anhaengen + '<select name="device" size="1">'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sda</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdb</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option selected="selected">/dev/sdc</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdd</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sde</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdf</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdg</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdh</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdu</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdj</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdk</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdl</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdm</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdn</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdo</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdp</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdq</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdr</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sds</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdt</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdu</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdv</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdw</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdx</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdy</option>'
          tabelle_anhaengen = tabelle_anhaengen + '<option>/dev/sdz</option>'
          tabelle_anhaengen = tabelle_anhaengen + '</select>'
          tabelle_anhaengen = tabelle_anhaengen + '</td>'
          tabelle_anhaengen = tabelle_anhaengen + '</tr>'
          tabelle_anhaengen = tabelle_anhaengen + '<tr>'
          tabelle_anhaengen = tabelle_anhaengen + '<td align="left" colspan="2">'
          tabelle_anhaengen = tabelle_anhaengen + '\n'
          if instanzen_in_region == 0:
            tabelle_anhaengen = tabelle_anhaengen + '&nbsp;'
          else:
            if sprache == "de":
              tabelle_anhaengen = tabelle_anhaengen + '<input type="submit" value="Volumen anh&auml;ngen">'
            else:
              tabelle_anhaengen = tabelle_anhaengen + '<input type="submit" value="attach volume">'
          tabelle_anhaengen = tabelle_anhaengen + '\n'
          tabelle_anhaengen = tabelle_anhaengen + '</td>'
          tabelle_anhaengen = tabelle_anhaengen + '</tr>'
          tabelle_anhaengen = tabelle_anhaengen + '</table>'
          tabelle_anhaengen = tabelle_anhaengen + '</form>'
  
          if regionname != "Amazon":   # Wenn die Region nicht Amazon EC2, sondern Eucalyptus ist...
            if sprache == "de":        # ... und die Sprache deutsch ist ...
              ebs_volumes_eucalyptus_warnung = '<font color="red">Achtung! Das Verbinden von Volumes mit Instanzen dauert unter Eucalyptus teilweise mehrere Minuten.</font>'
            else:                      # ... und die Sprache englisch ist ...
              ebs_volumes_eucalyptus_warnung = '<font color="red">Attention! Attaching volumes with Instances at Eucalyptus needs some time (several minutes).</font>'
          else:                        # Wenn die Region Amazon EC2 ist...
            ebs_volumes_eucalyptus_warnung = "<p>&nbsp;</p>"
  
          path = '&amp;path=volumeanhaengen&amp;mobile='+mobile+'&amp;volume='+volume+'&amp;zone='+volume_zone
  
          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonen_liste': zonen_liste,
          'tabelle_anhaengen': tabelle_anhaengen,
          'ebs_volumes_eucalyptus_warnung': ebs_volumes_eucalyptus_warnung,
          'path': path,
          }
  
          if mobile == "true":
              path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "volume_anhaengen.html")
          else:
              path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "volume_anhaengen.html")
          self.response.out.write(template.render(path,template_values))

          
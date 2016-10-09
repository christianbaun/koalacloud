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

class ImageStarten(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # self.response.out.write('test')
        # Den Usernamen erfahren
        # Get the username
        username = users.get_current_user()
        if not username:
            self.redirect('/')
        # Die ID des zu startenden Images holen
        # Get the ID of the image that shall be started
        image = self.request.get('image')
        # Die Architektur des zu startenden Images holen
        # Get the architecture of the image that shall be started
        arch = self.request.get('arch')
        # Das Root Device des zu startenden Images holen
        # Get the root device of the image that shall be started
        root = self.request.get('root')

        sprache = aktuelle_sprache(username)
        navigations_bar = navigations_bar_funktion(sprache,mobile)
        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if not results:
          regionname = '---'
          zone_amazon = ""
        else:
          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

        # So wird der HTML-Code korrekt
        url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
        #url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'

        zonen_liste = zonen_liste_funktion(username,sprache,mobile)

        for result in results:

          imageliste = [str(image)]
          # Liste mit den Images
          liste_images = conn_region.get_all_images(image_ids=imageliste)  
          # Anzahl der Images in der Liste
          laenge_liste_images = len(liste_images)
          for i in range(laenge_liste_images):
            if liste_images[i].id == image:
              manifest = str(liste_images[i].location)

        
        if result.zugangstyp == "Nimbus":
          # If it is a Nimbus infrastructure...

          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'image': image,
          'manifest': manifest,
          'zonen_liste': zonen_liste,
          'mobile': mobile,
          }

          if mobile == "true":
              path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "image_starten_nimbus.html")
          else:
              path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "image_starten_nimbus.html")
          self.response.out.write(template.render(path,template_values))

        else:
          # If it is not a Nimbus infrastructure...


          # Wenn es Amazon EC2 ist
          if result.zugangstyp == "Amazon":
            if arch == "i386":
              # Liste mit den Instanz-Typen wenn es ein 32-Bit Image ist
              if root == "ebs":
                liste_instanztypen_eucalyptus = ["t1.micro", "m1.small", "c1.medium"]
              else:
                # root == instance-store
                # t1.micro instances must have an EBS root device
                liste_instanztypen_eucalyptus = ["m1.small", "c1.medium"]
            else:
              # Liste mit den Instanz-Typen wenn es ein 64-Bit Image ist
              liste_instanztypen_eucalyptus = ["t1.micro", "m1.small", "m1.medium", "m1.large", "m1.xlarge", "m2.xlarge", "m2.2xlarge", "m2.4xlarge", "c1.medium", "c1.xlarge", "cc1.4xlarge", "cc2.8xlarge", "cg1.4xlarge"]
            # Anzahl der Elemente in der Liste
            laenge_liste_instanztypen_eucalyptus = len(liste_instanztypen_eucalyptus)

            instance_types_liste = ""
            for i in range(laenge_liste_instanztypen_eucalyptus):
                if i == 0:
                  instance_types_liste = instance_types_liste + '<option selected="selected">'
                else:
                  instance_types_liste = instance_types_liste + "<option>"
                instance_types_liste = instance_types_liste + liste_instanztypen_eucalyptus[i]
                instance_types_liste = instance_types_liste + "</option>"

            instance_types_liste_laenge = laenge_liste_instanztypen_eucalyptus
          elif result.zugangstyp == "Nimbus":
            # Wenn es Nimbus ist
            instance_types_liste_laenge = 0
            liste_instanztypen_eucalyptus = []
            laenge_liste_instanztypen_eucalyptus = 0
            instance_types_liste = []
          else:
            # Wenn es Eucalyptus ist
            liste_instanztypen_eucalyptus = ["m1.small", "c1.medium", "m1.large", "m1.xlarge", "c1.xlarge"] 
            # Anzahl der Elemente in der Liste mit den Instanz-Typen
            laenge_liste_instanztypen_eucalyptus = len(liste_instanztypen_eucalyptus) 

            instance_types_liste = ""
            for i in range(laenge_liste_instanztypen_eucalyptus):
                if i == 0:
                  instance_types_liste = instance_types_liste + '<option selected="selected">'
                else:
                  instance_types_liste = instance_types_liste + "<option>"
                instance_types_liste = instance_types_liste + liste_instanztypen_eucalyptus[i]
                instance_types_liste = instance_types_liste + "</option>"

            instance_types_liste_laenge = laenge_liste_instanztypen_eucalyptus

          # Liste mit den Zonen
          liste_zonen = conn_region.get_all_zones()
          # Anzahl der Elemente in der Liste
          laenge_liste_zonen = len(liste_zonen)

          # Hier wird die Auswahlliste der Zonen erzeugt
          # Diese Auswahlliste ist zum Erzeugen neuer Volumes notwendig
          zonen_in_der_region = ''
          for i in range(laenge_liste_zonen):
              zonen_in_der_region = zonen_in_der_region + "<option>"
              zonen_in_der_region = zonen_in_der_region + liste_zonen[i].name
              zonen_in_der_region = zonen_in_der_region + "</option>"

          # Liste mit den Schlüsseln
          liste_key_pairs = conn_region.get_all_key_pairs()
          # Anzahl der Elemente in der Liste
          laenge_liste_keys = len(liste_key_pairs)

          keys_liste = ''
          if laenge_liste_keys == 0:
            if sprache == "de":
              keys_liste = '<font color="red">Es sind keine Schl&uuml in der Zone vorhanden</font>'
            else:
              keys_liste = '<font color="red">No keypairs exist inside this security zone</font>'
          # This is not workling. We need a list to get the value to the class that starts the instance
          #elif laenge_liste_keys == 1:
          #  keys_liste = '<input name="keys_liste" type="text" size="70" maxlength="70" value="'
          #  keys_liste = keys_liste + liste_key_pairs[0].name
          #  keys_liste = keys_liste + '" readonly>'
          else:
            keys_liste = keys_liste + '<select name="keys_liste" size="1">'
            for i in range(laenge_liste_keys):
              if i == 0:
                keys_liste = keys_liste + '<option selected="selected">'
              else:
                keys_liste = keys_liste + '<option>'
              keys_liste = keys_liste + liste_key_pairs[i].name
              keys_liste = keys_liste + '</option>'
            keys_liste = keys_liste + '</select>'


          try:
            # Liste mit den Security Groups
            liste_security_groups = conn_region.get_all_security_groups()
          except EC2ResponseError:
            # Wenn es nicht geklappt hat
            fehlermeldung = "78"
            self.redirect('/images?mobile='+str(mobile)+'&message='+fehlermeldung)
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            fehlermeldung = "8"
            self.redirect('/images?mobile='+str(mobile)+'&message='+fehlermeldung)
          else:
            # Wenn es geklappt hat
            
            # Anzahl der Elemente in der Liste
            laenge_liste_security_groups = len(liste_security_groups)
  
            gruppen_liste = ''
            if laenge_liste_security_groups == 0:
              if sprache == "de":
                gruppen_liste = '<font color="red">Es sind keine Sicherheitsgruppen in der Zone vorhanden</font>'
              else:
                gruppen_liste = '<font color="red">No Security Groups exist inside this security zone</font>'
            # This is not workling. We need a list to get the value to the class that starts the instance
            #elif laenge_liste_security_groups == 1:
            #  gruppen_liste = liste_security_groups[0].name
            else:
              gruppen_liste = gruppen_liste + '<select name="gruppen_liste" size="1">'
              for i in range(laenge_liste_security_groups):
                if i == 0:
                  gruppen_liste = gruppen_liste + '<option selected="selected">'
                else:
                  gruppen_liste = gruppen_liste + '<option>'
                gruppen_liste = gruppen_liste + liste_security_groups[i].name
                #gruppen_liste = gruppen_liste + ' ('
                #gruppen_liste = gruppen_liste + liste_security_groups[i].owner_id
                #gruppen_liste = gruppen_liste + ')'
                gruppen_liste = gruppen_liste + '</option>'
              gruppen_liste = gruppen_liste + '</select>'
  
  
  
            instanz_starten_tabelle = ''
            if mobile == "true":
              # Mobile version
              instanz_starten_tabelle += '<form action="/instanzanlegen" method="post" accept-charset="utf-8">\n'
              instanz_starten_tabelle += '<input type="hidden" name="mobile" value="'+mobile+'">\n'
              instanz_starten_tabelle += '<input type="hidden" name="image_id" value="'+image+'">\n'
              instanz_starten_tabelle += '<table border="0" cellspacing="0" cellpadding="5" width="300">\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>AMI:</b></td>\n'
              instanz_starten_tabelle += '<td align="left">'+image+'</td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>Manifest:</b></td>\n'
              instanz_starten_tabelle += '<td align="left">'+manifest+'</td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>Root:</b></td>\n'
              instanz_starten_tabelle += '<td align="left">'+root+'</td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>AKI:</b></td>\n'
              instanz_starten_tabelle += '<td align="left"><input name="aki_id" type="text" size="12" maxlength="12"></td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>ARI:</b></td>\n'
              instanz_starten_tabelle += '<td align="left"><input name="ari_id" type="text" size="12" maxlength="12"></td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              if sprache == "de":
                instanz_starten_tabelle += '<td align="right"><b>Typ:</b></td>\n'
              else:
                instanz_starten_tabelle += '<td align="right"><b>Type:</b></td>\n'
              instanz_starten_tabelle += '<td align="left">'
              instanz_starten_tabelle += '<select name="instance_type" size="1">'+instance_types_liste+'</select>\n'
              instanz_starten_tabelle += '</td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>Zone:</b></td>\n'
              instanz_starten_tabelle += '<td align="left">'
              instanz_starten_tabelle += '<select name="zonen_auswahl" size="1">'+zonen_in_der_region+'</select>\n'
              instanz_starten_tabelle += '</td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>Min:</b></td>\n'
              instanz_starten_tabelle += '<td align="left"><input name="number_instances_min" type="text" size="2" maxlength="2" value="1"></td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>Max:</b></td>\n'
              instanz_starten_tabelle += '<td align="left"><input name="number_instances_max" type="text" size="2" maxlength="2" value="1"></td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              if sprache == "de":
                instanz_starten_tabelle += '<td align="right"><b>Schl&uuml;ssel:</b></td>\n'
              else:
                instanz_starten_tabelle += '<td align="right"><b>Keypair:</b></td>\n'
              instanz_starten_tabelle += '<td align="left">'+keys_liste+'</td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              if sprache == "de":
                instanz_starten_tabelle += '<td align="right"><b>Gruppe:</b></td>\n'
              else:
                instanz_starten_tabelle += '<td align="right"><b>Group:</b></td>\n'
              instanz_starten_tabelle += '<td align="left">'+gruppen_liste+'</td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td colspan="2" align="left">'
              if sprache == "de":
                instanz_starten_tabelle += '<input type="submit" value="Instanz starten">'
              else:
                instanz_starten_tabelle += '<input type="submit" value="create Instance">'
              instanz_starten_tabelle += '</td>\n'          
              instanz_starten_tabelle += '</tr>\n'            
              instanz_starten_tabelle += '</table>\n'
              instanz_starten_tabelle += '</form>\n'
              
            else:
              # Not the mobile version...
              
              instanz_starten_tabelle += '<form action="/instanzanlegen" method="post" accept-charset="utf-8">\n'
              instanz_starten_tabelle += '<input type="hidden" name="mobile" value="'+mobile+'">\n'
              instanz_starten_tabelle += '<input type="hidden" name="image_id" value="'+image+'">\n'
              instanz_starten_tabelle += '<table border="0" cellspacing="0" cellpadding="5">\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>AMI:</b></td>\n'
              instanz_starten_tabelle += '<td align="left">'+image+'</td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>Manifest:</b></td>\n'
              instanz_starten_tabelle += '<td align="left">'+manifest+'</td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>Root:</b></td>\n'
              instanz_starten_tabelle += '<td align="left">'+root+'</td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>AKI:</b></td>\n'
              instanz_starten_tabelle += '<td align="left"><input name="aki_id" type="text" size="12" maxlength="12"></td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>ARI:</b></td>\n'
              instanz_starten_tabelle += '<td align="left"><input name="ari_id" type="text" size="12" maxlength="12"></td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              if sprache == "de":
                instanz_starten_tabelle += '<td align="right"><b>Typ:</b></td>\n'
              else:
                instanz_starten_tabelle += '<td align="right"><b>Type:</b></td>\n'
              instanz_starten_tabelle += '<td align="left">'
              instanz_starten_tabelle += '<select name="instance_type" size="1">'+instance_types_liste+'</select>\n'
              instanz_starten_tabelle += '</td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>Zone:</b></td>\n'
              instanz_starten_tabelle += '<td align="left">'
              instanz_starten_tabelle += '<select name="zonen_auswahl" size="1">'+zonen_in_der_region+'</select>\n'
              instanz_starten_tabelle += '</td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>Min:</b></td>\n'
              instanz_starten_tabelle += '<td align="left"><input name="number_instances_min" type="text" size="2" maxlength="2" value="1"></td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td align="right"><b>Max:</b></td>\n'
              instanz_starten_tabelle += '<td align="left"><input name="number_instances_max" type="text" size="2" maxlength="2" value="1"></td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              if sprache == "de":
                instanz_starten_tabelle += '<td align="right"><b>Schl&uuml;ssel:</b></td>\n'
              else:
                instanz_starten_tabelle += '<td align="right"><b>Keypair:</b></td>\n'
              instanz_starten_tabelle += '<td align="left">'+keys_liste+'</td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              if sprache == "de":
                instanz_starten_tabelle += '<td align="right"><b>Gruppe:</b></td>\n'
              else:
                instanz_starten_tabelle += '<td align="right"><b>Group:</b></td>\n'
              instanz_starten_tabelle += '<td align="left">'+gruppen_liste+'</td>\n'
              instanz_starten_tabelle += '</tr>\n'
              instanz_starten_tabelle += '<tr>\n'
              instanz_starten_tabelle += '<td colspan="2" align="left">'
              if sprache == "de":
                instanz_starten_tabelle += '<input type="submit" value="Instanz starten">'
              else:
                instanz_starten_tabelle += '<input type="submit" value="create Instance">'
              instanz_starten_tabelle += '</td>\n'          
              instanz_starten_tabelle += '</tr>\n'            
              instanz_starten_tabelle += '</table>\n'
              instanz_starten_tabelle += '</form>\n'
              

          # Wenn es Amazon EC2 ist
          if result.aktivezone in ("us-east-1", "eu-west-1", "us-west-1", "ap-southeast-1"):
            if arch == "i386": # 32-Bit Image
              tabelle_ec2_instanztypen = '<table border="3" cellspacing="0" cellpadding="5">'
              tabelle_ec2_instanztypen += '<tr>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen += '<th>Instanztyp</th>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen += '<th>Type</th>'
              tabelle_ec2_instanztypen += '<th>Bit</th>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen += '<th>Kerne</th>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen += '<th>Cores</th>'
              tabelle_ec2_instanztypen += '<th align="center">ECU</th>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen += '<th align="center">RAM</th>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen += '<th align="center">RAM</th>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen += '<th align="center">Speicher</th>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen += '<th align="center">Storage</th>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>t1.micro</td>'
              tabelle_ec2_instanztypen += '<td align="center">32</td>'
              tabelle_ec2_instanztypen += '<td align="center">1</td>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen += '<td align="center">bis zu 2</td>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen += '<td align="center">up to 2</td>'
              tabelle_ec2_instanztypen += '<td align="center">613 MB</td>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen += '<td align="center">nur EBS</td>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen += '<td align="center">only EBS</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>m1.small</td>'
              tabelle_ec2_instanztypen += '<td align="center">32</td>'
              tabelle_ec2_instanztypen += '<td align="center">1</td>'
              tabelle_ec2_instanztypen += '<td align="center">1</td>'
              tabelle_ec2_instanztypen += '<td align="center">1.7 GB</td>'
              tabelle_ec2_instanztypen += '<td align="center">160 GB</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>c1.medium</td>'
              tabelle_ec2_instanztypen += '<td align="center">32</td>'
              tabelle_ec2_instanztypen += '<td align="center">2</td>'
              tabelle_ec2_instanztypen += '<td align="center">5</td>'
              tabelle_ec2_instanztypen += '<td align="center">1.7 GB</td>'
              tabelle_ec2_instanztypen += '<td align="center">350 GB</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '</table>'
            
              if root != "ebs":
                if sprache == "de":
                  t1_micro_warnung = '<font color="red">t1.micro Instanzen ben&ouml;tigen als Root EBS</font>'
                else:
                  t1_micro_warnung = '<font color="red">t1.micro instances must have an EBS root device</font>'
              else:
                t1_micro_warnung = ''

            elif arch == "x86_64": # 64-Bit Image
              tabelle_ec2_instanztypen = '<table border="3" cellspacing="0" cellpadding="5">'
              tabelle_ec2_instanztypen += '<tr>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen += '<th>Instanztyp</th>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen += '<th>Type</th>'
              tabelle_ec2_instanztypen += '<th>Bit</th>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen += '<th>Kerne</th>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen += '<th>Cores</th>'
              tabelle_ec2_instanztypen += '<th align="center">ECU</th>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen += '<th align="center">RAM</th>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen += '<th align="center">RAM</th>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen += '<th align="center">Speicher</th>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen += '<th align="center">Storage</th>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>t1.micro</td>'
              tabelle_ec2_instanztypen += '<td align="center">64</td>'
              tabelle_ec2_instanztypen += '<td align="center">1</td>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen += '<td align="center">bis zu 2</td>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen += '<td align="center">up to 2</td>'
              tabelle_ec2_instanztypen += '<td align="center">613 MB</td>'
              if sprache == "de": # Wenn die Sprache Deutsch ist...
                tabelle_ec2_instanztypen += '<td align="center">nur EBS</td>'
              else:               # Wenn die Sprache Englisch ist...
                tabelle_ec2_instanztypen += '<td align="center">only EBS</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>m1.small</td>'
              tabelle_ec2_instanztypen += '<td align="center">32</td>'
              tabelle_ec2_instanztypen += '<td align="center">1</td>'
              tabelle_ec2_instanztypen += '<td align="center">1</td>'
              tabelle_ec2_instanztypen += '<td align="center">1.7 GB</td>'
              tabelle_ec2_instanztypen += '<td align="center">160 GB</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>m1.medium</td>'
              tabelle_ec2_instanztypen += '<td align="center">32</td>'
              tabelle_ec2_instanztypen += '<td align="center">2</td>'
              tabelle_ec2_instanztypen += '<td align="center">5</td>'
              tabelle_ec2_instanztypen += '<td align="center">1.7 GB</td>'
              tabelle_ec2_instanztypen += '<td align="center">410 GB</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>m1.large</td>'
              tabelle_ec2_instanztypen += '<td align="center">64</td>'
              tabelle_ec2_instanztypen += '<td align="center">2</td>'
              tabelle_ec2_instanztypen += '<td align="center">4</td>'
              tabelle_ec2_instanztypen += '<td align="center">7.5 GB</td>'
              tabelle_ec2_instanztypen += '<td align="center">850 GB</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>m1.xlarge</td>'
              tabelle_ec2_instanztypen += '<td align="center">64</td>'
              tabelle_ec2_instanztypen += '<td align="center">4</td>'
              tabelle_ec2_instanztypen += '<td align="center">8</td>'
              tabelle_ec2_instanztypen += '<td align="center">15 GB</td>'
              tabelle_ec2_instanztypen += '<td align="center">1690 GB</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>m2.xlarge</td>'
              tabelle_ec2_instanztypen += '<td align="center">64</td>'
              tabelle_ec2_instanztypen += '<td align="center">2</td>'
              tabelle_ec2_instanztypen += '<td align="center">6.5</td>'
              tabelle_ec2_instanztypen += '<td align="center">17.1 GB</td>'
              tabelle_ec2_instanztypen += '<td align="center">420 GB</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>m2.2xlarge</td>'
              tabelle_ec2_instanztypen += '<td align="center">64</td>'
              tabelle_ec2_instanztypen += '<td align="center">4</td>'
              tabelle_ec2_instanztypen += '<td align="center">13</td>'
              tabelle_ec2_instanztypen += '<td align="center">34.2 GB</td>'
              tabelle_ec2_instanztypen += '<td align="center">850 GB</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>m2.4xlarge</td>'
              tabelle_ec2_instanztypen += '<td align="center">64</td>'
              tabelle_ec2_instanztypen += '<td align="center">8</td>'
              tabelle_ec2_instanztypen += '<td align="center">26</td>'
              tabelle_ec2_instanztypen += '<td align="center">68.4 GB</td>'
              tabelle_ec2_instanztypen += '<td align="center">1690 GB</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>c1.medium</td>'
              tabelle_ec2_instanztypen += '<td align="center">32</td>'
              tabelle_ec2_instanztypen += '<td align="center">2</td>'
              tabelle_ec2_instanztypen += '<td align="center">5</td>'
              tabelle_ec2_instanztypen += '<td align="center">1.7 GB</td>'
              tabelle_ec2_instanztypen += '<td align="center">350 GB</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>c1.xlarge</td>'
              tabelle_ec2_instanztypen += '<td align="center">64</td>'
              tabelle_ec2_instanztypen += '<td align="center">8</td>'
              tabelle_ec2_instanztypen += '<td align="center">20</td>'
              tabelle_ec2_instanztypen += '<td align="center">7 GB</td>'
              tabelle_ec2_instanztypen += '<td align="center">1690 GB</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>cc1.4xlarge</td>'
              tabelle_ec2_instanztypen += '<td align="center">64</td>'
              tabelle_ec2_instanztypen += '<td align="center">8</td>'
              tabelle_ec2_instanztypen += '<td align="center">33,5</td>'
              tabelle_ec2_instanztypen += '<td align="center">23 GB</td>'
              tabelle_ec2_instanztypen += '<td align="center">1690 GB</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>cc2.8xlarge</td>'
              tabelle_ec2_instanztypen += '<td align="center">64</td>'
              tabelle_ec2_instanztypen += '<td align="center">16</td>'
              tabelle_ec2_instanztypen += '<td align="center">88</td>'
              tabelle_ec2_instanztypen += '<td align="center">60.5 GB</td>'
              tabelle_ec2_instanztypen += '<td align="center">3370 GB</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '<tr>'
              tabelle_ec2_instanztypen += '<td>cg1.4xlarge</td>'
              tabelle_ec2_instanztypen += '<td align="center">64</td>'
              tabelle_ec2_instanztypen += '<td align="center">8</td>'
              tabelle_ec2_instanztypen += '<td align="center">33,5</td>'
              tabelle_ec2_instanztypen += '<td align="center">22 GB</td>'
              tabelle_ec2_instanztypen += '<td align="center">1690 GB</td>'
              tabelle_ec2_instanztypen += '</tr>'
              tabelle_ec2_instanztypen += '</table>'
              
              if root != "ebs":
                if sprache == "de":
                  t1_micro_warnung = '<font color="red">t1.micro Instanzen ben&ouml;tigen als Root Device EBS</font>'
                else:
                  t1_micro_warnung = '<font color="red">t1.micro instances must have an EBS root device</font>'
              else:
                t1_micro_warnung = ''

            else:
              # Wenn es etwas ganz anderes ist...?
              tabelle_ec2_instanztypen = ''
              t1_micro_warnung = ''
          else:
            # wenn es Eucalyptus ist
            tabelle_ec2_instanztypen = ''
            t1_micro_warnung = ''
          
          path = '&amp;path=images&amp;mobile='+mobile
          
          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'instance_types_liste': instance_types_liste,
          'instance_types_liste_laenge': instance_types_liste_laenge,
          'keys_liste': keys_liste,
          'gruppen_liste': gruppen_liste,
          'zonen_liste': zonen_liste,
          'tabelle_ec2_instanztypen':tabelle_ec2_instanztypen,
          'zonen_in_der_region': zonen_in_der_region,
          'laenge_liste_zonen': laenge_liste_zonen,
          't1_micro_warnung': t1_micro_warnung,
          'instanz_starten_tabelle': instanz_starten_tabelle,
          'mobile': mobile,
          'path': path,
          }

          if mobile == "true":
              path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "image_starten.html")
          else:
              path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "image_starten.html")
          self.response.out.write(template.render(path,template_values))


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
from library import logins3

from dateutil.parser import *

from error_messages import error_messages

class ACL_einsehen(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
          self.redirect('/')
        # Namen des Buckets holen, in dem der Key ist
        bucketname = self.request.get('bucket')
        # Namen des Keys holen, dessen ACL angezeigt wird
        keyname = self.request.get('key')
        # War es die reine S3-Darstellung oder die Komfort-Darstellung, aus der die 
        # Anfrage zu Löschen des Keys kam?
        typ = self.request.get('typ')
        # Verzeichnis holen, wenn es die Komfort-Ansicht war
        directory = self.request.get('dir')

        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if not results:
          self.redirect('/')
        else:
          # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
          sprache = aktuelle_sprache(username)
          navigations_bar = navigations_bar_funktion(sprache,mobile)

          results = aktivezone.fetch(100)

          url = users.create_logout_url(self.request.uri).replace('&', '&amp;').replace('&amp;amp;', '&amp;')
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache,mobile)

          # Mit S3 verbinden
          conn_s3 = logins3(username)
          bucket_instance = conn_s3.get_bucket(bucketname)

          key_instance = bucket_instance.get_acl(keyname)

          acl = bucket_instance.get_acl(key_name=keyname)

          AllUsersREAD  = ''
          AllUsersWRITE = ''
          AllUsersFULL  = ''
          AuthentUsersREAD   = ''
          AuthentUsersWRITE  = ''
          AuthentUsersFULL   = ''
          OwnerName   = ''
          OwnerREAD   = ''
          OwnerWRITE  = ''
          OwnerFULL   = ''

          for grant in acl.acl.grants:
            if str(grant.uri).find('AllUsers') != -1 and grant.permission == 'READ':
              AllUsersREAD  = 'tick.png'
            if str(grant.uri).find('AllUsers') != -1 and grant.permission == 'WRITE':
              AllUsersWRITE = 'tick.png'
            if str(grant.uri).find('AllUsers') != -1 and grant.permission == 'FULL_CONTROL':
              AllUsersREAD  = 'tick.png'
              AllUsersWRITE = 'tick.png'
              AllUsersFULL  = 'tick.png'
            if str(grant.uri).find('AuthenticatedUsers') != -1 and grant.permission == 'READ':
              AuthentUsersREAD  = 'tick.png'
            elif str(grant.uri).find('AuthenticatedUsers') != -1 and grant.permission == 'WRITE':
              AuthentUsersWRITE = 'tick.png'
            elif str(grant.uri).find('AuthenticatedUsers') != -1 and grant.permission == 'FULL_CONTROL':
              AuthentUsersFULL  = 'tick.png'
            # Wenn der Besitzer des Keys dieser Eintrag hier ist...
            if str(key_instance.owner.id) == str(grant.id):
              OwnerName = str(grant.display_name)
              if grant.permission == 'READ':
                OwnerREAD   = 'tick.png'
              if grant.permission == 'WRITE':
                OwnerWRITE  = 'tick.png'
              if grant.permission == 'FULL_CONTROL':
                OwnerREAD   = 'tick.png'
                OwnerWRITE  = 'tick.png'
                OwnerFull   = 'tick.png'

          if AllUsersREAD  == '': AllUsersREAD  = 'delete.png'
          if AllUsersWRITE == '': AllUsersWRITE = 'delete.png'
          if AllUsersFULL  == '': AllUsersFULL  = 'delete.png'
          if AuthentUsersREAD  == '': AuthentUsersREAD  = 'delete.png'
          if AuthentUsersWRITE == '': AuthentUsersWRITE = 'delete.png'
          if AuthentUsersFULL  == '': AuthentUsersFULL  = 'delete.png'
          if OwnerREAD  == '': OwnerREAD  = 'delete.png'
          if OwnerWRITE == '': OwnerWRITE = 'delete.png'
          if OwnerFull  == '': OwnerFull  = 'delete.png'

          acl_tabelle = '\n'
          acl_tabelle = acl_tabelle + '<table border="0" cellspacing="0" cellpadding="5"> \n'
          acl_tabelle = acl_tabelle + '<tr> \n'
          if sprache == "de": 
            acl_tabelle = acl_tabelle + '<th align="left">Benutzer</th> \n'
            acl_tabelle = acl_tabelle + '<th align="center">Lesen</th> \n'
            acl_tabelle = acl_tabelle + '<th align="center">Schreiben</th> \n'
            acl_tabelle = acl_tabelle + '<th align="center">Voller Zugriff</th> \n'
          else:
            acl_tabelle = acl_tabelle + '<th align="left">User</th> \n'
            acl_tabelle = acl_tabelle + '<th align="center">Read</th> \n'
            acl_tabelle = acl_tabelle + '<th align="center">Write</th> \n'
            acl_tabelle = acl_tabelle + '<th align="center">Full Control</th> \n'
          acl_tabelle = acl_tabelle + '</tr> \n'
          acl_tabelle = acl_tabelle + '<tr> \n'
          if sprache == "de": acl_tabelle = acl_tabelle + '<td>Alle</td> \n'
          else:               acl_tabelle = acl_tabelle + '<td>Everyone</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+AllUsersREAD+'" width="24" height="24" border="0" alt="'+AllUsersREAD+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+AllUsersWRITE+'" width="24" height="24" border="0" alt="'+AllUsersWRITE+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+AllUsersFULL+'" width="24" height="24" border="0" alt="'+AllUsersFULL+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '</tr> \n'
          acl_tabelle = acl_tabelle + '<tr> \n'
          if sprache == "de": acl_tabelle = acl_tabelle + '<td>Authentifizierte Benutzer</td> \n'
          else:               acl_tabelle = acl_tabelle + '<td>Authenticated Users</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+AuthentUsersREAD+'" width="24" height="24" border="0" alt="'+AuthentUsersREAD+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+AuthentUsersWRITE+'" width="24" height="24" border="0" alt="'+AuthentUsersWRITE+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+AuthentUsersFULL+'" width="24" height="24" border="0" alt="'+AuthentUsersFULL+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '</tr> \n'
          acl_tabelle = acl_tabelle + '<tr> \n'
          if sprache == "de": acl_tabelle = acl_tabelle + '<td>'+OwnerName+' (Besitzer)</td> \n'
          else:               acl_tabelle = acl_tabelle + '<td>'+OwnerName+' Owner</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+OwnerREAD+'" width="24" height="24" border="0" alt="'+OwnerREAD+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+OwnerWRITE+'" width="24" height="24" border="0" alt="'+OwnerWRITE+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '<td align="center"> \n'
          acl_tabelle = acl_tabelle + '<img src="bilder/'+OwnerFull+'" width="24" height="24" border="0" alt="'+OwnerFull+'"> \n'
          acl_tabelle = acl_tabelle + '</td> \n'
          acl_tabelle = acl_tabelle + '</tr> \n'
          acl_tabelle = acl_tabelle + '</table> \n'

          # Wenn man sich NICHT unter Amazon befindet, funktioniert das Ändern der ACL nicht.
          if regionname == "Amazon":
            eucalyptus_warnung = ''
          elif regionname == "GoogleStorage":
            eucalyptus_warnung = ''
          else: 
            if sprache == "de":
              eucalyptus_warnung = '<B>Achtung!</B> Unter Eucalyptus 1.6 und 1.6.1 funktioniert das &Auml;ndern der Zugriffsberechtigung (Access Control List) nicht.</B>'
            else:
              eucalyptus_warnung = '<B>Attention!</B> With Eucalyptus 1.6 and 1.6.1 changing the ACL is broken.</B>'
            
          path = '&amp;path=s3&amp;mobile='+mobile
          
          template_values = {
          'navigations_bar': navigations_bar,
          'url': url,
          'url_linktext': url_linktext,
          'zone': regionname,
          'zone_amazon': zone_amazon,
          'zonen_liste': zonen_liste,
          'bucketname': bucketname,
          'keyname': keyname,
          'acl_tabelle': acl_tabelle,
          'typ': typ,
          'directory': directory,
          'eucalyptus_warnung': eucalyptus_warnung,
          'mobile': mobile,
          'path': path,
          }

          if mobile == "true":
              path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "acl.html")
          else:
              path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "acl.html")
          self.response.out.write(template.render(path,template_values))



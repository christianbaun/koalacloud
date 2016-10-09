#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os

from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch import DownloadError
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext.webapp import template

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

class Keys(webapp.RequestHandler):
    def get(self):
        # self.response.out.write('posted!')
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
          self.redirect('/')
        # Wurde ein neuer Schlüssel angelegt?
        neu = self.request.get('neu')
        # Name des neuen Schlüssels
        neuerkeyname = self.request.get('neuerkeyname')
        # Name des Datastore-Schlüssels, unter dem der Secret-Key angehegt ist
        secretkey = self.request.get('secretkey')
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')

        #So könnte man vielleicht den File-Download-Dialog bekommen
        #Content-disposition: attachment; filename="fname.ext"


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

          # It is Google Storage and not am IaaS  
          if regionname == "GoogleStorage":
            
            path = '&amp;path=schluessel&amp;mobile='+mobile
            
            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'zonen_liste': zonen_liste,
            'path': path,
            }
            if mobile == "true":
                path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "not_implemente_with_google_storage.html")
            else:
                path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "not_implemente_with_google_storage.html")
            self.response.out.write(template.render(path,template_values))
            
          # It is Host Europe Cloud Storage and not am IaaS  
          elif regionname == "HostEuropeCloudStorage":
            
            path = '&amp;path=zonen&amp;mobile='+mobile
            
            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'zonen_liste': zonen_liste,
            'path': path,
            }

            if mobile == "true":
                path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "not_implemente_with_host_europe_storage.html")
            else:
                path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "not_implemente_with_host_europe_storage.html")
            self.response.out.write(template.render(path,template_values))
            

            
          # It is not Google Storage. It is an IaaS
          else:   

            if sprache != "de":
              sprache = "en"
  
            input_error_message = error_messages.get(message, {}).get(sprache)
  
            # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
            if input_error_message == None:
              input_error_message = ""
  
            # Wenn die Nachricht grün formatiert werden soll...
            if message in ("99", "103"):
              # wird sie hier, in der Hilfsfunktion grün formatiert
              input_error_message = format_error_message_green(input_error_message)
            # Ansonsten wird die Nachricht rot formatiert
            elif message in ("8", "92", "100", "101", "102", "104"):
              input_error_message = format_error_message_red(input_error_message)
            else:
              input_error_message = ""
  
            try:
              # Liste mit den Keys
              liste_key_pairs = conn_region.get_all_key_pairs()
            except EC2ResponseError:
              # Wenn es nicht klappt...
              if sprache == "de":
                keytabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
              else:
                keytabelle = '<font color="red">An error occured</font>'
            except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              if sprache == "de":
                keytabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
              else:
                keytabelle = '<font color="red">A timeout error occured</font>'
            else:
              # Wenn es geklappt hat...
              # Anzahl der Elemente in der Liste
              laenge_liste_keys = len(liste_key_pairs)
  
              if laenge_liste_keys == 0:
                if sprache == "de":
                  keytabelle = 'Sie haben keine Schl&uuml;sselpaare in dieser Region.'
                else:
                  keytabelle = 'You have no keypairs inside this region.'
              else:
                if mobile == "true":
                    keytabelle = ''
                    keytabelle += '<table border="0" cellspacing="0" cellpadding="5">'
                   
                    counter = 0
                    
                    for i in range(laenge_liste_keys):
                        if counter > 0:
                            keytabelle += '<tr><td colspan="2">&nbsp;</td></tr>'
                        counter += 1
                      
                        keytabelle += '<tr>'
                        keytabelle += '<td>'
                        keytabelle += '<a href="/schluesselentfernen?key='
                        keytabelle += liste_key_pairs[i].name
                        keytabelle += "&amp;mobile="
                        keytabelle += str(mobile)
                        keytabelle += '"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Schl&uuml;sselpaar l&ouml;schen"></a>'
                        keytabelle += '</td>'
                        keytabelle += '<td>'+liste_key_pairs[i].name+'</td>'
                        keytabelle += '</tr>'
#                        keytabelle += '<tr>'
#                        keytabelle += '<td>&nbsp;</td>'
#                        keytabelle += '<td><tt>'+liste_key_pairs[i].fingerprint+'</tt></td>'
#                        keytabelle += '</tr>'
                    keytabelle = keytabelle + '</table>'
                else:
                    keytabelle = ''
                    keytabelle += '<table border="0" cellspacing="0" cellpadding="5">'
                    keytabelle += '<tr>'
                    keytabelle += '<th>&nbsp;</th>'
                    keytabelle += '<th align="center">Name</th>'
                    if sprache == "de":
                      keytabelle += '<th align="center">Pr&uuml;fsumme</th>'
                    else:
                      keytabelle += '<th align="center">Fingerprint</th>'
                    keytabelle = keytabelle + '</tr>'
                    for i in range(laenge_liste_keys):
                        keytabelle += '<tr>'
                        keytabelle += '<td>'
                        keytabelle += '<a href="/schluesselentfernen?key='
                        keytabelle += liste_key_pairs[i].name
                        keytabelle += "&amp;mobile="
                        keytabelle += str(mobile)
                        keytabelle += '"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Schl&uuml;sselpaar l&ouml;schen"></a>'
                        keytabelle += '</td>'
                        keytabelle += '<td>'+liste_key_pairs[i].name+'</td>'
                        keytabelle += '<td><tt>'+liste_key_pairs[i].fingerprint+'</tt></td>'
                        keytabelle += '</tr>'
                    keytabelle = keytabelle + '</table>'
  
              if neu == "ja":
                secretkey_memcache_mit_zeilenumbruch = memcache.get(secretkey)
                secretkey_memcache = secretkey_memcache_mit_zeilenumbruch.replace("\n","<BR>")
                # Das wird in den Body-Tag der Datei base.html eingefügt. 
#                bodycommand = ' onLoad="newkey()" '
#                javascript_funktion = '''
#<SCRIPT LANGUAGE="JavaScript" TYPE="text/javascript">
#  <!--  to hide script contents from old browsers
#  function newkey()
#  {
#  OpenWindow=window.open("", "newwin", "height=450, width=500,toolbar=no,scrollbars="+scroll+",menubar=no")
#  OpenWindow.document.write("<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01 Transitional//EN'")
#  OpenWindow.document.write("      'http://www.w3.org/TR/html4/loose.dtd'>")
#
#  OpenWindow.document.write("<HTML>")
#  OpenWindow.document.write("<HEAD>")
#  OpenWindow.document.write("<meta http-equiv='Content-Type' content='text/html; charset=UTF-8'>")
#  OpenWindow.document.write("<TITLE>Secret Key<\/TITLE>")
#  OpenWindow.document.write("<link type='text/css' rel='stylesheet' href='/stylesheets/style.css'>")
#  OpenWindow.document.write("<link rel='SHORTCUT ICON' href='/favicon.ico'>")
#  OpenWindow.document.write("<\/HEAD>")
#  OpenWindow.document.write("<BODY BGCOLOR='white'>")
#  OpenWindow.document.write("<h1>Secret Key<\/h1>")
#  OpenWindow.document.write("<P>&nbsp;<\/P>")
#  OpenWindow.document.write("<tt>'''
#                javascript_funktion = javascript_funktion + secretkey_memcache
#                if sprache == "de":
#                  javascript_funktion = javascript_funktion + '''<\/tt>")
#                  OpenWindow.document.write("<P>&nbsp;<\/P>")
#                  OpenWindow.document.write("<B>Achtung!<\/B> Den Secret Key m&uuml;ssen Sie speichern.<BR>")
#                  OpenWindow.document.write("Am besten in einer Datei <tt>'''
#                else:
#                  javascript_funktion = javascript_funktion + '''<\/tt>")
#                  OpenWindow.document.write("<P>&nbsp;<\/P>")
#                  OpenWindow.document.write("<B>Attention!<\/B> The secret key need to be saved.<BR>")
#                  OpenWindow.document.write("As an advise use the filename <tt>'''
#                javascript_funktion = javascript_funktion + neuerkeyname
#                javascript_funktion = javascript_funktion + '''.secret<\/tt>.")
#                OpenWindow.document.write("<P>&nbsp;<\/P>")
#                OpenWindow.document.write("<tt>chmod 600 '''
#                javascript_funktion = javascript_funktion + neuerkeyname
#                javascript_funktion = javascript_funktion + '''.secret<\/tt>")
#  OpenWindow.document.write("<\/BODY>")
#  OpenWindow.document.write("<\/HTML>")
#  OpenWindow.document.close()
#  self.name="main"
#  }
#  // end hiding contents from old browsers  -->
#</SCRIPT>'''
                new_keypair_secretkey = ''
                if sprache == "de":
                  new_keypair_secretkey += '<b>Ihr neuer geheimer Schl&uuml;ssel</b>'
                else:
                  new_keypair_secretkey += '<b>Your new secret key</b>'
                new_keypair_secretkey += '<p>&nbsp;</p>'
                new_keypair_secretkey += '<tt>'+secretkey_memcache+'</tt>'
                new_keypair_secretkey += '<p>&nbsp;</p>'
                if sprache == "de":
                  new_keypair_secretkey += '<b>Achtung!</b> Ihren geheimen Schl&uuml;ssel m&uuml;ssen Sie speichern. Am besten in einer lokalen Datei mit den korrekten Benutzerrechten.<BR>'
                  new_keypair_secretkey += '<tt>chmod 600 '+neuerkeyname+'.secret</tt>'
                else:
                  new_keypair_secretkey += '<b>Attention!</b> You need to save your new secret key. As an advise use a local file with the correct user access rights.BR>'
                  new_keypair_secretkey += '<tt>chmod 600 '+neuerkeyname+'.secret</tt>'
                new_keypair_secretkey += '<p>&nbsp;</p>'         
                
                
                new_keypair_secretkey_download_link = ''
                new_keypair_secretkey_download_link += '<a href="'+secretkey_memcache+'">'+neuerkeyname+'.secret</a>'
                new_keypair_secretkey_download_link += '<p>&nbsp;</p>' 
                                       
              else:
                  # neu ist nicht "ja"
#                  bodycommand = " "
#                  javascript_funktion = " "
                  new_keypair_secretkey = ""
                  new_keypair_secretkey_download_link = ""
  
              path = '&amp;path=schluessel&amp;mobile='+mobile
  
              template_values = {
              'navigations_bar': navigations_bar,
              'url': url,
              'url_linktext': url_linktext,
              'zone': regionname,
              'zone_amazon': zone_amazon,
              'keytabelle': keytabelle,
#              'bodycommand': bodycommand,
#              'javascript_funktion': javascript_funktion,
              'zonen_liste': zonen_liste,
              'input_error_message': input_error_message,
              'mobile': mobile,
              'new_keypair_secretkey': new_keypair_secretkey,
              'new_keypair_secretkey_download_link': new_keypair_secretkey_download_link,
              'path': path,
              }
  
              if mobile == "true":
                  path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "keys.html")
              else:
                  path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "keys.html")
              self.response.out.write(template.render(path,template_values))


#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api.urlfetch import DownloadError

from library import login

from library import login
from library import aktuelle_sprache
from library import navigations_bar_funktion
from library import amazon_region
from library import zonen_liste_funktion
from library import format_error_message_green
from library import format_error_message_red

from error_messages import error_messages

from dateutil.parser import *

from boto.ec2.connection import *

class SnapshotsAmazonAll(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
          self.redirect('/')
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')

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

          # It is Google Storage and not am IaaS  
          if regionname == "GoogleStorage":
            
            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'zonen_liste': zonen_liste,
            }
  
            path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "not_implemente_with_google_storage.html")
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
            if message in ("11", "13"):
              # wird sie hier, in der Hilfsfunktion grün formatiert
              input_error_message = format_error_message_green(input_error_message)
            # Ansonsten wird die Nachricht rot formatiert
            elif message in ("8", "12", "14"):
              input_error_message = format_error_message_red(input_error_message)
            else:
              input_error_message = ""
  
            try:
              # Liste mit den Snapshots
              liste_snapshots = conn_region.get_all_snapshots(owner="amazon")
            except EC2ResponseError:
              # Wenn es nicht klappt...
              if sprache == "de":
                snapshotstabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
              else:
                snapshotstabelle = '<font color="red">An error occured</font>'
            except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              if sprache == "de":
                snapshotstabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
              else:
                snapshotstabelle = '<font color="red">A timeout error occured</font>'
            else:
              # Wenn es geklappt hat...
              # Anzahl der Snapshots in der Liste
              laenge_liste_snapshots = len(liste_snapshots)
  
              if laenge_liste_snapshots == 0:
                if sprache == "de":
                  snapshotstabelle = 'Es sind keine Snapshots in der Region vorhanden.'
                else:
                  snapshotstabelle = 'No snapshots exist inside this region.'
              else: 

                if mobile == "true":
                  # Mobile version of the table
                  snapshotstabelle = ''
                  snapshotstabelle += '<table border="0" cellspacing="0" cellpadding="5" width="300">'
                 
                  counter = 0
                  for i in range(laenge_liste_snapshots):
                    
                      if counter > 0:
                          snapshotstabelle += '<tr><td colspan="3">&nbsp;</td></tr>'
                      counter += 1
                      
                      snapshotstabelle += '<tr>'
                      snapshotstabelle += '<td colspan="2" align="left">'
                      snapshotstabelle += '<a href="/snapshotsentfernen?snapshot='
                      snapshotstabelle += liste_snapshots[i].id
                      snapshotstabelle += "&amp;mobile="
                      snapshotstabelle += str(mobile)
                      snapshotstabelle += "&amp;ami=all"
                      if sprache == "de":
                        snapshotstabelle += '" title="Snapshot l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Snapshot l&ouml;schen"></a>'
                      else:
                        snapshotstabelle += '" title="erase snapshot"><img src="bilder/delete.png" width="16" height="16" border="0" alt="snapshot volume"></a>'
                      snapshotstabelle += '</td>'
                      snapshotstabelle += '<td align="center">'
                      snapshotstabelle += '<a href="/volumeaussnapshoterzeugen?snapshot='
                      snapshotstabelle += liste_snapshots[i].id
                      snapshotstabelle += "&amp;mobile="
                      snapshotstabelle += str(mobile)
                      if sprache == "de":
                        snapshotstabelle += '" title="Volume erzeugen"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Volume erzeugen"></a>'
                      else:
                        snapshotstabelle += '" title="create volume"><img src="bilder/plus.png" width="16" height="16" border="0" alt="create volume"></a>'
                      snapshotstabelle += '</td>'
                      snapshotstabelle += '</tr>'
                        
                      snapshotstabelle += '<tr>'
                      snapshotstabelle += '<td colspan="2" align="right"><b>ID:</b></td>'
                      snapshotstabelle += '<td align="center">'+liste_snapshots[i].id+'</td>'
                      snapshotstabelle += '</tr>'
                      
                      snapshotstabelle += '<tr>'
                      snapshotstabelle += '<td colspan="2" align="right"><b>Volume:</b></td>'
                      snapshotstabelle += '<td align="center"><tt>'+liste_snapshots[i].volume_id+'</tt></td>'
                      snapshotstabelle += '</tr>'
                      
                      snapshotstabelle += '<tr>'
                      if sprache == "de":
                        snapshotstabelle += '<td colspan="2" align="right"><b>Gr&ouml;&szlig;e:</b></td>'
                      else:
                        snapshotstabelle += '<td colspan="2" align="right"><b>Size:</b></td>'
                      snapshotstabelle += '<td align="center">'+str(liste_snapshots[i].volume_size)+' GB</td>'
                      snapshotstabelle += '</tr>'
                      
                      snapshotstabelle += '<tr>'
                      snapshotstabelle += '<td colspan="2" align="right"><b>Status:</b></td>'
                      if liste_snapshots[i].status == u'completed':
                        snapshotstabelle += '<td bgcolor="#c3ddc3" align="center">'+liste_snapshots[i].status+'</td>'
                      elif liste_snapshots[i].status == u'pending':
                        snapshotstabelle += '<td bgcolor="#ffffcc" align="center">'+liste_snapshots[i].status+'</td>'
                      elif liste_snapshots[i].status == u'deleting':
                        snapshotstabelle += '<td bgcolor="#ffcc99" align="center">'+liste_snapshots[i].status+'</td>'
                      else:
                        snapshotstabelle += '<td align="center">'+liste_snapshots[i].status+'</td>'
                      snapshotstabelle += '</tr>'
                      
                      snapshotstabelle += '<tr>'
                      if sprache == "de":
                        snapshotstabelle += '<td colspan="2" align="right"><b>Besitzer:</b></td>'
                      else:
                        snapshotstabelle += '<td colspan="2" align="right"><b>Owner:</b></td>'
                      snapshotstabelle += '<td align="center">'+str(liste_snapshots[i].owner_id)+'</td>'
                      snapshotstabelle += '</tr>'
                      
                      snapshotstabelle += '<tr>'
                      if sprache == "de":
                        snapshotstabelle += '<td colspan="2" align="right"><b>Beschreibung:</b></td>'
                      else:
                        snapshotstabelle += '<td colspan="2" align="right"><b>Description:</b></td>'
                      snapshotstabelle += '<td align="center">'+str(liste_snapshots[i].description)+'</td>'
                      snapshotstabelle += '</tr>'
                      
                      snapshotstabelle += '<tr>'
                      if sprache == "de":
                        snapshotstabelle += '<td colspan="2" align="right"><b>Datum:</b></td>'
                      else:
                        snapshotstabelle += '<td colspan="2" align="right"><b>Start Time:</b></td>'
                      snapshotstabelle += '<td align="center">'
                      # Den ISO8601 Zeitstring umwandeln, damit es besser aussieht.
                      datum_der_erzeugung = parse(liste_snapshots[i].start_time)                      
                      snapshotstabelle += str(datum_der_erzeugung.strftime("%Y-%m-%d  %H:%M:%S"))
                      snapshotstabelle += '</td>'
                      snapshotstabelle += '</tr>'
                      
                      snapshotstabelle += '<tr>'
                      if sprache == "de":
                        snapshotstabelle += '<td colspan="2" align="right"><b>Fortschritt:</b></td>'
                      else:
                        snapshotstabelle += '<td colspan="2" align="right"><b>Progress:</b></td>'
                      snapshotstabelle += '<td align="center">'+str(liste_snapshots[i].progress)+'</td>'
                      snapshotstabelle += '</tr>'
                  snapshotstabelle += '</table>'     
                else:
                  # Not the mobile version 
                  snapshotstabelle = ''
                  snapshotstabelle += '<table border="0" cellspacing="0" cellpadding="5">'
                 
                  counter = 0
                  for i in range(laenge_liste_snapshots):
                    
                      if counter > 0:
                          snapshotstabelle += '<tr><td colspan="4">&nbsp;</td></tr>'
                      counter += 1
                      
                      snapshotstabelle += '<tr>'
                      snapshotstabelle += '<td align="left" bgcolor="#D4D4D4">'
                      snapshotstabelle += '<a href="/snapshotsentfernen?snapshot='
                      snapshotstabelle += liste_snapshots[i].id
                      snapshotstabelle += "&amp;mobile="
                      snapshotstabelle += str(mobile)
                      snapshotstabelle += "&amp;ami=all"
                      if sprache == "de":
                        snapshotstabelle += '" title="Snapshot l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Snapshot l&ouml;schen"></a>'
                      else:
                        snapshotstabelle += '" title="erase snapshot"><img src="bilder/delete.png" width="16" height="16" border="0" alt="snapshot volume"></a>'
                      snapshotstabelle += '</td>'

                      snapshotstabelle += '<td colspan="3" bgcolor="#D4D4D4">'
                      snapshotstabelle += '<a href="/volumeaussnapshoterzeugen?snapshot='
                      snapshotstabelle += liste_snapshots[i].id
                      snapshotstabelle += "&amp;mobile="
                      snapshotstabelle += str(mobile)
                      if sprache == "de":
                        snapshotstabelle += '" title="Volume erzeugen"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Volume erzeugen"></a>'
                      else:
                        snapshotstabelle += '" title="create volume"><img src="bilder/plus.png" width="16" height="16" border="0" alt="create volume"></a>'
                      snapshotstabelle += '</td>'

                                          
                      snapshotstabelle += '</tr>'                      
                      snapshotstabelle += '<tr>'
                      
                      snapshotstabelle += '<td align="right" bgcolor="#D4D4D4"><b>ID:</b></td>'
                      snapshotstabelle += '<td align="left">'+liste_snapshots[i].id+'</td>'
                      
                      snapshotstabelle += '<td align="right" bgcolor="#D4D4D4"><b>Status:</b></td>'
                      if liste_snapshots[i].status == u'completed':
                        snapshotstabelle += '<td bgcolor="#c3ddc3" align="left">'+liste_snapshots[i].status+'</td>'
                      elif liste_snapshots[i].status == u'pending':
                        snapshotstabelle += '<td bgcolor="#ffffcc" align="left">'+liste_snapshots[i].status+'</td>'
                      elif liste_snapshots[i].status == u'deleting':
                        snapshotstabelle += '<td bgcolor="#ffcc99" align="left">'+liste_snapshots[i].status+'</td>'
                      else:
                        snapshotstabelle += '<td align="left">'+liste_snapshots[i].status+'</td>'
                        
                      snapshotstabelle += '</tr>'                      
                      snapshotstabelle += '<tr>'
                      
                      if sprache == "de":
                        snapshotstabelle += '<td align="right" bgcolor="#D4D4D4"><b>Gr&ouml;&szlig;e:</b></td>'
                      else:
                        snapshotstabelle += '<td align="right" bgcolor="#D4D4D4"><b>Size:</b></td>'
                      snapshotstabelle += '<td align="left">'+str(liste_snapshots[i].volume_size)+' GB</td>'
                      
                      snapshotstabelle += '<td align="right" bgcolor="#D4D4D4"><b>Volume:</b></td>'
                      snapshotstabelle += '<td align="left">'+liste_snapshots[i].volume_id+'</td>'
                      
                      snapshotstabelle += '</tr>'
                      snapshotstabelle += '<tr>'

                      if sprache == "de":
                        snapshotstabelle += '<td align="right" bgcolor="#D4D4D4"><b>Fortschritt:</b></td>'
                      else:
                        snapshotstabelle += '<td align="right" bgcolor="#D4D4D4"><b>Progress:</b></td>'
                      snapshotstabelle += '<td align="left">'+str(liste_snapshots[i].progress)+'</td>'
                      
                      if sprache == "de":
                        snapshotstabelle += '<td align="right" bgcolor="#D4D4D4"><b>Besitzer:</b></td>'
                      else:
                        snapshotstabelle += '<td align="right" bgcolor="#D4D4D4"><b>Owner:</b></td>'
                      snapshotstabelle += '<td align="left">'+str(liste_snapshots[i].owner_id)+'</td>'
                      
                      snapshotstabelle += '</tr>'                      
                      snapshotstabelle += '<tr>'
                      
                      if sprache == "de":
                        snapshotstabelle += '<td align="right" bgcolor="#D4D4D4"><b>Datum:</b></td>'
                      else:
                        snapshotstabelle += '<td align="right" bgcolor="#D4D4D4"><b>Start Time:</b></td>'
                      snapshotstabelle += '<td colspan="3" align="left">'
                      # Den ISO8601 Zeitstring umwandeln, damit es besser aussieht.
                      datum_der_erzeugung = parse(liste_snapshots[i].start_time)                      
                      snapshotstabelle += str(datum_der_erzeugung.strftime("%Y-%m-%d  %H:%M:%S"))
                      snapshotstabelle += '</td>'
                      
                      snapshotstabelle += '</tr>'
                      snapshotstabelle += '<tr>'

                      if sprache == "de":
                        snapshotstabelle += '<td align="right" bgcolor="#D4D4D4"><b>Beschreibung:</b></td>'
                      else:
                        snapshotstabelle += '<td align="right" bgcolor="#D4D4D4"><b>Description:</b></td>'
                        
                      if liste_snapshots[i].description == "":
                        snapshotstabelle += '<td align="left">---</td>'
                        snapshotstabelle += '<td align="left" colspan="2">&nbsp;</td>'
                      else:
                        snapshotstabelle += '<td colspan="3" align="left">'+str(liste_snapshots[i].description)+'</td>'
                      snapshotstabelle += '</tr>'

                  snapshotstabelle += '</table>'     
  
  
            if regionname == "Amazon":
                if sprache == "de":
                  ansicht_amazon_button = ''
                  ansicht_amazon_button += '<form action="/snapshots" method="get">\n'
                  ansicht_amazon_button += '<input type="hidden" name="mobile" value="'+str(mobile)+'">\n'
                  ansicht_amazon_button += '<input type="submit" value="Nur eigene Snapshots anzeigen">\n'
                  ansicht_amazon_button += '</form>\n'
                  ansicht_amazon_button += '<p>&nbsp;</p>\n'
                else:
                  ansicht_amazon_button = ''
                  ansicht_amazon_button += '<form action="/snapshots" method="get">\n'
                  ansicht_amazon_button += '<input type="hidden" name="mobile" value="'+str(mobile)+'">\n'
                  ansicht_amazon_button += '<input type="submit" value="show only your snapshots">\n'
                  ansicht_amazon_button += '</form>\n'
                  ansicht_amazon_button += '<p>&nbsp;</p>\n'
            else:  
                ansicht_amazon_button = ""
  
            path = '&amp;path=snapshots_amazon_all&amp;mobile='+mobile
  
            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'snapshotstabelle': snapshotstabelle,
            'zonen_liste': zonen_liste,
            'input_error_message': input_error_message,
            'ansicht_amazon_button': ansicht_amazon_button,
            'path': path,
            }
  
            if mobile == "true":
                path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "snapshots.html")
            else:
                path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "snapshots.html")
            self.response.out.write(template.render(path,template_values))
  
            
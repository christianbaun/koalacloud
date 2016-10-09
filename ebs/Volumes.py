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

class Volumes(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # Eventuell vorhande Fehlermeldung holen
        message = self.request.get('message')
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
          #url = users.create_logout_url(self.request.uri)
          url_linktext = 'Logout'

          conn_region, regionname = login(username)
          zone_amazon = amazon_region(username)

          zonen_liste = zonen_liste_funktion(username,sprache,mobile)

          # It is Google Storage and not am IaaS  
          if regionname == "GoogleStorage":
            
            path = '&amp;path=volumes&amp;mobile='+mobile
            
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
            if message in ("15", "22", "23", "24", "27"):
              # wird sie hier, in der Hilfsfunktion grün formatiert
              input_error_message = format_error_message_green(input_error_message)
            # Ansonsten wird die Nachricht rot formatiert
            elif message in ("8", "10", "16", "17", "18", "19", "20", "21", "25", "26"):
              input_error_message = format_error_message_red(input_error_message)
            else:
              input_error_message = ""
  
            #!!!!!!! (Anfang)
            try:
              # Liste mit den Zonen
              liste_zonen = conn_region.get_all_zones()
            except EC2ResponseError:
              # Wenn es nicht klappt...
              if sprache == "de":
                zonentabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
              else:
                zonentabelle = '<font color="red">An error occured</font>'
              laenge_liste_zonen = 0
            except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              if sprache == "de":
                zonentabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
              else:
                zonentabelle = '<font color="red">A timeout error occured</font>'
              laenge_liste_zonen = 0
            else:
              # Wenn es geklappt hat...
              # Anzahl der Elemente in der Liste
              laenge_liste_zonen = len(liste_zonen)
            #!!!!!!! (Ende) 
                        
  #          # Liste mit den Zonen
  #          liste_zonen = conn_region.get_all_zones()
  #          # Anzahl der Elemente in der Liste
  #          laenge_liste_zonen = len(liste_zonen)
  
            # Hier wird die Auswahlliste der Zonen erzeugt
            # Diese Auswahlliste ist zum Erzeugen neuer Volumes notwendig
            zonen_in_der_region = ''
            if laenge_liste_zonen == 0:
                zonen_in_der_region = zonen_in_der_region + "<option>&nbsp;</option>"
            else:
                for i in range(laenge_liste_zonen):
                    zonen_in_der_region = zonen_in_der_region + "<option>"
                    zonen_in_der_region = zonen_in_der_region + liste_zonen[i].name
                    zonen_in_der_region = zonen_in_der_region + "</option>"
  
            try:
              # Liste mit den Volumes
              liste_volumes = conn_region.get_all_volumes()
            except EC2ResponseError:
              # Wenn es nicht klappt...
              if sprache == "de":
                volumestabelle = '<font color="red">Es ist zu einem Fehler gekommen</font>'
              else:
                volumestabelle = '<font color="red">An error occured</font>'
              # Wenn diese Zeile nicht da ist, kommt es später zu einem Fehler!
              laenge_liste_volumes = 0
            except DownloadError:
              # Diese Exception hilft gegen diese beiden Fehler:
              # DownloadError: ApplicationError: 2 timed out
              # DownloadError: ApplicationError: 5
              if sprache == "de":
                volumestabelle = '<font color="red">Es ist zu einem Timeout-Fehler gekommen</font>'
              else:
                volumestabelle = '<font color="red">A timeout error occured</font>'
              # Wenn diese Zeile nicht da ist, kommt es später zu einem Fehler!
              laenge_liste_volumes = 0
            else:
              # Wenn es geklappt hat...
              # Anzahl der Volumes in der Liste
              laenge_liste_volumes = len(liste_volumes)
  
  
              if laenge_liste_volumes == 0:
                # Wenn es noch keine Volumes in der Region gibt...
                if sprache == "de":
                  volumestabelle = 'Sie haben keine Volumen in dieser Region.'
                else:
                  volumestabelle = 'You have no volumes inside this region.'
              else: 
                # Wenn es schon Volumes in der Region gibt...
                
                if mobile == "true":
                  # Mobile version of the table
                  volumestabelle = ''
                  volumestabelle = volumestabelle + '<table border="0" cellspacing="0" cellpadding="5">'

                  counter = 0
                  for i in range(laenge_liste_volumes):
                      if counter > 0:
                          volumestabelle += '<tr><td colspan="3">&nbsp;</td></tr>'
                      counter += 1
                    
                      volumestabelle += '<tr>'
                      volumestabelle += '<td>'
                      # Nur wenn der Zustand des Volumes "available" ist, darf  man es löschen.
                      # Darum wird hier überprüft, ob der Wert von "attach_data.status" gesetzt ist.
                      # Wenn er nicht gesetzt ist, kann/darf das Volume gelöscht werden.
                      if liste_volumes[i].attach_data.status == None:
                        volumestabelle = volumestabelle + '<a href="/volumeentfernen?volume='
                        volumestabelle = volumestabelle + liste_volumes[i].id
                        volumestabelle = volumestabelle + "&amp;mobile="
                        volumestabelle = volumestabelle + str(mobile)
                        if sprache == "de":
                          volumestabelle = volumestabelle + '" title="Volume l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Volume l&ouml;schen"></a>'
                        else:
                          volumestabelle = volumestabelle + '" title="erase volume"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase volume"></a>'
                      else:
                      # Das Volume kann/darf nicht gelöscht werden.
                        volumestabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0">'
                      volumestabelle += '</td>'
    
                      volumestabelle = volumestabelle + '<td align="center">'
                      volumestabelle = volumestabelle + '<a href="/snapshoterzeugen?volume='
                      volumestabelle = volumestabelle + liste_volumes[i].id
                      volumestabelle = volumestabelle + "&amp;mobile="
                      volumestabelle = volumestabelle + str(mobile)
                      if sprache == "de":
                        volumestabelle = volumestabelle + '" title="Snapshot erzeugen"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Snapshot erzeugen"></a>'
                      else:
                        volumestabelle = volumestabelle + '" title="create snapshot"><img src="bilder/plus.png" width="16" height="16" border="0" alt="create snapshot"></a>'
                      volumestabelle = volumestabelle + '</td>'
    
                      if liste_volumes[i].attach_data.status == None:
                        volumestabelle = volumestabelle + '<td align="center">'
                        volumestabelle = volumestabelle + '<a href="/volumeanhaengen?volume='
                        volumestabelle = volumestabelle + liste_volumes[i].id
                        volumestabelle = volumestabelle + "&amp;zone="
                        volumestabelle = volumestabelle + str(liste_volumes[i].zone)
                        volumestabelle = volumestabelle + "&amp;mobile="
                        volumestabelle = volumestabelle + str(mobile)
                        if sprache == "de":
                          volumestabelle = volumestabelle + '" title="Volume anh&auml;ngen">'
                          volumestabelle = volumestabelle + '<img src="bilder/attach2.png" width="16" height="16" border="0" alt="Volume anh&auml;ngen"></a>'
                        else:
                          volumestabelle = volumestabelle + '" title="attach volume">'
                          volumestabelle = volumestabelle + '<img src="bilder/attach2.png" width="16" height="16" border="0" alt="attach volume"></a>'
                      elif liste_volumes[i].attach_data.status == u'attaching':
                        volumestabelle += '<td align="center">attaching</td>'

                      elif liste_volumes[i].attach_data.status == u'deleting':
                        volumestabelle += '<td align="center">deleting</td>'

                      elif liste_volumes[i].attach_data.status == u'busy':
                        volumestabelle += '<td align="center">busy</td>'

                      elif liste_volumes[i].attach_data.status == u'attached':
                        volumestabelle += '<td align="center">'
                        volumestabelle += '<a href="/volumeloesen?volume='
                        volumestabelle += liste_volumes[i].id
                        volumestabelle = volumestabelle + "&amp;mobile="
                        volumestabelle = volumestabelle + str(mobile)
                        if sprache == "de":
                          volumestabelle += '" title="Volume l&ouml;sen">'
                          volumestabelle += '<img src="bilder/detach2.png" width="16" height="16" border="0" alt="Volume l&ouml;sen"></a>'
                        else:
                          volumestabelle += '" title="detach volume">'
                          volumestabelle += '<img src="bilder/detach2.png" width="16" height="16" border="0" alt="detach volume"></a>'
                        volumestabelle += '</td>'
                      else:
                        volumestabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0">'                  
                      
                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'
                      
                      volumestabelle += '<td colspan="2" align="right"><b>ID:</b></td>'
                      volumestabelle += '<td align="center">'+str(liste_volumes[i].id)+'</td>'
                      
                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'
                      
                      if sprache == "de":
                        volumestabelle += '<td colspan="2" align="right"><b>Gr&ouml;&szlig;e:</b></td>'
                      else:
                        volumestabelle += '<td colspan="2" align="right"><b>Size:</b></td>'
                      volumestabelle += '<td align="center">'+str(liste_volumes[i].size)+' GB</td>'
                      
                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'
                         
                      volumestabelle += '<td colspan="2" align="right"><b>Status:</b></td>'
                      if liste_volumes[i].status == u'available':
                        volumestabelle += '<td bgcolor="#c3ddc3" align="center">'+liste_volumes[i].status+'</td>'
                      elif liste_volumes[i].status == u'in-use':
                        volumestabelle += '<td bgcolor="#ffffcc" align="center">'+liste_volumes[i].status+'</td>'
                      elif liste_volumes[i].status == u'deleting':
                        volumestabelle += '<td bgcolor="#ffcc99" align="center">'+liste_volumes[i].status+'</td>'
                      else:
                        volumestabelle += '<td align="center">'+liste_volumes[i].status+'</td>'

                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'
                      
                      volumestabelle += '<td colspan="2" align="right"><b>Zone:</b></td>'
                      volumestabelle += '<td align="center">'+str(liste_volumes[i].zone)+'</td>'
                      
                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'
                      
                      if sprache == "de":
                        volumestabelle += '<td colspan="2" align="right"><b>Datum:</b></td>'
                      else:
                        volumestabelle += '<td colspan="2" align="right"><b>Creation Date:</b></td>'
                      volumestabelle += '<td align="center">'
                      # Den ISO8601 Zeitstring umwandeln, damit es besser aussieht.
                      datum_der_erzeugung = parse(liste_volumes[i].create_time)
                      volumestabelle += str(datum_der_erzeugung.strftime("%Y-%m-%d  %H:%M:%S"))
                      #volumestabelle = volumestabelle + str(datum_der_erzeugung)
                      #volumestabelle = volumestabelle + str(liste_volumes[i].create_time)
                      volumestabelle += '</td>'
                      
                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'
                      
                      volumestabelle += '<td colspan="2" align="right"><b>Snapshot:</b></td>'
                      if liste_volumes[i].snapshot_id == "":
                        volumestabelle += '<td align="center">---</td>'
                      else:
                        volumestabelle += '<td align="center">'+str(liste_volumes[i].snapshot_id)+'</td>'
                      
                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'
                               
                      if sprache == "de":
                        volumestabelle += '<td colspan="2" align="right"><b>Ger&auml;t:</b></td>'
                      else:
                        volumestabelle += '<td colspan="2" align="right"><b>Device:</b></td>'            
                      if liste_volumes[i].attach_data.device == None:
                        volumestabelle += '<td align="center">---</td>'
                      else:
                        volumestabelle += '<td align="center">'+str(liste_volumes[i].attach_data.device)+'</td>'
                      
                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'

                      if sprache == "de":
                        volumestabelle += '<td colspan="2" align="right"><b>Verkn&uuml;pfung:</b></td>'
                      else:
                        volumestabelle += '<td colspan="2" align="right"><b>Attach Date:</b></td>'
                      if liste_volumes[i].attach_data.attach_time == None:
                        volumestabelle += '<td align="center">---</td>'
                      else:
                        volumestabelle = volumestabelle + '<td>'
                        # Den ISO8601 Zeitstring umwandeln, damit es besser aussieht.
                        datum_des_anhaengens = parse(liste_volumes[i].attach_data.attach_time)
                        volumestabelle = volumestabelle + str(datum_des_anhaengens.strftime("%Y-%m-%d  %H:%M:%S"))
                        #volumestabelle = volumestabelle + str(liste_volumes[i].attach_data.attach_time)
                        volumestabelle = volumestabelle + '</td>'

                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'

                      if sprache == "de":
                        volumestabelle += '<td colspan="2" align="right"><b>Instanz:</b></td>'
                      else:
                        volumestabelle += '<td colspan="2" align="right"><b>Instance:</b></td>'
                      if liste_volumes[i].attach_data.instance_id == None:
                        volumestabelle += '<td align="center">---</td>'
                      else:
                        volumestabelle += '<td align="center">'+str(liste_volumes[i].attach_data.instance_id)+'</td>'

                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'

                      if sprache == "de":
                        volumestabelle += '<td colspan="2" align="right"><b>Status:</b></td>'
                      else:
                        volumestabelle += '<td colspan="2" align="right"><b>Attach Status:</b></td>'
                      if liste_volumes[i].attach_data.status == None:
                        volumestabelle += '<td align="center">---</td>'
                      elif liste_volumes[i].attach_data.status == u'attached':
                        volumestabelle += '<td bgcolor="#c3ddc3" align="center">'+str(liste_volumes[i].attach_data.status)+'</td>'
                      elif liste_volumes[i].attach_data.status == u'busy':
                        volumestabelle += '<td bgcolor="#ffcc99" align="center">'+str(liste_volumes[i].attach_data.status)+'</td>'
                      else:
                        volumestabelle += '<td align="center">'+str(liste_volumes[i].attach_data.status)+'</td>'
                      volumestabelle = volumestabelle + '</tr>'
                  volumestabelle = volumestabelle + '</table>'
                  
                else:
                  # Not the mobile version

                  volumestabelle = ''
                  volumestabelle = volumestabelle + '<table border="0" cellspacing="0" cellpadding="5">'

                  counter = 0
                  for i in range(laenge_liste_volumes):
                      if counter > 0:
                          volumestabelle += '<tr><td colspan="5">&nbsp;</td></tr>'
                      counter += 1
                    
                      volumestabelle += '<tr>'
                      volumestabelle += '<td bgcolor="#D4D4D4">'
                      # Nur wenn der Zustand des Volumes "available" ist, darf  man es löschen.
                      # Darum wird hier überprüft, ob der Wert von "attach_data.status" gesetzt ist.
                      # Wenn er nicht gesetzt ist, kann/darf das Volume gelöscht werden.
                      if liste_volumes[i].attach_data.status == None:
                        volumestabelle = volumestabelle + '<a href="/volumeentfernen?volume='
                        volumestabelle = volumestabelle + liste_volumes[i].id
                        volumestabelle = volumestabelle + "&amp;mobile="
                        volumestabelle = volumestabelle + str(mobile)
                        if sprache == "de":
                          volumestabelle = volumestabelle + '" title="Volume l&ouml;schen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Volume l&ouml;schen"></a>'
                        else:
                          volumestabelle = volumestabelle + '" title="erase volume"><img src="bilder/delete.png" width="16" height="16" border="0" alt="erase volume"></a>'
                      else:
                      # Das Volume kann/darf nicht gelöscht werden.
                        volumestabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0">'
                      volumestabelle += '</td>'
    
                      volumestabelle += '<td align="center" bgcolor="#D4D4D4">'
                      volumestabelle += '<a href="/snapshoterzeugen?volume='
                      volumestabelle += liste_volumes[i].id
                      volumestabelle += "&amp;mobile="
                      volumestabelle += str(mobile)
                      if sprache == "de":
                        volumestabelle += '" title="Snapshot erzeugen"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Snapshot erzeugen"></a>'
                      else:
                        volumestabelle += '" title="create snapshot"><img src="bilder/plus.png" width="16" height="16" border="0" alt="create snapshot"></a>'
                      volumestabelle += '</td>'
    
                      if liste_volumes[i].attach_data.status == None:
                        volumestabelle += '<td colspan="3" align="left" bgcolor="#D4D4D4">'
                        volumestabelle += '<a href="/volumeanhaengen?volume='
                        volumestabelle += liste_volumes[i].id
                        volumestabelle += "&amp;zone="
                        volumestabelle += str(liste_volumes[i].zone)
                        volumestabelle += "&amp;mobile="
                        volumestabelle += str(mobile)
                        if sprache == "de":
                          volumestabelle += '" title="Volume anh&auml;ngen">'
                          volumestabelle += '<img src="bilder/attach2.png" width="16" height="16" border="0" alt="Volume anh&auml;ngen"></a>'
                        else:
                          volumestabelle += '" title="attach volume">'
                          volumestabelle += '<img src="bilder/attach2.png" width="16" height="16" border="0" alt="attach volume"></a>'
                      elif liste_volumes[i].attach_data.status == u'attaching':
                        volumestabelle += '<td colspan="3" align="left" bgcolor="#D4D4D4">attaching</td>'

                      elif liste_volumes[i].attach_data.status == u'deleting':
                        volumestabelle += '<td colspan="3" align="left" bgcolor="#D4D4D4">deleting</td>'

                      elif liste_volumes[i].attach_data.status == u'busy':
                        volumestabelle += '<td colspan="3" align="left" bgcolor="#D4D4D4">busy</td>'

                      elif liste_volumes[i].attach_data.status == u'attached':
                        volumestabelle += '<td colspan="3" align="left" bgcolor="#D4D4D4">'
                        volumestabelle += '<a href="/volumeloesen?volume='
                        volumestabelle += liste_volumes[i].id
                        volumestabelle += "&amp;mobile="
                        volumestabelle += str(mobile)
                        if sprache == "de":
                          volumestabelle += '" title="Volume l&ouml;sen">'
                          volumestabelle += '<img src="bilder/detach2.png" width="16" height="16" border="0" alt="Volume l&ouml;sen"></a>'
                        else:
                          volumestabelle += '" title="detach volume">'
                          volumestabelle += '<img src="bilder/detach2.png" width="16" height="16" border="0" alt="detach volume"></a>'
                        volumestabelle += '</td>'
                      else:
                        volumestabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0">'                  

                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'
                      
                      volumestabelle += '<td align="right" colspan="2" bgcolor="#D4D4D4"><b>ID:</b></td>'  
                      volumestabelle += '<td align="left">'+str(liste_volumes[i].id)+'</td>'

                      volumestabelle += '<td align="right" bgcolor="#D4D4D4"><b>Status:</b></td>'
                      if liste_volumes[i].status == u'available':
                        volumestabelle += '<td bgcolor="#c3ddc3" align="left">'+liste_volumes[i].status+'</td>'
                      elif liste_volumes[i].status == u'in-use':
                        volumestabelle += '<td bgcolor="#ffffcc" align="left">'+liste_volumes[i].status+'</td>'
                      elif liste_volumes[i].status == u'deleting':
                        volumestabelle += '<td bgcolor="#ffcc99" align="left">'+liste_volumes[i].status+'</td>'
                      else:
                        volumestabelle += '<td align="left">'+liste_volumes[i].status+'</td>'

                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'
                      
                      if sprache == "de":
                        volumestabelle += '<td colspan="2" align="right" bgcolor="#D4D4D4"><b>Gr&ouml;&szlig;e:</b></td>'
                      else:
                        volumestabelle += '<td colspan="2" align="right" bgcolor="#D4D4D4"><b>Size:</b></td>'
                      volumestabelle += '<td align="left">'+str(liste_volumes[i].size)+' GB</td>'
                      
                      volumestabelle += '<td align="right" bgcolor="#D4D4D4"><b>Zone:</b></td>'
                      volumestabelle += '<td align="left">'+str(liste_volumes[i].zone)+'</td>'
                      
                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'
                      
                      if sprache == "de":
                        volumestabelle += '<td colspan="2" align="right" bgcolor="#D4D4D4"><b>Datum:</b></td>'
                      else:
                        volumestabelle += '<td colspan="2" align="right" bgcolor="#D4D4D4"><b>Creation Date:</b></td>'
                      volumestabelle += '<td align="left">'
                      # Den ISO8601 Zeitstring umwandeln, damit es besser aussieht.
                      datum_der_erzeugung = parse(liste_volumes[i].create_time)
                      volumestabelle += str(datum_der_erzeugung.strftime("%Y-%m-%d  %H:%M:%S"))
                      #volumestabelle = volumestabelle + str(datum_der_erzeugung)
                      #volumestabelle = volumestabelle + str(liste_volumes[i].create_time)
                      volumestabelle += '</td>'

                      
                      volumestabelle += '<td align="right" bgcolor="#D4D4D4"><b>Snapshot:</b></td>'
                      if liste_volumes[i].snapshot_id == "":
                        volumestabelle += '<td align="left">---</td>'
                      else:
                        volumestabelle += '<td>'+str(liste_volumes[i].snapshot_id)+'</td>'

                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'

                      if sprache == "de":
                        volumestabelle += '<td colspan="2" align="right" bgcolor="#D4D4D4"><b>Instanz:</b></td>'
                      else:
                        volumestabelle += '<td colspan="2" align="right" bgcolor="#D4D4D4"><b>Instance:</b></td>'
                      if liste_volumes[i].attach_data.instance_id == None:
                        volumestabelle += '<td align="left">---</td>'
                      else:
                        volumestabelle += '<td align="left">'+str(liste_volumes[i].attach_data.instance_id)+'</td>'

                      if sprache == "de":
                        volumestabelle += '<td align="right" bgcolor="#D4D4D4"><b>Status:</b></td>'
                      else:
                        volumestabelle += '<td align="right" bgcolor="#D4D4D4"><b>Attach Status:</b></td>'
                      if liste_volumes[i].attach_data.status == None:
                        volumestabelle += '<td align="left">---</td>'
                      elif liste_volumes[i].attach_data.status == u'attached':
                        volumestabelle += '<td bgcolor="#c3ddc3" align="left">'+str(liste_volumes[i].attach_data.status)+'</td>'
                      elif liste_volumes[i].attach_data.status == u'busy':
                        volumestabelle += '<td bgcolor="#ffcc99" align="left">'+str(liste_volumes[i].attach_data.status)+'</td>'
                      else:
                        volumestabelle += '<td align="left">'+str(liste_volumes[i].attach_data.status)+'</td>'
                        
                      volumestabelle += '</tr>'
                      volumestabelle += '<tr>'

                      if sprache == "de":
                        volumestabelle += '<td colspan="2" align="right" bgcolor="#D4D4D4"><b>Datum:</b></td>'
                      else:
                        volumestabelle += '<td colspan="2" align="right" bgcolor="#D4D4D4"><b>Attach Date:</b></td>'
                      if liste_volumes[i].attach_data.attach_time == None:
                        volumestabelle += '<td align="left">---</td>'
                      else:
                        volumestabelle += '<td align="left">'
                        # Den ISO8601 Zeitstring umwandeln, damit es besser aussieht.
                        datum_des_anhaengens = parse(liste_volumes[i].attach_data.attach_time)
                        volumestabelle += str(datum_des_anhaengens.strftime("%Y-%m-%d  %H:%M:%S"))
                        #volumestabelle += str(liste_volumes[i].attach_data.attach_time)
                        volumestabelle += '</td>'

                      if sprache == "de":
                        volumestabelle += '<td align="right" bgcolor="#D4D4D4"><b>Ger&auml;t:</b></td>'
                      else:
                        volumestabelle += '<td align="right" bgcolor="#D4D4D4"><b>Device:</b></td>'            
                      if liste_volumes[i].attach_data.device == None:
                        volumestabelle += '<td align="left">---</td>'
                      else:
                        volumestabelle += '<td align="left">'+str(liste_volumes[i].attach_data.device)+'</td>'
                                            
                      volumestabelle = volumestabelle + '</tr>'
                  volumestabelle = volumestabelle + '</table>'
                  
  
            if laenge_liste_volumes >= 1:
              alle_volumes_loeschen_button = '<p>&nbsp;</p>\n'
              alle_volumes_loeschen_button += '<table border="0" cellspacing="0" cellpadding="5">\n'
              alle_volumes_loeschen_button += '<tr>\n'
              alle_volumes_loeschen_button += '<td align="center">\n'
              alle_volumes_loeschen_button += '<form action="/alle_volumes_loeschen" method="get">\n'
              alle_volumes_loeschen_button += '<input type="hidden" name="mobile" value="'+mobile+'">'
              if sprache == "de":
                alle_volumes_loeschen_button += '<input type="submit" value="Alle EBS Volumen l&ouml;schen">\n'
              else:
                alle_volumes_loeschen_button += '<input type="submit" value="erase all EBS volumes">\n'
              alle_volumes_loeschen_button += '</form>\n'
              alle_volumes_loeschen_button += '</td>\n'
              alle_volumes_loeschen_button += '</tr>\n'
              alle_volumes_loeschen_button += '</table>\n'
            else:
              alle_volumes_loeschen_button = '<p>&nbsp;</p>\n'
  
            path = '&amp;path=volumes&amp;mobile='+mobile
  
            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'volumestabelle': volumestabelle,
            'zonen_in_der_region': zonen_in_der_region,
            'input_error_message': input_error_message,
            'zonen_liste': zonen_liste,
            'alle_volumes_loeschen_button': alle_volumes_loeschen_button,
            'mobile': mobile,
            'path': path,
            }
  
            if mobile == "true":
                path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "volumes.html")
            else:  
                path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "volumes.html")
            self.response.out.write(template.render(path,template_values))

          
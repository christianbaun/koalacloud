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

class Instanzen(webapp.RequestHandler):
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
        # Eventuell vorhande Fehlernachricht holen
        fehlernachricht = self.request.get('fehlernachricht') 

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
            
            path = '&amp;path=instanzen&amp;mobile='+mobile
            
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
            

            
          # It is not Google Storage or Host Europe Cloud Storage => it is an IaaS
          else:          

            if sprache != "de":
              sprache = "en"
  
            input_error_message = error_messages.get(message, {}).get(sprache)
  
            # Wenn keine Fehlermeldung gefunden wird, ist das Ergebnis "None"
            if input_error_message == None:
              input_error_message = ""
  
            # Wenn die Nachricht grün formatiert werden soll...
            if message in ("73", "77", "79", "81", "123", "125"):
              # wird sie hier, in der Hilfsfunktion grün formatiert
              input_error_message = format_error_message_green(input_error_message)
            # Ansonsten wird die Nachricht rot formatiert
            elif message in ("8", "9", "10", "74", "75", "76", "78", "80", "82", "122", "124", "126"):
              input_error_message = format_error_message_red(input_error_message)
              if fehlernachricht != None:
                input_error_message += format_error_message_red(fehlernachricht)
            else:
              input_error_message = ""
  
            # Herausfinden, was für eine Infrastruktur wir verwenden.
            # Ist es Amazon, Nimbus, OpenNebula oder Eucalyptus? 
            # Die Ergebnisse des SELECT durchlaufen (ist nur eins) 
            # for result in results:
            #   aktueller_zugangstyp = result.zugangstyp
              
            # Zur Kontrolle, die Art der Infrastruktur ausgeben
            # self.response.out.write(aktueller_zugangstyp)
  
  
            try:
              liste_reservations = conn_region.get_all_instances()
            except EC2ResponseError:
              # Wenn es nicht klappt...
              if sprache == "de":
                instanzentabelle = '<font color="red">Es ist zu einem Fehler gekommen</font> <p>&nbsp;</p>'
              else:
                instanzentabelle = '<font color="red">An error occured</font> <p>&nbsp;</p>'
              # Wenn diese Zeile nicht da ist, kommt es später zu einem Fehler!
              laenge_liste_reservations = 0
            except DownloadError:
              if sprache == "de":
                instanzentabelle = '<font color="red">Es ist zu einem Timeout gekommen</font> <p>&nbsp;</p>'
              else:
                instanzentabelle = '<font color="red">A timeout error occured</font> <p>&nbsp;</p>'
              # Wenn diese Zeile nicht da ist, kommt es später zu einem Fehler!
              laenge_liste_reservations = 0
            else:
              # Wenn es geklappt hat...
              # Anzahl der Elemente in der Liste
              laenge_liste_reservations = len(liste_reservations)
  
              if laenge_liste_reservations == 0:
                if sprache == "de":
                  instanzentabelle = 'Sie haben keine Instanzen in dieser Region.'
                else:
                  instanzentabelle = 'You have no instances inside this region.'
              else:
                            
                if mobile == "true":
                  # This is the mobile version

                  instanzentabelle = ''
                  instanzentabelle += '<table border="0" cellspacing="0" cellpadding="5" width="300">'

                  counter = 0
                  for i in liste_reservations:        
                    for x in i.instances:
                      if counter > 0:
                          instanzentabelle += '<tr><td colspan="7">&nbsp;</td></tr>'
                      counter += 1
                      
                      instanzentabelle += '<tr>'
                      
                      # Terminate instance
                      instanzentabelle += '<td>'
                      if sprache == "de":
                        instanzentabelle += '<a href="/instanzterminate?id='
                        instanzentabelle += x.id
                        instanzentabelle += "&amp;mobile="
                        instanzentabelle += str(mobile)                      
                        instanzentabelle += '"title="Instanz entfernen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Instanz entfernen"></a>'
                      else:
                        instanzentabelle += '<a href="/instanzterminate?id='
                        instanzentabelle += x.id
                        instanzentabelle += "&amp;mobile="
                        instanzentabelle += str(mobile)       
                        instanzentabelle += '"title="terminate instance"><img src="bilder/delete.png" width="16" height="16" border="0" alt="terminate instance"></a>'
                      instanzentabelle += '</td>'

                      # Die Icons der Betriebssysteme nur unter Amazon
                      #if regionname == "Amazon":
                      # Hier kommt die Spalte mit den Icons der Betriebssysteme
                      instanzentabelle += '<td align="center">'                  
                      
                      try:
                        image = conn_region.get_image(str(x.image_id))
                      except EC2ResponseError:
                        instanzentabelle += '&nbsp;'
                      except DownloadError:
                        # Diese Exception hilft gegen diese beiden Fehler:
                        # DownloadError: ApplicationError: 2 timed out
                        # DownloadError: ApplicationError: 5
                        instanzentabelle += '&nbsp;'
                      else:
    
                        if image == None:
                          # Das hier kommt, wenn das Image der laufenden Instanz nicht mehr existiert!
                          instanzentabelle += '<img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Linux">'
                        else:
                          beschreibung_in_kleinbuchstaben = image.location.lower()
                          if beschreibung_in_kleinbuchstaben.find('fedora') != -1:
                            instanzentabelle += '<img src="bilder/fedora_icon_48.png" width="24" height="24" border="0" alt="Fedora">'
                          elif beschreibung_in_kleinbuchstaben.find('ubuntu') != -1:
                            instanzentabelle += '<img src="bilder/ubuntu_icon_48.png" width="24" height="24" border="0" alt="Ubuntu">'
                          elif beschreibung_in_kleinbuchstaben.find('debian') != -1:
                            instanzentabelle += '<img src="bilder/debian_icon_48.png" width="24" height="24" border="0" alt="Debian">'
                          elif beschreibung_in_kleinbuchstaben.find('gentoo') != -1:
                            instanzentabelle += '<img src="bilder/gentoo_icon_48.png" width="24" height="24" border="0" alt="Gentoo">'
                          elif beschreibung_in_kleinbuchstaben.find('suse') != -1:
                            instanzentabelle += '<img src="bilder/suse_icon_48.png" width="24" height="24" border="0" alt="SUSE">'
                          elif beschreibung_in_kleinbuchstaben.find('centos') != -1:
                            instanzentabelle += '<img src="bilder/centos_icon_48.png" width="24" height="24" border="0" alt="CentOS">'
                          elif beschreibung_in_kleinbuchstaben.find('redhat') != -1:
                            instanzentabelle += '<img src="bilder/redhat_icon_48.png" width="24" height="24" border="0" alt="RedHat">'
                          elif beschreibung_in_kleinbuchstaben.find('windows') != -1:
                            instanzentabelle += '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                          elif beschreibung_in_kleinbuchstaben.find('opensolaris') != -1:
                            instanzentabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                          elif beschreibung_in_kleinbuchstaben.find('solaris') != -1:
                            instanzentabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                          elif beschreibung_in_kleinbuchstaben.find('osol') != -1:
                            instanzentabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                          else:
                            instanzentabelle += '<img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Linux">'
                          instanzentabelle += '</td>'
                        #else:
                          ## Das hier wird bei Eucalyptus gemacht
                          #instanzentabelle += '<td><img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Linux"></td>'

                      # Stop instance
                      instanzentabelle += '<td align="center">'
                      if x.root_device_type == 'instance-store': 
                        if x.state == u'running': 
                          fehlermeldung = "122"
                          if sprache == "de":
                            instanzentabelle += '<a href="/instanzen?message='
                            instanzentabelle += fehlermeldung
                            instanzentabelle += "&amp;mobile="
                            instanzentabelle += str(mobile)       
                            instanzentabelle += '"title="Instanz beenden"><img src="bilder/stop.png" width="16" height="16" border="0" alt="Instanz beenden"></a>'
                          else:
                            instanzentabelle += '<a href="/instanzen?message='
                            instanzentabelle += fehlermeldung
                            instanzentabelle += "&amp;mobile="
                            instanzentabelle += str(mobile)       
                            instanzentabelle += '"title="stop instance"><img src="bilder/stop.png" width="16" height="16" border="0" alt="stop instance"></a>'
                        else:
                          instanzentabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0" alt="">'
                      else:
                        if x.state == u'running': 
                          if sprache == "de":
                            instanzentabelle += '<a href="/instanzbeenden?id='
                            instanzentabelle += x.id
                            instanzentabelle += "&amp;mobile="
                            instanzentabelle += str(mobile)       
                            instanzentabelle += '"title="Instanz beenden"><img src="bilder/stop.png" width="16" height="16" border="0" alt="Instanz beenden"></a>'
                          else:
                            instanzentabelle += '<a href="/instanzbeenden?id='
                            instanzentabelle += x.id
                            instanzentabelle += "&amp;mobile="
                            instanzentabelle += str(mobile)       
                            instanzentabelle += '"title="stop instance"><img src="bilder/stop.png" width="16" height="16" border="0" alt="stop instance"></a>'
                        elif x.state == u'stopped':
                          if sprache == "de":
                            instanzentabelle += '<a href="/instanzstarten?id='
                            instanzentabelle += x.id
                            instanzentabelle += "&amp;mobile="
                            instanzentabelle += str(mobile)    
                            instanzentabelle += '"title="Instanz starten"><img src="bilder/up.png" width="16" height="16" border="0" alt="Instanz starten"></a>'
                          else:
                            instanzentabelle += '<a href="/instanzstarten?id='
                            instanzentabelle += x.id
                            instanzentabelle += "&amp;mobile="
                            instanzentabelle += str(mobile)    
                            instanzentabelle += '"title="start instance"><img src="bilder/up.png" width="16" height="16" border="0" alt="start instance"></a>'
                        # If the instance status is "stopping", "pending", "shutting-down" oder "terminated"...                                           
                        else:
                          if sprache == "de":
                            instanzentabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0" alt="Die Instanz kann jetzt nicht beendet werden">'
                          else:
                            instanzentabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0" alt="This instance cannot be stopped now">'
                      instanzentabelle += '</td>'
                      
                      # Id of the instance
                      instanzentabelle += '<td align="center">'+str(x.id)+'</td>'

                      
                      # Reboot instance
                      instanzentabelle += '<td align="center">'
                      if x.state == u'running':
                        if sprache == "de":
                          instanzentabelle += '<a href="/instanzreboot?id='
                          instanzentabelle += x.id
                          instanzentabelle += "&amp;mobile="
                          instanzentabelle += str(mobile)    
                          instanzentabelle += '"title="Instanz neustarten"><img src="bilder/gear.png" width="16" height="16" border="0" alt="Instanz neustarten"></a>'
                        else:
                          instanzentabelle += '<a href="/instanzreboot?id='
                          instanzentabelle += x.id
                          instanzentabelle += "&amp;mobile="
                          instanzentabelle += str(mobile)    
                          instanzentabelle += '"title="reboot instance"><img src="bilder/gear.png" width="16" height="16" border="0" alt="reboot instance"></a>'
                      else:
                        instanzentabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0" alt="">'                        
                      instanzentabelle += '</td>'
                      
                      # Console output
                      instanzentabelle += '<td align="center">'
                      if x.state == u'running':
                        if sprache == "de":
                          instanzentabelle += '<a href="/console_output?id='
                          instanzentabelle += x.id
                          instanzentabelle += "&amp;mobile="
                          instanzentabelle += str(mobile)    
                          instanzentabelle += '"title="Konsolenausgabe"><img src="bilder/terminal.png" width="22" height="16" border="0" alt="Konsolenausgabe"></a>'
                        else:
                          instanzentabelle += '<a href="/console_output?id='
                          instanzentabelle += x.id
                          instanzentabelle += "&amp;mobile="
                          instanzentabelle += str(mobile)    
                          instanzentabelle += '"title="console output"><img src="bilder/terminal.png" width="22" height="16" border="0" alt="console output"></a>'
                      else:
                        instanzentabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0" alt="">'                        
                      instanzentabelle += '</td>'
    
                      # Launch more of these
                      instanzentabelle += '<td align="center">'
                      if sprache == "de":
                        instanzentabelle += '<a href="/instanzanlegen?image='
                        instanzentabelle += str(x.image_id)
                        instanzentabelle += "&amp;zone="
                        instanzentabelle += str(x.placement)
                        instanzentabelle += "&amp;key="
                        instanzentabelle += str(x.key_name)
                        # Es ist denkbar, dass der Wert des Kernels "None" ist.
                        # Dann darf man hier nichts angeben!
                        if x.kernel != None:
                          instanzentabelle += "&amp;aki="
                          instanzentabelle += str(x.kernel)
                        # Manchmal ist die Angabe der Ramdisk "None".
                        # Dann darf man hier nichts angeben!
                        if x.ramdisk != None:
                          instanzentabelle += "&amp;ari="
                          instanzentabelle += str(x.ramdisk)
                        instanzentabelle += "&amp;type="
                        instanzentabelle += str(x.instance_type)
                        instanzentabelle += "&amp;gruppe="
                        instanzentabelle += i.groups[0].id
                        instanzentabelle += "&amp;mobile="
                        instanzentabelle += str(mobile)    
                        instanzentabelle += '"title="Eine weitere Instanz mit den gleichen Parametern starten"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Eine weitere Instanz mit den gleichen Parametern starten"></a>'
                      else:
                        instanzentabelle += '<a href="/instanzanlegen?image='
                        instanzentabelle += str(x.image_id)
                        instanzentabelle += "&amp;zone="
                        instanzentabelle += str(x.placement)
                        instanzentabelle += "&amp;key="
                        instanzentabelle += str(x.key_name)
                        # Es ist denkbar, dass der Wert des Kernels "None" ist.
                        # Dann darf man hier nichts angeben!
                        if x.kernel != None:
                          instanzentabelle += "&amp;aki="
                          instanzentabelle += str(x.kernel)
                        # Manchmal ist die Angabe der Ramdisk "None".
                        # Dann darf man hier nichts angeben!
                        if x.ramdisk != None:
                          instanzentabelle += "&amp;ari="
                          instanzentabelle += str(x.ramdisk)
                        instanzentabelle += "&amp;type="
                        instanzentabelle += str(x.instance_type)
                        instanzentabelle += "&amp;gruppe="
                        instanzentabelle += i.groups[0].id
                        instanzentabelle += "&amp;mobile="
                        instanzentabelle += str(mobile)    
                        instanzentabelle += '"title="launch a new instance with the same values"><img src="bilder/plus.png" width="16" height="16" border="0" alt="launch a new instance with the same values"></a>'
                      instanzentabelle += '</td>'
        
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'
                      
                      instanzentabelle += '<td align="right" colspan="3"><b>Status:</b></td>'        
                      # Hier kommt die Spalte "Status"
                      if x.state == u'running':
                        instanzentabelle += '<td bgcolor="#c3ddc3" colspan="4" align="center">running</td>'
                      elif x.state == u'pending':
                        instanzentabelle += '<td bgcolor="#ffffcc" colspan="4" align="center">pending</td>'
                      elif x.state == u'shutting-down':
                        instanzentabelle += '<td bgcolor="#ffcc99" colspan="4" align="center">shutting-down</td>'
                      elif x.state == u'terminated':
                        instanzentabelle += '<td bgcolor="#ffcccc" colspan="4" align="center">terminated</td>'
                      elif x.state == u'stopping':
                        instanzentabelle += '<td bgcolor="#ffcc99" colspan="4" align="center">stopping</td>'
                      elif x.state == u'stopped':
                        instanzentabelle += '<td bgcolor="#ffce81" colspan="4" align="center">stopped</td>'
                      else:
                        instanzentabelle += '<td colspan="4" align="center">'+str(x.state)+'</td>'
  
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'

                      if sprache == "de":
                        instanzentabelle += '<td align="right" colspan="3"><b>Typ:</b></td>'
                      else:
                        instanzentabelle += '<td align="right" colspan="3"><b>Type:</b></td>'
                      instanzentabelle += '<td align="center" colspan="4">'+str(x.instance_type)+'</td>'
                      
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'
                      
                      instanzentabelle += '<td align="right" colspan="3"><b>Reservation:</b></td>'                      
                      instanzentabelle += '<td align="center" colspan="4">'+str(i.id)+'</td>'
                      
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'
                      
                      instanzentabelle += '<td align="right" colspan="3"><b>Root:</b></td>'     
                      instanzentabelle += '<td align="center" colspan="4">'+str(x.root_device_type)+'</td>'
                      
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'

                      if sprache == "de":
                        instanzentabelle += '<td align="right" colspan="3"><b>Besitzer:</b></td>'
                      else:
                        instanzentabelle += '<td align="right" colspan="3"><b>Owner:</b></td>'
                      instanzentabelle += '<td align="center" colspan="4">'+str(i.owner_id)+'</td>'
                      
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'
                      
                      instanzentabelle += '<td align="right" colspan="3"><b>Image:</b></td>'     
                      instanzentabelle += '<td align="center" colspan="4">'+str(x.image_id)+'</td>'
                      
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'
                      
                      instanzentabelle += '<td align="right" colspan="3"><b>Kernel:</b></td>'    
                      instanzentabelle += '<td align="center" colspan="4">'+str(x.kernel)+'</td>'

                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'
                      
                      instanzentabelle += '<td align="right" colspan="3"><b>Ramdisk:</b></td>'    
                      instanzentabelle += '<td align="center" colspan="4">'+str(x.ramdisk)+'</td>'

                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'          
                                  
                      instanzentabelle += '<td align="right" colspan="3"><b>Zone:</b></td>'   
                      instanzentabelle += '<td align="center" colspan="4">'+str(x.placement)+'</td>'
                      
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'      
                      
                      if sprache == "de":
                        instanzentabelle += '<td align="right" colspan="3"><b>Gruppe:</b></td>'
                      else:
                        instanzentabelle += '<td align="right" colspan="3"><b>Group:</b></td>'
                      laenge_liste_guppen_reservations = len(i.groups)
                      if laenge_liste_guppen_reservations == 1:
                        # Wenn zu der Reservation nur eine Sicherheitsgruppe gehört
                        for z in range(laenge_liste_guppen_reservations):
                          instanzentabelle += '<td align="center" colspan="4">'+i.groups[z].id+'</td>'
                      else:
                        # Wenn zu der Reservation mehrere Sicherheitsgruppen gehören
                        for z in range(laenge_liste_guppen_reservations):
                          instanzentabelle += '<td align="center" colspan="4">'+i.groups[z].id+' </td>'
    
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'     
                      
                      if sprache == "de":
                        instanzentabelle += '<td align="right" colspan="3"><b>Extern:</b></td>'
                      else:
                        instanzentabelle += '<td align="right" colspan="3"><b>Public:</b></td>'
                      instanzentabelle += '<td align="center" colspan="4">'+str(x.public_dns_name)+'</td>'

                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'     

                      if sprache == "de":
                        instanzentabelle += '<td align="right" colspan="3"><b>Intern:</b></td>'
                      else:
                        instanzentabelle += '<td align="right" colspan="3"><b>Private:</b></td>'
                      instanzentabelle += '<td align="center" colspan="4">'+str(x.private_dns_name)+'</td>'

                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'     

                      if sprache == "de":
                        instanzentabelle += '<td align="right" colspan="3"><b>Schl&uuml;ssel:</b></td>'
                      else:
                        instanzentabelle += '<td align="right" colspan="3"><b>Keypair:</b></td>'
                      # Bei Eucalyptus kommt es manchmal vor, dass der Keyname nicht geholt werden kann. In diesem Fall kommt es zu einer HTML-Warnung, weil <tt></tt> leer ist. Darum lieber nur ein Leerzeichen, wenn der Keyname leer ist.
                      if x.key_name == "":
                        instanzentabelle += '<td align="center" colspan="4">&nbsp;</td>'
                      else:
                        instanzentabelle += '<td align="center" colspan="4">'+str(x.key_name)+'</td>'

                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'   

                      if sprache == "de":
                        instanzentabelle += '<td align="right" colspan="3"><b>Datum:</b></td>'
                      else:
                        instanzentabelle += '<td align="right" colspan="3"><b>Date:</b></td>'
                      datum_des_starts = parse(x.launch_time)
                      instanzentabelle += '<td align="center" colspan="4">'+str(datum_des_starts.strftime("%Y-%m-%d  %H:%M:%S"))+'</td>'
                      instanzentabelle += '</tr>'
                  instanzentabelle += '</table>'                  
                  
                else:
                  # Not the mobile version
                    
                  instanzentabelle = ''
                  instanzentabelle += '<table border="0" cellspacing="0" cellpadding="5">'

                  counter = 0
                  for i in liste_reservations:        
                    for x in i.instances:
                      if counter > 0:
                          instanzentabelle += '<tr><td colspan="6">&nbsp;</td></tr>'
                      counter += 1
                      
                      instanzentabelle += '<tr>'
                      
                      # Terminate instance
                      instanzentabelle += '<td bgcolor="#D4D4D4">'
                      if sprache == "de":
                        instanzentabelle += '<a href="/instanzterminate?id='
                        instanzentabelle += x.id
                        instanzentabelle += "&amp;mobile="
                        instanzentabelle += str(mobile)                      
                        instanzentabelle += '"title="Instanz entfernen"><img src="bilder/delete.png" width="16" height="16" border="0" alt="Instanz entfernen"></a>'
                      else:
                        instanzentabelle += '<a href="/instanzterminate?id='
                        instanzentabelle += x.id
                        instanzentabelle += "&amp;mobile="
                        instanzentabelle += str(mobile)       
                        instanzentabelle += '"title="terminate instance"><img src="bilder/delete.png" width="16" height="16" border="0" alt="terminate instance"></a>'
                      instanzentabelle += '</td>'

                      # Die Icons der Betriebssysteme nur unter Amazon
                      #if regionname == "Amazon":
                      # Hier kommt die Spalte mit den Icons der Betriebssysteme
                      instanzentabelle += '<td align="center" bgcolor="#D4D4D4">'                  
                      
                      try:
                        image = conn_region.get_image(str(x.image_id))
                      except EC2ResponseError:
                        instanzentabelle += '&nbsp;'
                      except DownloadError:
                        # Diese Exception hilft gegen diese beiden Fehler:
                        # DownloadError: ApplicationError: 2 timed out
                        # DownloadError: ApplicationError: 5
                        instanzentabelle += '&nbsp;'
                      else:
    
                        if image == None:
                          # Das hier kommt, wenn das Image der laufenden Instanz nicht mehr existiert!
                          instanzentabelle += '<img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Linux">'
                        else:
                          beschreibung_in_kleinbuchstaben = image.location.lower()
                          if beschreibung_in_kleinbuchstaben.find('fedora') != -1:
                            instanzentabelle += '<img src="bilder/fedora_icon_48.png" width="24" height="24" border="0" alt="Fedora">'
                          elif beschreibung_in_kleinbuchstaben.find('ubuntu') != -1:
                            instanzentabelle += '<img src="bilder/ubuntu_icon_48.png" width="24" height="24" border="0" alt="Ubuntu">'
                          elif beschreibung_in_kleinbuchstaben.find('debian') != -1:
                            instanzentabelle += '<img src="bilder/debian_icon_48.png" width="24" height="24" border="0" alt="Debian">'
                          elif beschreibung_in_kleinbuchstaben.find('gentoo') != -1:
                            instanzentabelle += '<img src="bilder/gentoo_icon_48.png" width="24" height="24" border="0" alt="Gentoo">'
                          elif beschreibung_in_kleinbuchstaben.find('suse') != -1:
                            instanzentabelle += '<img src="bilder/suse_icon_48.png" width="24" height="24" border="0" alt="SUSE">'
                          elif beschreibung_in_kleinbuchstaben.find('centos') != -1:
                            instanzentabelle += '<img src="bilder/centos_icon_48.png" width="24" height="24" border="0" alt="CentOS">'
                          elif beschreibung_in_kleinbuchstaben.find('redhat') != -1:
                            instanzentabelle += '<img src="bilder/redhat_icon_48.png" width="24" height="24" border="0" alt="RedHat">'
                          elif beschreibung_in_kleinbuchstaben.find('windows') != -1:
                            instanzentabelle += '<img src="bilder/windows_icon_48.png" width="24" height="24" border="0" alt="Windows">'
                          elif beschreibung_in_kleinbuchstaben.find('opensolaris') != -1:
                            instanzentabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                          elif beschreibung_in_kleinbuchstaben.find('solaris') != -1:
                            instanzentabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                          elif beschreibung_in_kleinbuchstaben.find('osol') != -1:
                            instanzentabelle += '<img src="bilder/opensolaris_icon_48.png" width="24" height="24" border="0" alt="Open Solaris">'
                          else:
                            instanzentabelle += '<img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Linux">'
                          instanzentabelle += '</td>'
                        #else:
                          ## Das hier wird bei Eucalyptus gemacht
                          #instanzentabelle += '<td><img src="bilder/linux_icon_48.gif" width="24" height="24" border="0" alt="Linux"></td>'

                      # Stop instance
                      instanzentabelle += '<td align="center" bgcolor="#D4D4D4">'
                      if x.root_device_type == 'instance-store': 
                        if x.state == u'running': 
                          fehlermeldung = "122"
                          if sprache == "de":
                            instanzentabelle += '<a href="/instanzen?message='
                            instanzentabelle += fehlermeldung
                            instanzentabelle += "&amp;mobile="
                            instanzentabelle += str(mobile)       
                            instanzentabelle += '"title="Instanz beenden"><img src="bilder/stop.png" width="16" height="16" border="0" alt="Instanz beenden"></a>'
                          else:
                            instanzentabelle += '<a href="/instanzen?message='
                            instanzentabelle += fehlermeldung
                            instanzentabelle += "&amp;mobile="
                            instanzentabelle += str(mobile)       
                            instanzentabelle += '"title="stop instance"><img src="bilder/stop.png" width="16" height="16" border="0" alt="stop instance"></a>'
                        else:
                          instanzentabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0" alt="">'                        
                      else:
                        if x.state == u'running': 
                          if sprache == "de":
                            instanzentabelle += '<a href="/instanzbeenden?id='
                            instanzentabelle += x.id
                            instanzentabelle += "&amp;mobile="
                            instanzentabelle += str(mobile)       
                            instanzentabelle += '"title="Instanz beenden"><img src="bilder/stop.png" width="16" height="16" border="0" alt="Instanz beenden"></a>'
                          else:
                            instanzentabelle += '<a href="/instanzbeenden?id='
                            instanzentabelle += x.id
                            instanzentabelle += "&amp;mobile="
                            instanzentabelle += str(mobile)       
                            instanzentabelle += '"title="stop instance"><img src="bilder/stop.png" width="16" height="16" border="0" alt="stop instance"></a>'
                        elif x.state == u'stopped':
                          if sprache == "de":
                            instanzentabelle += '<a href="/instanzstarten?id='
                            instanzentabelle += x.id
                            instanzentabelle += "&amp;mobile="
                            instanzentabelle += str(mobile)    
                            instanzentabelle += '"title="Instanz starten"><img src="bilder/up.png" width="16" height="16" border="0" alt="Instanz starten"></a>'
                          else:
                            instanzentabelle += '<a href="/instanzstarten?id='
                            instanzentabelle += x.id
                            instanzentabelle += "&amp;mobile="
                            instanzentabelle += str(mobile)    
                            instanzentabelle += '"title="start instance"><img src="bilder/up.png" width="16" height="16" border="0" alt="start instance"></a>'
                        # If the instance status is "stopping", "pending", "shutting-down" oder "terminated"...                                           
                        else:
                          if sprache == "de":
                            instanzentabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0" alt="Die Instanz kann jetzt nicht beendet werden">'
                          else:
                            instanzentabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0" alt="This instance cannot be stopped now">'
                      instanzentabelle += '</td>'
                      
                      
                      # Reboot instance
                      instanzentabelle += '<td align="center" bgcolor="#D4D4D4">'
                      if x.state == u'running':
                        if sprache == "de":
                          instanzentabelle += '<a href="/instanzreboot?id='
                          instanzentabelle += x.id
                          instanzentabelle += "&amp;mobile="
                          instanzentabelle += str(mobile)    
                          instanzentabelle += '"title="Instanz neustarten"><img src="bilder/gear.png" width="16" height="16" border="0" alt="Instanz neustarten"></a>'
                        else:
                          instanzentabelle += '<a href="/instanzreboot?id='
                          instanzentabelle += x.id
                          instanzentabelle += "&amp;mobile="
                          instanzentabelle += str(mobile)    
                          instanzentabelle += '"title="reboot instance"><img src="bilder/gear.png" width="16" height="16" border="0" alt="reboot instance"></a>'
                      else:
                        instanzentabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0" alt="">'                        
                      instanzentabelle += '</td>'
                      
                      # Console output
                      instanzentabelle += '<td align="center" bgcolor="#D4D4D4">'
                      if x.state == u'running':
                        if sprache == "de":
                          instanzentabelle += '<a href="/console_output?id='
                          instanzentabelle += x.id
                          instanzentabelle += "&amp;mobile="
                          instanzentabelle += str(mobile)    
                          instanzentabelle += '"title="Konsolenausgabe"><img src="bilder/terminal.png" width="22" height="16" border="0" alt="Konsolenausgabe"></a>'
                        else:
                          instanzentabelle += '<a href="/console_output?id='
                          instanzentabelle += x.id
                          instanzentabelle += "&amp;mobile="
                          instanzentabelle += str(mobile)    
                          instanzentabelle += '"title="console output"><img src="bilder/terminal.png" width="22" height="16" border="0" alt="console output"></a>'
                      else:
                        instanzentabelle += '<img src="bilder/platzhalter.png" width="16" height="16" border="0" alt="">'                        
                      instanzentabelle += '</td>'
    
                      # Launch more of these
                      instanzentabelle += '<td align="center" bgcolor="#D4D4D4">'
                      if sprache == "de":
                        instanzentabelle += '<a href="/instanzanlegen?image='
                        instanzentabelle += str(x.image_id)
                        instanzentabelle += "&amp;zone="
                        instanzentabelle += str(x.placement)
                        instanzentabelle += "&amp;key="
                        instanzentabelle += str(x.key_name)
                        # Es ist denkbar, dass der Wert des Kernels "None" ist.
                        # Dann darf man hier nichts angeben!
                        if x.kernel != None:
                          instanzentabelle += "&amp;aki="
                          instanzentabelle += str(x.kernel)
                        # Manchmal ist die Angabe der Ramdisk "None".
                        # Dann darf man hier nichts angeben!
                        if x.ramdisk != None:
                          instanzentabelle += "&amp;ari="
                          instanzentabelle += str(x.ramdisk)
                        instanzentabelle += "&amp;type="
                        instanzentabelle += str(x.instance_type)
                        instanzentabelle += "&amp;gruppe="
                        instanzentabelle += i.groups[0].id
                        instanzentabelle += "&amp;mobile="
                        instanzentabelle += str(mobile)    
                        instanzentabelle += '"title="Eine weitere Instanz mit den gleichen Parametern starten"><img src="bilder/plus.png" width="16" height="16" border="0" alt="Eine weitere Instanz mit den gleichen Parametern starten"></a>'
                      else:
                        instanzentabelle += '<a href="/instanzanlegen?image='
                        instanzentabelle += str(x.image_id)
                        instanzentabelle += "&amp;zone="
                        instanzentabelle += str(x.placement)
                        instanzentabelle += "&amp;key="
                        instanzentabelle += str(x.key_name)
                        # Es ist denkbar, dass der Wert des Kernels "None" ist.
                        # Dann darf man hier nichts angeben!
                        if x.kernel != None:
                          instanzentabelle += "&amp;aki="
                          instanzentabelle += str(x.kernel)
                        # Manchmal ist die Angabe der Ramdisk "None".
                        # Dann darf man hier nichts angeben!
                        if x.ramdisk != None:
                          instanzentabelle += "&amp;ari="
                          instanzentabelle += str(x.ramdisk)
                        instanzentabelle += "&amp;type="
                        instanzentabelle += str(x.instance_type)
                        instanzentabelle += "&amp;gruppe="
                        instanzentabelle += i.groups[0].id
                        instanzentabelle += "&amp;mobile="
                        instanzentabelle += str(mobile)    
                        instanzentabelle += '"title="launch a new instance with the same values"><img src="bilder/plus.png" width="16" height="16" border="0" alt="launch a new instance with the same values"></a>'
                      instanzentabelle += '</td>'
        
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'
                      
                      # Id of the instance
                      instanzentabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>ID:</b></td>'    
                      instanzentabelle += '<td align="left">'+str(x.id)+'</td>'
                      
                      
                      instanzentabelle += '<td align="right" bgcolor="#D4D4D4"><b>Status:</b></td>'        
                      # Hier kommt die Spalte "Status"
                      if x.state == u'running':
                        instanzentabelle += '<td bgcolor="#c3ddc3" align="left">running</td>'
                      elif x.state == u'pending':
                        instanzentabelle += '<td bgcolor="#ffffcc" align="left">pending</td>'
                      elif x.state == u'shutting-down':
                        instanzentabelle += '<td bgcolor="#ffcc99" align="left">shutting-down</td>'
                      elif x.state == u'terminated':
                        instanzentabelle += '<td bgcolor="#ffcccc" align="left">terminated</td>'
                      elif x.state == u'stopping':
                        instanzentabelle += '<td bgcolor="#ffcc99" align="left">stopping</td>'
                      elif x.state == u'stopped':
                        instanzentabelle += '<td bgcolor="#ffce81" align="left">stopped</td>'
                      else:
                        instanzentabelle += '<td align="left">'+str(x.state)+'</td>'
  
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'
                      
                      instanzentabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Reservation:</b></td>'                      
                      instanzentabelle += '<td align="left">'+str(i.id)+'</td>'
                      
                      instanzentabelle += '<td align="right" bgcolor="#D4D4D4"><b>Image:</b></td>'     
                      instanzentabelle += '<td align="left">'+str(x.image_id)+'</td>'
                      
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'
                      
                      if sprache == "de":
                        instanzentabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Typ:</b></td>'
                      else:
                        instanzentabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Type:</b></td>'
                      instanzentabelle += '<td align="left">'+str(x.instance_type)+'</td>'

                      instanzentabelle += '<td align="right" bgcolor="#D4D4D4"><b>Kernel:</b></td>'    
                      instanzentabelle += '<td align="left">'+str(x.kernel)+'</td>'
                      
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'
                      
                      instanzentabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Root:</b></td>'     
                      instanzentabelle += '<td align="left">'+str(x.root_device_type)+'</td>'

                      instanzentabelle += '<td align="right" bgcolor="#D4D4D4"><b>Ramdisk:</b></td>'    
                      instanzentabelle += '<td align="left">'+str(x.ramdisk)+'</td>'
                      
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'

                      if sprache == "de":
                        instanzentabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Gruppe:</b></td>'
                      else:
                        instanzentabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Group:</b></td>'
                      laenge_liste_guppen_reservations = len(i.groups)
                      if laenge_liste_guppen_reservations == 1:
                        # Wenn zu der Reservation nur eine Sicherheitsgruppe gehört
                        for z in range(laenge_liste_guppen_reservations):
                          instanzentabelle += '<td align="left">'+i.groups[z].id+'</td>'
                      else:
                        # Wenn zu der Reservation mehrere Sicherheitsgruppen gehören
                        for z in range(laenge_liste_guppen_reservations):
                          instanzentabelle += '<td align="left">'+i.groups[z].id+' </td>'
    
                      if sprache == "de":
                        instanzentabelle += '<td align="right" bgcolor="#D4D4D4"><b>Besitzer:</b></td>'
                      else:
                        instanzentabelle += '<td align="right" bgcolor="#D4D4D4"><b>Owner:</b></td>'
                      instanzentabelle += '<td align="left">'+str(i.owner_id)+'</td>'

                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'          
                                  
                      instanzentabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Zone:</b></td>'   
                      instanzentabelle += '<td align="left">'+str(x.placement)+'</td>'

                      if sprache == "de":
                        instanzentabelle += '<td align="right" bgcolor="#D4D4D4"><b>Schl&uuml;ssel:</b></td>'
                      else:
                        instanzentabelle += '<td align="right" bgcolor="#D4D4D4"><b>Keypair:</b></td>'
                      # Bei Eucalyptus kommt es manchmal vor, dass der Keyname nicht geholt werden kann. In diesem Fall kommt es zu einer HTML-Warnung, weil <tt></tt> leer ist. Darum lieber nur ein Leerzeichen, wenn der Keyname leer ist.
                      if x.key_name == "":
                        instanzentabelle += '<td align="left">&nbsp;</td>'
                      else:
                        instanzentabelle += '<td align="left">'+str(x.key_name)+'</td>'
                        
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'                          
  

                      if sprache == "de":
                        instanzentabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Intern:</b></td>'
                      else:
                        instanzentabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Private:</b></td>'
                      instanzentabelle += '<td align="left" colspan="3">'+str(x.private_dns_name)+'</td>'
                      
                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'     
                      
                      if sprache == "de":
                        instanzentabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Extern:</b></td>'
                      else:
                        instanzentabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Public:</b></td>'
                      instanzentabelle += '<td align="left" colspan="3">'+str(x.public_dns_name)+'</td>'

                      instanzentabelle += '</tr>'
                      instanzentabelle += '<tr>'     


                      if sprache == "de":
                        instanzentabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Datum:</b></td>'
                      else:
                        instanzentabelle += '<td align="right" colspan="3" bgcolor="#D4D4D4"><b>Date:</b></td>'
                      datum_des_starts = parse(x.launch_time)
                      instanzentabelle += '<td align="left" colspan="3">'+str(datum_des_starts.strftime("%Y-%m-%d  %H:%M:%S"))+'</td>'
                      instanzentabelle += '</tr>'
                  instanzentabelle += '</table>'          
  
  
            if laenge_liste_reservations >= 1:
              alle_instanzen_loeschen_button = '<p>&nbsp;</p>\n'
              alle_instanzen_loeschen_button += '<table border="0" cellspacing="0" cellpadding="5">\n'
              alle_instanzen_loeschen_button += '<tr>\n'
              alle_instanzen_loeschen_button += '<td align="left">\n'
              alle_instanzen_loeschen_button += '<form action="/alle_instanzen_beenden" method="get">\n'
              alle_instanzen_loeschen_button += '<input type="hidden" name="mobile" value="'+mobile+'">\n'
              if sprache == "de":
                alle_instanzen_loeschen_button += '<input type="submit" value="Alle Instanzen beenden">\n'
              else:
                alle_instanzen_loeschen_button += '<input type="submit" value="terminate all instances">\n'
              alle_instanzen_loeschen_button += '</form>\n'
              alle_instanzen_loeschen_button += '</td>\n'
              alle_instanzen_loeschen_button += '</tr>\n'
              alle_instanzen_loeschen_button += '</table>\n'
            else:
              alle_instanzen_loeschen_button = '<p>&nbsp;</p>\n'

            path = '&amp;path=instanzen&amp;mobile='+mobile

            template_values = {
            'navigations_bar': navigations_bar,
            'url': url,
            'url_linktext': url_linktext,
            'zone': regionname,
            'zone_amazon': zone_amazon,
            'reservationliste': instanzentabelle,
            'zonen_liste': zonen_liste,
            'input_error_message': input_error_message,
            'alle_instanzen_loeschen_button': alle_instanzen_loeschen_button,
            'mobile': mobile,
            'path': path,
            }
  
            if mobile == "true":
                path = os.path.join(os.path.dirname(__file__), "../templates/mobile", sprache, "instanzen.html")
            else:
                path = os.path.join(os.path.dirname(__file__), "../templates", sprache, "instanzen.html")
            self.response.out.write(template.render(path,template_values))



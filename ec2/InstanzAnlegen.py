#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError

from library import login

from boto.ec2.connection import *

class InstanzAnlegen(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        instance_type = self.request.get('type')
        keys_liste = self.request.get('key')
        image_id = self.request.get('image')
        gruppen_liste = self.request.get('gruppe')
        aki_id = self.request.get('aki')
        ari_id = self.request.get('ari')
        zonen_auswahl = self.request.get('zone')

        gruppen_liste_liste = []
        gruppen_liste_liste.append(gruppen_liste)

        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')

        conn_region, regionname = login(username)

        try:
          # Instanz(en) anlegen
          reservation = conn_region.run_instances(image_id,
                                                  key_name=keys_liste,
                                                  security_groups=gruppen_liste_liste,
                                                  instance_type=instance_type,
                                                  placement=zonen_auswahl,
                                                  kernel_id=aki_id,
                                                  ramdisk_id=ari_id)
        except EC2ResponseError:
          # Wenn es nicht geklappt hat
          fehlermeldung = "78"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat
          fehlermeldung = "77"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)


    def post(self):
        #self.response.out.write('posted!')
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        instance_type = self.request.get('instance_type')
        number_instances = self.request.get('number_instances')
        keys_liste = self.request.get('keys_liste')
        image_manifest = self.request.get('image_manifest')
        image_id = self.request.get('image_id')
        number_instances_max = self.request.get('number_instances_max')
        number_instances_min = self.request.get('number_instances_min')
        gruppen_liste = self.request.get('gruppen_liste')
        aki_id = self.request.get('aki_id')
        ari_id = self.request.get('ari_id')
        zonen_auswahl = self.request.get('zonen_auswahl')

        gruppen_liste_liste = []
        gruppen_liste_liste.append(gruppen_liste)

        if not aki_id:
          aki_id = None

        if not ari_id:
          ari_id = None

        if not zonen_auswahl:
          zonen_auswahl = None

        # Wenn im Feld Instanzen (max) ein kleinerer Wert eingegebenen wurde als im Feld
        # Instanzen (min), dann macht das keinen Sinn.
        # In diesem Fall ist dann Instanzen (max) = Instanzen (min)
        if number_instances_max < number_instances_min:
          number_instances_max = number_instances_min

        # Den Usernamen erfahren
        username = users.get_current_user()
        if not username:
            self.redirect('/')

        conn_region, regionname = login(username)

        try:
          # Instanz(en) anlegen
          reservation = conn_region.run_instances(image_id,
                                                  min_count=number_instances_min,
                                                  max_count=number_instances_max,
                                                  key_name=keys_liste,
                                                  security_groups=gruppen_liste_liste,
                                                  instance_type=instance_type,
                                                  placement=zonen_auswahl,
                                                  kernel_id=aki_id,
                                                  ramdisk_id=ari_id)
        except EC2ResponseError, fehlernachricht:
          # Zum Testen: self.response.out.write(fehlernachricht)
          # Wenn es nicht geklappt hat
          fehlermeldung = "78"
          #So geht es auch und dann wird nur der hintere Teil der Fehlermeldung ausgegeben.
          #self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung+'&fehlernachricht='+str(fehlernachricht.endElement))
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung+'&fehlernachricht='+str(fehlernachricht))
        except DownloadError:
          # Diese Exception hilft gegen diese beiden Fehler:
          # DownloadError: ApplicationError: 2 timed out
          # DownloadError: ApplicationError: 5
          fehlermeldung = "8"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          # Wenn es geklappt hat
          fehlermeldung = "77"
          self.redirect('/instanzen?mobile='+str(mobile)+'&message='+fehlermeldung)

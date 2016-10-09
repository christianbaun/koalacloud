#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

# Copyright 2009,2010 Christian Baun

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import decimal
import wsgiref.handlers
import os
import sys
import cgi
import time
import re
import webapp2 as webapp

from ebs.VolumesLoesen import *
from ebs.VolumesEntfernen import *
from ebs.AlleVolumesLoeschenDefinitiv import *
from ebs.VolumeDefinitivAnhaengen import *
from ebs.VolumesErzeugen import *
from ebs.VolumesAnhaengen import *
from ebs.Volumes import *
from ebs.AlleVolumesLoeschenFrage import *
from ebs.Snapshots import *
from ebs.SnapshotsAmazonAll import *
from ebs.SnapshotsErzeugen import *
from ebs.SnapshotsEntfernen import *
from ebs.SnapshotsErzeugenDefinitiv import *
from ebs.VolumeausSnapshotErzeugen import *
from ebs.VolumeausSnapshotErzeugenDefinitiv import *

from ec2.AlleInstanzenBeenden import *
from ec2.Zonen import *
from ec2.Release_IP import *
from ec2.Allocate_IP import *
from ec2.Disassociate_IP import *
from ec2.IP_Definitiv_Anhaengen import *
from ec2.Associate_IP import *
from ec2.Elastic_IPs import *
from ec2.KeyEntfernen import *
from ec2.KeyErzeugen import *
from ec2.InstanzAnlegen import *
from ec2.InstanzAnlegenNimbus import *
from ec2.InstanzReboot import *
from ec2.InstanzBeenden import *
from ec2.AlleInstanzenBeendenFrage import *
from ec2.Images import *
from ec2.ImageStarten import *
from ec2.Instanzen import *
from ec2.SecurityGroups import *
from ec2.GruppeErzeugen import *
from ec2.GruppeEntfernen import *
from ec2.GruppeAendern import *
from ec2.GruppeRegelErzeugen import *
from ec2.GruppeRegelEntfernen import *
from ec2.Keys import *
from ec2.InstanzTerminate import *
from ec2.InstanzStarten import *
#from ec2.ConsoleOutput import *

from elb.LoadBalancer import *
from elb.LoadBalancer_Instanz_Zuordnen import *
from elb.LoadBalancer_Instanz_Entfernen import *
from elb.LoadBalancer_Zone_Entfernen import *
from elb.LoadBalancer_Zone_Zuordnen import *
from elb.LoadBalancer_Aendern import *
from elb.DeleteLoadBalancer import *
from elb.CreateLoadBalancer import *
from elb.CreateLoadBalancerWirklich import *

from s3.AlleKeysLoeschenDefinitiv import *
from s3.ACL_Aendern import *
from s3.AlleKeysLoeschenFrage import *
from s3.BucketEntfernen import *
from s3.BucketKeyEntfernen import *
from s3.BucketVerzeichnisErzeugen import *
from s3.BucketErzeugen import *
from s3.ACL_einsehen import *
from s3.BucketInhalt import *
from s3.BucketInhaltPur import *
from s3.S3 import *

from internal.ZugangEntfernen import *
from internal.Sprache import *
from internal.Datastore import *
from internal.PersoenlicheDatanLoeschen import *
from internal.Info import *
from internal.PersoenlicheFavoritenLoeschen import *
from internal.FavoritAMIerzeugen import *
from internal.FavoritEntfernen import *
from internal.ZugangEinrichten import *
from internal.RegionWechseln import *
from internal.Regionen import *
from internal.Login import *
from internal.MainPage import *

from library import login
from library import xor_crypt_string
from library import aktuelle_sprache
from library import navigations_bar_funktion
from library import amazon_region
from library import zonen_liste_funktion
from library import format_error_message_green
from library import format_error_message_red
from library import loginelb
from library import logins3
from library import aws_access_key_erhalten
from library import aws_secret_access_key_erhalten


from error_messages import error_messages

from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch import DownloadError
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from boto.ec2.connection import *
from boto.ec2 import *
from boto.s3.connection import *
from boto.s3 import *
from boto.ec2.elb import ELBConnection
from dateutil.parser import *
from dateutil.tz import *
from datetime import *
# für die Verschlüsselung
# this is needed for the encyption
from itertools import izip, cycle
import hmac, sha
# für die Verschlüsselung
# this is needed for the encyption
import base64

class ConsoleOutput(webapp.RequestHandler):
    def get(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        # self.response.out.write('posted!')
        # Den Usernamen erfahren
        username = users.get_current_user()  
        if not username:
            self.redirect('/')
        # Die ID der Instanz holen
        instance_id = self.request.get('id')

        # Nachsehen, ob eine Region/Zone ausgewählte wurde
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        if results:
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
                path = os.path.join(os.path.dirname(__file__), "templates/mobile", sprache, "console_output.html")
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
                path = os.path.join(os.path.dirname(__file__), "templates/mobile", sprache, "console_output.html")
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
                path = os.path.join(os.path.dirname(__file__), "templates/mobile", sprache, "console_output.html")
            else:
                path = os.path.join(os.path.dirname(__file__), "templates", sprache, "console_output.html")
            self.response.out.write(template.render(path,template_values))
        else:
          self.redirect('/')


def main():
    application = webapp.WSGIApplication([('/', MainPage),
                                          ('/regionen', Regionen),
                                          ('/instanzen', Instanzen),
                                          ('/alle_instanzen_beenden', AlleInstanzenBeendenFrage),
                                          ('/alle_instanzen_beenden_definitiv', AlleInstanzenBeenden),
                                          ('/instanzbeenden', InstanzBeenden),
                                          ('/instanzterminate', InstanzTerminate),
                                          ('/instanzreboot', InstanzReboot),
                                          ('/instanzanlegen', InstanzAnlegen),
                                          ('/instanzstarten', InstanzStarten),
                                          ('/instanzanlegen_nimbus', InstanzAnlegenNimbus),
                                          ('/images', Images),
                                          ('/imagestarten', ImageStarten),
                                          ('/console_output', ConsoleOutput),
                                         # ('/login', Login), #This can be erased!
                                          ('/schluessel', Keys),
                                          ('/schluesselentfernen', KeyEntfernen),
                                          ('/schluesselerzeugen', KeyErzeugen),
                                          ('/securitygroups', SecurityGroups),
                                          ('/gruppenentfernen', GruppeEntfernen),
                                          ('/gruppenerzeugen', GruppeErzeugen),
                                          ('/grupperegelanlegen', GruppeRegelErzeugen),
                                          ('/grupperegelentfernen', GruppeRegelEntfernen),
                                          ('/gruppenaendern', GruppeAendern),
                                          ('/zonen', Zonen),
                                          ('/sprache', Sprache),
                                          ('/info', MainPage),
                                          ('/loadbalancer', LoadBalancer),
                                          ('/delete_load_balancer', DeleteLoadBalancer),
                                          ('/create_load_balancer', CreateLoadBalancer),
                                          ('/loadbalanceraendern', LoadBalancer_Aendern),
                                          ('/loadbalancer_instanz_zuordnen', LoadBalancer_Instanz_Zuordnen),
                                          ('/loadbalancer_deregister_instance', LoadBalancer_Instanz_Entfernen),
                                          ('/loadbalancer_deregister_zone', LoadBalancer_Zone_Entfernen),
                                          ('/loadbalancer_zone_zuordnen', LoadBalancer_Zone_Zuordnen),
                                          ('/elb_definiv_erzeugen', CreateLoadBalancerWirklich),
                                          ('/elastic_ips', Elastic_IPs),
                                          ('/ip_definitiv_anhaengen', IP_Definitiv_Anhaengen),
                                          ('/release_address', Release_IP),
                                          ('/allocate_address', Allocate_IP),
                                          ('/associate_address', Associate_IP),
                                          ('/disassociate_address', Disassociate_IP),
                                          ('/zugangeinrichten', ZugangEinrichten),
                                          ('/zugangentfernen', ZugangEntfernen),
                                          ('/regionwechseln', RegionWechseln),
                                          ('/persoenliche_datan_loeschen', PersoenlicheDatanLoeschen),
                                          ('/persoenliche_favoriten_loeschen', PersoenlicheFavoritenLoeschen),
                                          ('/favoritamierzeugen', FavoritAMIerzeugen),
                                          ('/favoritentfernen', FavoritEntfernen),
                                          ('/s3', S3),
                                          ('/bucketerzeugen', BucketErzeugen),
                                          ('/bucketentfernen', BucketEntfernen),
                                          ('/bucket_inhalt', BucketInhalt),
                                          ('/bucket_inhalt_pure', BucketInhaltPur),
                                          ('/bucketkeyentfernen', BucketKeyEntfernen),
                                          ('/bucketverzeichniserzeugen', BucketVerzeichnisErzeugen),
                                          ('/acl_einsehen', ACL_einsehen),
                                          ('/acl_aendern', ACL_Aendern),
                                          ('/alle_keys_loeschen', AlleKeysLoeschenFrage),
                                          ('/alle_keys_loeschen_definitiv', AlleKeysLoeschenDefinitiv),
                                          ('/snapshots_amazon_all', SnapshotsAmazonAll),
                                          ('/snapshots', Snapshots),
                                          ('/snapshotsentfernen', SnapshotsEntfernen),
                                          ('/snapshoterzeugen', SnapshotsErzeugen),
                                          ('/snapshoterzeugendefinitiv', SnapshotsErzeugenDefinitiv),
                                          ('/volumes', Volumes),
                                          ('/volumeentfernen', VolumesEntfernen),
                                          ('/volumeanhaengen', VolumesAnhaengen),
                                          ('/volumedefinitivanhaengen', VolumeDefinitivAnhaengen),
                                          ('/volumeerzeugen', VolumesErzeugen),
                                          ('/volumeloesen', VolumesLoesen),
                                          ('/volumeaussnapshoterzeugen', VolumeausSnapshotErzeugen),
                                          ('/volumeaussnapshoterzeugen_definiv', VolumeausSnapshotErzeugenDefinitiv),
                                          ('/alle_volumes_loeschen', AlleVolumesLoeschenFrage),
                                          ('/alle_volumes_loeschen_definitiv', AlleVolumesLoeschenDefinitiv)],
                                          debug=True)
    run_wsgi_app(application)
    #wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
    main()






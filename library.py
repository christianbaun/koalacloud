#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

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



from internal.Datastore import *

def login(username):
  # Die Zugangsdaten des Benutzers holen
  aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

  for db_eintrag in aktivezone:
    zoneinderdb = db_eintrag.aktivezone

    if zoneinderdb in ("us-east-1", "eu-west-1", "us-west-1", "us-west-2", "ap-southeast-1", "ap-northeast-1", "sa-east-1"):
      aktuellezone = "Amazon"
    elif zoneinderdb in ("us_east", "us_west"):
      aktuellezone = "HP"
    else:
      aktuellezone = zoneinderdb


  if aktivezone:
    # In der Spalte "eucalyptusname" steht entweder "Amazon" oder der Eucalyptus-Name der Private Cloud
    zugangsdaten = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db=aktuellezone)

    for db_eintrag in zugangsdaten:
      accesskey = db_eintrag.accesskey
      secretaccesskey = db_eintrag.secretaccesskey
      endpointurl = db_eintrag.endpointurl
      eucalyptusname = db_eintrag.eucalyptusname
      port = db_eintrag.port
      regionname = db_eintrag.regionname

    if zoneinderdb == "us-east-1" or zoneinderdb == "eu-west-1" or zoneinderdb == "us-west-1" or zoneinderdb == "us-west-2" or zoneinderdb == "ap-southeast-1" or zoneinderdb == "ap-northeast-1" or zoneinderdb == "sa-east-1":
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_region = boto.ec2.connect_to_region(zoneinderdb,
                                               aws_access_key_id=accesskey,
                                               aws_secret_access_key=secretaccesskey,
                                               is_secure=True,
                                               validate_certs=False)
      regionname = aktuellezone
    elif zoneinderdb == "us_east" or zoneinderdb == "us_west":
      # HP Cloud
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_region = boto.connect_ec2(aws_access_key_id=accesskey,
                                               aws_secret_access_key=secretaccesskey,
                                               is_secure=True,
                                               validate_certs=False,
                                               region=RegionInfo(name="hpcloud", endpoint=endpointurl),
                                               path="/services/Cloud/")
      regionname = aktuellezone     
    elif regionname == "nimbus":
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_region = boto.connect_ec2(str(accesskey), str(secretaccesskey), port=int(port))
      conn_region.host = str(endpointurl)

    elif regionname == "GoogleStorage":
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      calling_format=boto.s3.connection.OrdinaryCallingFormat()
      conn_region = boto.connect_s3(aws_access_key_id=accesskey,
                                    aws_secret_access_key=secretaccesskey,
                                    is_secure=True,
                                    validate_certs=False,
                                    host="commondatastorage.googleapis.com",
                                    calling_format=calling_format,
                                    path="/")

      regionname = aktuellezone
    elif regionname == "HostEuropeCloudStorage":
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      calling_format=boto.s3.connection.OrdinaryCallingFormat()
      conn_region = boto.connect_s3(aws_access_key_id=accesskey,
                                    aws_secret_access_key=secretaccesskey,
                                    is_secure=False,
                                    validate_certs=False,
                                    host="cs.hosteurope.de",
                                    calling_format=calling_format,
                                    path="/")

      regionname = aktuellezone
    elif regionname == "DunkelCloudStorage":
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      calling_format=boto.s3.connection.OrdinaryCallingFormat()
      conn_region = boto.connect_s3(aws_access_key_id=accesskey,
                                    aws_secret_access_key=secretaccesskey,
                                    is_secure=True,
                                    validate_certs=False,
                                    host="dcs.dunkel.de",
                                    calling_format=calling_format,
                                    path="/")

      regionname = aktuellezone
    elif regionname == "opennebula":
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_region = boto.connect_ec2(accesskey, secretaccesskey, is_secure=False, validate_certs=False, port=int(port))
      conn_region.host = endpointurl

      regionname = aktuellezone
    else:
      port = int(port)
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_region = boto.connect_ec2(aws_access_key_id=accesskey,
                                    aws_secret_access_key=secretaccesskey,
                                    is_secure=False,
                                    validate_certs=False,
                                    region=RegionInfo(name="eucalyptus", endpoint=endpointurl),
                                    port=port,
                                    path="/services/Eucalyptus")

      regionname = aktuellezone
  else:
    regionname = "---"
  return conn_region, regionname




def xor_crypt_string(data, key):
    return ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(data, cycle(key)))


def aktuelle_sprache(username):
    # Nachsehen, ob eine Sprache ausgewählte wurde und wenn ja, welche Sprache
    spracheanfrage = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankSprache WHERE user = :username_db", username_db=username)
    ergebnisse = spracheanfrage.fetch(10)

    if not ergebnisse:
        logindaten = KoalaCloudDatenbankSprache(sprache="en",
                                              user=username)
        logindaten.put()   # In den Datastore schreiben
        spracheanfrage = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankSprache WHERE user = :username_db", username_db=username)
        ergebnisse = spracheanfrage.fetch(10)

    for ergebnis in ergebnisse:
        if ergebnis.sprache == "en":
            sprache = "en"
        elif ergebnis.sprache == "de":
            sprache = "de"
        else:
            sprache = "en"

    return sprache
  
  
def navigations_bar_funktion(sprache,mobile):
  if mobile == "true":
    if sprache == "de":
        navigations_bar = ''
        navigations_bar = navigations_bar + '<form name="gowhereform" action="">\n'
        navigations_bar = navigations_bar + '<select id="gowhere" onchange="go()">\n'
        navigations_bar = navigations_bar + '<option>- Funktionalit&auml;t/Dienst ausw&auml;hlen -\n'
        navigations_bar = navigations_bar + '<option value="/regionen?mobile=true">Regionen\n'
        navigations_bar = navigations_bar + '<option value="/instanzen?mobile=true">Instanzen\n'
        navigations_bar = navigations_bar + '<option value="/images?mobile=true">Images\n'
        navigations_bar = navigations_bar + '<option value="/schluessel?mobile=true">Schl&uuml;ssel\n'
        navigations_bar = navigations_bar + '<option value="/volumes?mobile=true">Elastic Block Store\n'
        navigations_bar = navigations_bar + '<option value="/snapshots?mobile=true">Snapshots\n'
        navigations_bar = navigations_bar + '<option value="/elastic_ips?mobile=true">Elastische IPs\n'
        navigations_bar = navigations_bar + '<option value="/zonen?mobile=true">Verf&uuml;gbarkeitszonen\n'
        navigations_bar = navigations_bar + '<option value="/securitygroups?mobile=true">Sicherheitsgruppen\n'
        navigations_bar = navigations_bar + '<option value="/s3?mobile=true">Simple Storage Service\n'
        navigations_bar = navigations_bar + '<option value="/loadbalancer?mobile=true">Elastische Lastverteiler\n'
        navigations_bar = navigations_bar + '<option value="/info?mobile=true">Info\n'
        navigations_bar = navigations_bar + '</select>\n'
        navigations_bar = navigations_bar + '</form>'
    else:
        navigations_bar = ''
        navigations_bar = navigations_bar + '<form name="gowhereform" action="">\n'
        navigations_bar = navigations_bar + '<select id="gowhere" onchange="go()">\n'
        navigations_bar = navigations_bar + '<option>- select action/service -\n'
        navigations_bar = navigations_bar + '<option value="/regionen?mobile=true">Regions\n'
        navigations_bar = navigations_bar + '<option value="/instanzen?mobile=true">Instances\n'
        navigations_bar = navigations_bar + '<option value="/images?mobile=true">Images\n'
        navigations_bar = navigations_bar + '<option value="/schluessel?mobile=true">Keys\n'
        navigations_bar = navigations_bar + '<option value="/volumes?mobile=true">Elastic Block Store\n'
        navigations_bar = navigations_bar + '<option value="/snapshots?mobile=true">Snapshots\n'
        navigations_bar = navigations_bar + '<option value="/elastic_ips?mobile=true">Elastic IPs\n'
        navigations_bar = navigations_bar + '<option value="/zonen?mobile=true">Availability Zones\n'
        navigations_bar = navigations_bar + '<option value="/securitygroups?mobile=true">Security Groups\n'
        navigations_bar = navigations_bar + '<option value="/s3?mobile=true">Simple Storage Service\n'
        navigations_bar = navigations_bar + '<option value="/loadbalancer?mobile=true">Elastic Load Balancer\n'
        navigations_bar = navigations_bar + '<option value="/info?mobile=true">Info\n'
        navigations_bar = navigations_bar + '</select>\n'
        navigations_bar = navigations_bar + '</form>'
    return navigations_bar
  else:
    if sprache == "de":
        navigations_bar = '&nbsp; \n'
        navigations_bar = navigations_bar + '<a href="/regionen" title="Regionen">Regionen</a> | \n'
        navigations_bar = navigations_bar + '<a href="/instanzen" title="Instanzen">Instanzen</a> | \n'
        navigations_bar = navigations_bar + '<a href="/images" title="Images">Images</a> | \n'
        navigations_bar = navigations_bar + '<a href="/schluessel" title="Schl&uuml;ssel">Schl&uuml;ssel</a> | \n'
        navigations_bar = navigations_bar + '<a href="/volumes" title="Elastic Block Store">EBS</a> | \n'
        navigations_bar = navigations_bar + '<a href="/snapshots" title="Snapshots">Snapshots</a> | \n'
        navigations_bar = navigations_bar + '<a href="/elastic_ips" title="Elastic IPs">IPs</a> | \n'
        navigations_bar = navigations_bar + '<a href="/zonen" title="Verf&uuml;gbarkeitszonen">Zonen</a> | \n'
        navigations_bar = navigations_bar + '<a href="/securitygroups" title="Sicherheitsgruppen">Gruppen</a> | \n'
        navigations_bar = navigations_bar + '<a href="/s3" title="Simple Storage Service">S3</a> | \n'
        navigations_bar = navigations_bar + '<a href="/loadbalancer" title="Elastic Load Balancer">ELB</a> | \n'
        navigations_bar = navigations_bar + '<a href="/info" title="Info">Info</a> \n'
    else:
        navigations_bar = '&nbsp; \n'
        navigations_bar = navigations_bar + '<a href="/regionen" title="Regions">Regions</a> | \n'
        navigations_bar = navigations_bar + '<a href="/instanzen" title="Instances">Instances</a> | \n'
        navigations_bar = navigations_bar + '<a href="/images" title="Images">Images</a> | \n'
        navigations_bar = navigations_bar + '<a href="/schluessel" title="Keys">Keys</a> | \n'
        navigations_bar = navigations_bar + '<a href="/volumes" title="Elastic Block Store">EBS</a> | \n'
        navigations_bar = navigations_bar + '<a href="/snapshots" title="Snapshots">Snapshots</a> | \n'
        navigations_bar = navigations_bar + '<a href="/elastic_ips" title="Elastic IPs">IPs</a> | \n'
        navigations_bar = navigations_bar + '<a href="/zonen" title="Availability Zones">Zones</a> | \n'
        navigations_bar = navigations_bar + '<a href="/securitygroups" title="Security Groups">Groups</a> | \n'
        navigations_bar = navigations_bar + '<a href="/s3" title="Simple Storage Service">S3</a> | \n'
        navigations_bar = navigations_bar + '<a href="/loadbalancer" title="Elastic Load Balancer">ELB</a> | \n'
        navigations_bar = navigations_bar + '<a href="/info" title="Info">Info</a> \n'
    return navigations_bar


def amazon_region(username):
    aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
    results = aktivezone.fetch(10)

    for result in results:
        if result.aktivezone in ("us-east-1", "eu-west-1", "us-west-1", "us-west-2", "ap-southeast-1", "ap-northeast-1", "sa-east-1"):
            # Hier wird einach nur der Text in result.aktivezone von runden Klammern umschlossen 
            zone_amazon = '(' + str(result.aktivezone) + ')'
        elif result.aktivezone in ("us_east", "us_west"):
            # Hier wird einach nur der Text in result.aktivezone von runden Klammern umschlossen 
            zone_amazon = '(' + str(result.aktivezone) + ')'
        else:
            zone_amazon = ""

    return zone_amazon
  
  
def zonen_liste_funktion(username,sprache,mobile):
    testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db", username_db=username)
    # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
    # Wie viele Einträge des Benutzers sind schon vorhanden?
    anzahl = testen.count()
    # Alle Einträge des Benutzers holen?
    results = testen.fetch(100)

    zonen_liste = ''
    if anzahl:
        zonen_liste = zonen_liste + '<form action="/regionwechseln" method="post" accept-charset="utf-8">'
        zonen_liste = zonen_liste + '<input type="hidden" name="mobile" value="'+mobile+'">'
        zonen_liste = zonen_liste + '<select name="regionen" size="1">'
        for test in results:
            zonen_liste = zonen_liste + '<option>'
            if test.eucalyptusname == "Amazon":
                # Änderungen hier müssen auch in RegionWechseln.py berücksichtigt werden
                # Changes made in this List need to be done in RegionWechseln.py too
                zonen_liste = zonen_liste + 'EC2 US East Virginia'
                zonen_liste = zonen_liste + '</option>'
                zonen_liste = zonen_liste + '<option>'
                zonen_liste = zonen_liste + 'EC2 US West N.California'
                zonen_liste = zonen_liste + '</option>'
                zonen_liste = zonen_liste + '<option>'
                zonen_liste = zonen_liste + 'EC2 US West Oregon'
                zonen_liste = zonen_liste + '</option>'
                zonen_liste = zonen_liste + '<option>'
                zonen_liste = zonen_liste + 'EC2 EU West Ireland'
                zonen_liste = zonen_liste + '</option>'
                zonen_liste = zonen_liste + '<option>'
                zonen_liste = zonen_liste + 'EC2 AP Singapore'
                zonen_liste = zonen_liste + '</option>'
                zonen_liste = zonen_liste + '<option>'
                zonen_liste = zonen_liste + 'EC2 AP Tokyo'
                zonen_liste = zonen_liste + '</option>'
                zonen_liste = zonen_liste + '<option>'
                zonen_liste = zonen_liste + 'EC2 S.America Sao Paulo'
            elif test.eucalyptusname == "HP":
                # Änderungen hier müssen auch in RegionWechseln.py berücksichtigt werden
                # Changes made in this List need to be done in RegionWechseln.py too
                #zonen_liste = zonen_liste + 'HP US East'
                #zonen_liste = zonen_liste + '</option>'
                #zonen_liste = zonen_liste + '<option>'
                zonen_liste = zonen_liste + 'HP US West'
            else:
                #zonen_liste = zonen_liste + 'Eucalyptus'
                #zonen_liste = zonen_liste + ' ('
                zonen_liste = zonen_liste + str(test.eucalyptusname)
                #zonen_liste = zonen_liste + ')'
            zonen_liste = zonen_liste + '</option>'
        zonen_liste = zonen_liste + '</select>'
        zonen_liste = zonen_liste + '&nbsp;'
        if sprache == "de":
            zonen_liste = zonen_liste + '<input type="submit" value="Region wechseln">'
        else:
            zonen_liste = zonen_liste + '<input type="submit" value="switch to region">'
        zonen_liste = zonen_liste + '</form>'
    else:
        zonen_liste = ''

    return zonen_liste
  

# Hilfsfunktion für die Formatierung der grünen Fehlermeldungen
def format_error_message_green(input_error_message):
    if input_error_message:
        return "<font color='green'>%s</font><p>&nbsp;</p>" % (input_error_message)
    else:
        return ""

# Hilfsfunktion für die Formatierung der roten Fehlermeldungen
def format_error_message_red(input_error_message):
    if input_error_message:
        return "<font color='red'>%s</font><p>&nbsp;</p>" % (input_error_message)
    else:
        return ""
      
def loginelb(username):
  # Die Zugangsdaten des Benutzers holen
  aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

  for db_eintrag in aktivezone:
    zoneinderdb = db_eintrag.aktivezone

    if zoneinderdb in ("us-east-1", "eu-west-1", "us-west-1", "us-west-2", "ap-southeast-1", "ap-northeast-1", "sa-east-1"):
      aktuellezone = "Amazon"
    else:
      aktuellezone = zoneinderdb


  if aktivezone:
    # In der Spalte "eucalyptusname_db" steht entweder "Amazon" oder der Eucalyptus-Name der Private Cloud
    zugangsdaten = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db=aktuellezone)

    for db_eintrag in zugangsdaten:
      accesskey = db_eintrag.accesskey
      secretaccesskey = db_eintrag.secretaccesskey
      endpointurl = db_eintrag.endpointurl
      port = db_eintrag.port


    if zoneinderdb in ("us-east-1", "eu-west-1", "us-west-1", "us-west-2", "ap-southeast-1", "ap-northeast-1", "sa-east-1"):   
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_elb = boto.ec2.elb.connect_to_region(zoneinderdb,
                              aws_access_key_id=accesskey,
                              aws_secret_access_key=secretaccesskey,
                              is_secure=True,
                              validate_certs=False,
                              #port=8773,
                              path="/")
      regionname = aktuellezone
    else:
      regionname = "---"
  else:
    regionname = "---"
  return conn_elb

def logins3(username):
  # Die Zugangsdaten des Benutzers holen
  aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)

  for db_eintrag in aktivezone:
    zoneinderdb = db_eintrag.aktivezone
    if zoneinderdb in ("us-east-1", "eu-west-1", "us-west-1", "us-west-2", "ap-southeast-1", "ap-northeast-1", "sa-east-1"):
      aktuellezone = "Amazon"
    else:
      aktuellezone = zoneinderdb


  if aktivezone:
    # In der Spalte "eucalyptusname_db" steht entweder "Amazon" oder der Eucalyptus-Name der Private Cloud
    zugangsdaten = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :eucalyptusname_db", username_db=username, eucalyptusname_db=aktuellezone)

    for db_eintrag in zugangsdaten:
      accesskey = db_eintrag.accesskey
      secretaccesskey = db_eintrag.secretaccesskey
      endpointurl = db_eintrag.endpointurl
      port = db_eintrag.port

    if zoneinderdb in ("us-east-1", "eu-west-1", "us-west-1", "us-west-2", "ap-southeast-1", "ap-northeast-1", "sa-east-1"):
      calling_format=boto.s3.connection.OrdinaryCallingFormat()
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
                                        aws_secret_access_key=secretaccesskey,
                                        is_secure=False,
                                        validate_certs=False,
                                        host="s3.amazonaws.com",
                                        calling_format=calling_format,
                                        path="/")

      regionname = aktuellezone
    elif zoneinderdb in ("us_east", "us_west"):
      calling_format=boto.s3.connection.OrdinaryCallingFormat()
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
                                        aws_secret_access_key=secretaccesskey,
                                        is_secure=True,
                                        validate_certs=False,
                                        host="region-a.geo-1.objects.hpcloudsvc.com/v1/17981992107691",
                                        calling_format=calling_format,
                                        path="/services/Cloud/")

      regionname = aktuellezone
    elif zoneinderdb == "GoogleStorage":
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      calling_format=boto.s3.connection.OrdinaryCallingFormat()
      conn_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
                                    aws_secret_access_key=secretaccesskey,
                                    is_secure=False,
                                    validate_certs=False,
                                    host="commondatastorage.googleapis.com",
                                    calling_format=calling_format,
                                    path="/")

      regionname = aktuellezone
    elif zoneinderdb == "HostEuropeCloudStorage":
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      calling_format=boto.s3.connection.OrdinaryCallingFormat()
      conn_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
                                    aws_secret_access_key=secretaccesskey,
                                    is_secure=False,
                                    validate_certs=False,
                                    host="cs.hosteurope.de",
                                    calling_format=calling_format,
                                    path="/")

      regionname = aktuellezone
    elif zoneinderdb == "DunkelCloudStorage":
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      calling_format=boto.s3.connection.OrdinaryCallingFormat()
      conn_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
                                    aws_secret_access_key=secretaccesskey,
                                    is_secure=True,
                                    validate_certs=False,
                                    host="dcs.dunkel.de",
                                    calling_format=calling_format,
                                    path="/")

      regionname = aktuellezone
    else:
      port = int(port)
      calling_format=boto.s3.connection.OrdinaryCallingFormat()
      secretaccesskey_base64decoded = base64.b64decode(str(secretaccesskey))
      secretaccesskey = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))
      conn_s3 = boto.s3.connection.S3Connection(aws_access_key_id=accesskey,
                                        aws_secret_access_key=secretaccesskey,
                                        is_secure=False,
                                        validate_certs=False,
                                        host=endpointurl,
                                        port=port,
                                        calling_format=calling_format,
                                        path="/services/Walrus")

      regionname = aktuellezone
  else:
    regionname = "---"
  return conn_s3

def aws_access_key_erhalten(username,regionname):
  Anfrage_nach_AWSAccessKeyId = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :regionname_db", username_db=username, regionname_db=regionname)
  for db_eintrag in Anfrage_nach_AWSAccessKeyId:
    AWSAccessKeyId = db_eintrag.accesskey

  return AWSAccessKeyId

def aws_secret_access_key_erhalten(username,regionname):
  Anfrage_nach_AWSSecretAccessKeyId = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :regionname_db", username_db=username, regionname_db=regionname)
  for db_eintrag in Anfrage_nach_AWSSecretAccessKeyId:
    AWSSecretAccessKeyId = db_eintrag.secretaccesskey
    secretaccesskey_base64decoded = base64.b64decode(str(AWSSecretAccessKeyId))
    AWSSecretAccessKeyId = xor_crypt_string(secretaccesskey_base64decoded, key=str(username))

  return AWSSecretAccessKeyId

def endpointurl_erhalten(username,regionname):
  Anfrage_nach_endpointurl = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :regionname_db", username_db=username, regionname_db=regionname)
  for db_eintrag in Anfrage_nach_endpointurl:
    endpointurl = db_eintrag.endpointurl

  return endpointurl


def port_erhalten(username,regionname):
  Anfrage_nach_port = db.GqlQuery("SELECT * FROM KoalaCloudDatenbank WHERE user = :username_db AND eucalyptusname = :regionname_db", username_db=username, regionname_db=regionname)
  for db_eintrag in Anfrage_nach_port:
    port = db_eintrag.port

  return port

def zugangstyp_erhalten(username):
  Anfrage_nach_zugangstyp = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
  for db_eintrag in Anfrage_nach_zugangstyp:
    zugangstyp = db_eintrag.zugangstyp

  return zugangstyp




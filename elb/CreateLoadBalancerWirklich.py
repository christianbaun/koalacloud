#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import re

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api.urlfetch import DownloadError
from google.appengine.ext import db

from library import loginelb
from library import login

from boto.ec2.connection import *

class CreateLoadBalancerWirklich(webapp.RequestHandler):
    def post(self):
        mobile = self.request.get('mobile')
        if mobile != "true":
            mobile = "false"
        elb_name = self.request.get('elb_name')
        elb_protokoll = self.request.get('elb_protokoll')
        ELBPort = self.request.get('ELBPort')
        InstPort = self.request.get('InstPort')
        useast1a = self.request.get('us-east-1a') # Virginia
        useast1b = self.request.get('us-east-1b')
        useast1c = self.request.get('us-east-1c')
        useast1d = self.request.get('us-east-1d')
        useast1e = self.request.get('us-east-1e')
        uswest1a = self.request.get('us-west-1a') # Northern California
        uswest1b = self.request.get('us-west-1b')
        uswest1c = self.request.get('us-west-1c')
        uswest2a = self.request.get('us-west-2a') # Oregon
        uswest2b = self.request.get('us-west-2b')
        uswest2c = self.request.get('us-west-2c')
        euwest1a = self.request.get('eu-west-1a') # Irland
        euwest1b = self.request.get('eu-west-1b')
        euwest1c = self.request.get('eu-west-1c')
        apsoutheast1a = self.request.get('ap-southeast-1a') # Singapur
        apsoutheast1b = self.request.get('ap-southeast-1b')
        apnortheast1a = self.request.get('ap-northeast-1a') # Tokio
        apnortheast1b = self.request.get('ap-northeast-1b')
        saeast1a = self.request.get('sa-east-1a') # Sao Paulo
        saeast1b = self.request.get('sa-east-1b')

        # Der Name muss ein String sein
        elb_name = str(elb_name)
        # Das Protokoll muss ein String sein
        elb_protokoll = str(elb_protokoll)

        # Den Usernamen erfahren
        username = users.get_current_user()

        conn_region, regionname = login(username)

        # Nachsehen, wo wir sind
        aktivezone = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankAktiveZone WHERE user = :username_db", username_db=username)
        results = aktivezone.fetch(100)

        for db_eintrag in aktivezone:
          aktivezone = db_eintrag.aktivezone


        if ELBPort.isdigit() == False:
          # Testen ob der Load Balancer Port eine Zahl ist
          # Wenn nicht ausschließlich eine Zahl eingegeben wurde sondern evtl. Buchstaben oder Sonderzeichen
          fehlermeldung = "55"
          self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          # Der Load Balancer Port muss ein Integer sein
          ELBPort = int(ELBPort)

        if InstPort.isdigit() == False:
          # Testen ob der EC2 Instanz Port eine Zahl ist
          # Wenn nicht ausschließlich eine Zahl eingegeben wurde sondern evtl. Buchstaben oder Sonderzeichen
          fehlermeldung = "56"
          self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:
          # Der EC2 Instanz Port muss ein Integer sein
          InstPort = int(InstPort)

        if elb_name == "":
          # Testen ob ein Name für den neue ELB angegeben wurde
          fehlermeldung = "50"
          self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif re.search(r'[^\-a-zA-Z0-9]', elb_name) != None:
          # Überprüfen, ob der name nur erlaubte Zeichen enthält
          # Die Zeichen - und a-zA-Z0-9 sind erlaubt. Alle anderen nicht. Darum das ^
          fehlermeldung = "51"
          self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif InstPort == "" and ELBPort == "":
          # Testen ob ein Load Balancer Port und ein EC2 Instanz Port für den neue ELB angegeben wurde
          fehlermeldung = "54"
          self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif ELBPort == "":
          # Testen ob ein Load Balancer Port für den neue ELB angegeben wurde
          fehlermeldung = "52"
          self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif InstPort == "":
          # Testen ob ein EC2 Instanz Port für den neue ELB angegeben wurde
          fehlermeldung = "53"
          self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif aktivezone == "us-east-1" and useast1a == "" and useast1b == "" and useast1c == "" and useast1d == "":
          # Testen ob mindestens eine Zone angegeben wurde
          fehlermeldung = "58"
          self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif aktivezone == "us-west-1" and uswest1a == "" and uswest1b == "":
          # Testen ob mindestens eine Zone angegeben wurde
          fehlermeldung = "58"
          self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif aktivezone == "eu-west-1" and euwest1a == "" and euwest1b == "":
          # Testen ob mindestens eine Zone angegeben wurde
          fehlermeldung = "58"
          self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif aktivezone == "ap-southeast-1" and apsoutheast1a == "" and apsoutheast1b == "":
          # Testen ob mindestens eine Zone angegeben wurde
          fehlermeldung = "58"
          self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif not (ELBPort == 80 or ELBPort == 443 or (1024 <= ELBPort <= 65535)):
          # Testen ob ein korrekter Port für den Load Balancer Port angegeben wurde
          # Load Balancer port must be either 80, 443 or 1024~65535 inclusive
          fehlermeldung = "59"
          self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        elif InstPort >= 65535:
          # Testen ob ein korrekter Port für den EC2 Instanz Port angegeben wurde
          # Member must have value less than or equal to 65535
          fehlermeldung = "60"
          self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
        else:

          conn_elb = loginelb(username) # Mit ELB verbinden

          zones_elb = []
          if aktivezone == "us-east-1":
            if useast1a != "":
              zones_elb.append('us-east-1a')
            if useast1b != "":
              zones_elb.append('us-east-1b')
            if useast1c != "":
              zones_elb.append('us-east-1c')
            if useast1d != "":
              zones_elb.append('us-east-1d')
            if useast1e != "":
              zones_elb.append('us-east-1e')
          if aktivezone == "us-west-1":
            if uswest1a != "":
              zones_elb.append('us-west-1a')
            if uswest1b != "":
              zones_elb.append('us-west-1b')
            if uswest1c != "":
              zones_elb.append('us-west-1c')
          if aktivezone == "us-west-2":
            if uswest2a != "":
              zones_elb.append('us-west-2a')
            if uswest2b != "":
              zones_elb.append('us-west-2b')
            if uswest2c != "":
              zones_elb.append('us-west-2c')
          if aktivezone == "eu-west-1":
            if euwest1a != "":
              zones_elb.append('eu-west-1a')
            if euwest1b != "":
              zones_elb.append('eu-west-1b')
            if euwest1c != "":
              zones_elb.append('eu-west-1c')
          if aktivezone == "ap-southeast-1":
            if apsoutheast1a != "":
              zones_elb.append('ap-southeast-1a')
            if apsoutheast1b != "":
              zones_elb.append('ap-southeast-1b')
          if aktivezone == "ap-northeast-1":
            if apnortheast1a != "":
              zones_elb.append('ap-northeast-1a')
            if apnortheast1b != "":
              zones_elb.append('ap-northeast-1b')
          if aktivezone == "sa-east-1":
            if saeast1a != "":
              zones_elb.append('sa-east-1a')
            if saeast1b != "":
              zones_elb.append('sa-east-1b')
          listeners_elb = []
          listeners_elb.append((ELBPort,InstPort,elb_protokoll))

          try:
            # Versuchen, den Load Balancer zu erzeugen
            neuer_loadbalancer = conn_elb.create_load_balancer(elb_name, zones_elb, listeners_elb)
          except EC2ResponseError:
            # Wenn es nicht geklappt hat...
            fehlermeldung = "57"
            self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
          except DownloadError:
            # Diese Exception hilft gegen diese beiden Fehler:
            # DownloadError: ApplicationError: 2 timed out
            # DownloadError: ApplicationError: 5
            fehlermeldung = "8"
            self.redirect('/create_load_balancer?mobile='+str(mobile)+'&message='+fehlermeldung)
          else:
            # Wenn es geklappt hat...
            fehlermeldung = "72"
            self.redirect('/loadbalancer?mobile='+str(mobile)+'&message='+fehlermeldung)
            
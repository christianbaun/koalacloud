#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp

class KoalaCloudDatenbank(db.Model):
    user = db.UserProperty(required=True)
    #input = db.IntegerProperty()
    regionname = db.StringProperty(required=True)
    endpointurl = db.StringProperty()
    port = db.StringProperty()
    eucalyptusname = db.StringProperty()
    zugangstyp = db.StringProperty()  # Amazon, Eucalyptus, Nimbus...
    accesskey = db.StringProperty(required=True)
    secretaccesskey = db.StringProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)

class KoalaCloudDatenbankAktiveZone(db.Model):
    user = db.UserProperty(required=True)
    aktivezone = db.StringProperty()
    zugangstyp = db.StringProperty()  # Amazon, Eucalyptus, Nimbus...

class KoalaCloudDatenbankSprache(db.Model):
    user = db.UserProperty(required=True)
    sprache = db.StringProperty()

class KoalaCloudDatenbankFavouritenAMIs(db.Model):
    user = db.UserProperty(required=True)
    zone = db.StringProperty(required=True)
    ami = db.StringProperty(required=True)
    
class KoalaQuickStartAMIs(db.Model):
    zone = db.StringProperty(required=True)
    ami = db.StringProperty(required=True)
#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp

from internal.Datastore import *

class Sprache(webapp.RequestHandler):
    def get(self):
        attributes = ''
        # Die ausgewählte Sprache holen
        # Get the chosen language
        lang = self.request.get('lang')
                  
        # Den Pfad holen
        # Get the path      
        path = self.request.get('path')
        if not path:
          path = ''
        
        mobile = self.request.get('mobile')
        if mobile == 'true':
          mobile_to_path = '?mobile=true'
        else:
          mobile_to_path = '?mobile=false'
                     
                          

        if path == 'snapshoterzeugen':
          volume = self.request.get('volume')
          if not volume:
            volume = ''
          attributes = '&volume='+volume

        if path == 'volumeanhaengen':
          volume = self.request.get('volume')
          if not volume:
            volume = ''
          zone = self.request.get('zone')
          if not zone:
            zone = ''            
          attributes = '&volume='+volume+'&zone='+zone

        if path == 'alle_keys_loeschen':
          s3_ansicht = self.request.get('s3_ansicht')
          if not s3_ansicht:
            s3_ansicht = ''
          bucket_name = self.request.get('bucket_name')
          if not bucket_name:
            bucket_name = ''            
          attributes = '&s3_ansicht='+s3_ansicht+'&bucket_name='+bucket_name
          

        
        if path == 'volumeaussnapshoterzeugen':
          snapshot = self.request.get('snapshot')
          if not snapshot:
            snapshot = ''
          attributes = '&snapshot='+snapshot

        if path == 'associate_address':
          address = self.request.get('address')
          if not address:
            address = ''
          attributes = '&address='+address

        if path == 'gruppenaendern':
          gruppe = self.request.get('gruppe')
          if not gruppe:
            gruppe = ''
          attributes = '&gruppe='+gruppe
          
        if path == 'loadbalanceraendern':
          name = self.request.get('name')
          if not name:
            name = ''
          attributes = '&name='+name
          
        if path == 'bucket_inhalt_pure':
          bucket = self.request.get('bucket')
          if not bucket:
            bucket = ''
          attributes = '&bucket='+bucket
          
        if path == 'bucket_inhalt':
          bucket = self.request.get('bucket')
          if not bucket:
            bucket = ''
          attributes = '&bucket='+bucket
          
          
        # Den Usernamen erfahren
        # Get the username
        username = users.get_current_user()

        if username:

          # Erst überprüfen, ob schon ein Eintrag dieses Benutzers vorhanden ist.
          testen = db.GqlQuery("SELECT * FROM KoalaCloudDatenbankSprache WHERE user = :username_db", username_db=username)

          # Wenn Einträge vorhanden sind, werden sie aus der DB geholt und gelöscht
          results = testen.fetch(100)

          for result in results:
            result.delete()

          logindaten = KoalaCloudDatenbankSprache(sprache=lang,
                                                  user=username)


          try:
            # In den Datastore schreiben
            # Write into the datastore
            logindaten.put()
          except:
            # Wenn es nicht klappt...
            # If it didn't work...
            self.redirect('/')
          else:
            # Wenn es geklappt hat...
            # If it worked...
            self.redirect('/'+path + mobile_to_path + attributes)
        else:
          self.redirect('/')

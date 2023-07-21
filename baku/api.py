# -*- coding: utf-8 -*

import requests
import logging
import json
import jwt
import os

BASE_URL = os.getenv("BASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

TOKEN = jwt.encode({
    "scopes": [{"pattern": f".*/api/collections"}], 
    "userkey": "0"
}, SECRET_KEY, algorithm="HS256")

##
#

class Document:

    def __init__(self, data, session):
        self.data = data
        self.id = data['id']
        self.session = session

    def __setattr__(self, name, value):
        self.__dict__[name] = value

    def __getattr__(self, name):
        self.__dict__[name]

    def save(self):
        return self.session.save(self.id, self.data)
    
    def remove(self):
        return self.session.remove(self.id)

##
#

class Collection(requests.Session):
   
    def __init__(self, name):
        self.name = name
        self.url = f"{BASE_URL}/api/collections/{name}"
        self.headers.update({"Authorization": f"Bearer {TOKEN}"})

    def findAll(self, criteria=None, order=None, created_at_min=None, created_at_max=None):

        params = {}

        if criteria is not None:
            params['criteria'] = json.dumps(criteria)

        if created_at_min is not None:
            params['created_at_min'] = created_at_min

        if created_at_max is not None:
            params['created_at_max'] = created_at_max

        logging.debug("finding in %s with %s", self.url, params)
       
        res = self.get(self.url, params=params)

        if res.status_code >= 400:
            raise Exception(f"{res.status_code}: {res.text}")

        return [Document(x, self) for x in res.json()]
    
    def findOne(self, criteria=None):

        data = self.findAll(criteria)

        if not data:
            raise Exception(f"Not data for {criteria} in ")
        
        return data[0]
    
    def create(self, data):

        logging.debug("creating in %s with %s", self.url, data)
       
        res = self.post(self.url, json=data)

        if res.status_code >= 400:
            raise Exception(f"{res.status_code}: {res.text}")

        return res.json()
    
    def save(self, id, data):

        logging.debug("updating in %s/%s with %s", self.url, id, data)
       
        res = self.put(f"{self.url}/{id}", json=data)

        if res.status_code >= 400:
            raise Exception(f"{res.status_code}: {res.text}")

        return res.json()
    
    def remove(self, id):

        logging.debug("removing in %s/%s", self.url, id)
       
        res = self.delete(f"{self.url}/{id}")

        if res.status_code >= 400:
            raise Exception(f"{res.status_code}: {res.text}")

        return res.json()

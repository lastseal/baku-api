# -*- coding: utf-8 -*

import requests
import logging
import json
import jwt
import os

COLLECTION_HOST = os.getenv("COLLECTION_HOST")

##
#

def search(name, params):
  
  scopes = [{"pattern": f"GET.*/api/collections/{name}"}] 
  token = jwt.encode({"scopes": scopes, "userkey": "none"}, SECRET_KEY, algorithm="HS256")
  
  res = requests.get(f"{COLLECTION_HOST}/api/collections/{name}", params=params, headers={
    "Authorization": f"Bearer {token}"
  })

  if res.status_code >= 400:
      raise Exception(f"{res.status_code}: {res.text}")

  return res.json()

##
#

def findOne(name, params):
  
  data = search(name, params)
  
  if not data:
      raise Exception(f"data not found for event {event}")

  return data[0]

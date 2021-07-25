#!/usr/bin/python3

import cgi
import subprocess
import pymongo
from pymongo import MongoClient

print("content-type:  text/html")
print()

fs = cgi.FieldStorage()
cmd = fs.getvalue("x")

output = subprocess.getoutput("sudo " + cmd)

print(output)

user = MongoClient("mongodb://{ mongodb__connection__string }:{ port__number }")  #aws ecs service i.e AWS ELB URL as MongoDB connection string

db = user['data']['cmd'].insert( { cmd : output } )

#! /usr/bin/env python
# *-* coding: iso-8859-1 *-*
""" 
Copyright © 2011, andres lozano aka loz
Copyleft: This work is free, you can redistribute it and / or modify it under the terms of the Free Art License. You can find a copy of this license on the site Copyleft Attitude well as http://artlibre.org/licence/lal/en on other sites.
"""

# script to convert data figure to coordinates
import sys
import os
import re
import math

def extension(val):
	"detect extension file"
	arr = val.split('.')
	result = arr.pop()
	return result

root = os.getcwd()
file,ext = sys.argv[0].split('.')
arguments = sys.argv

print file + ".py convert into hplot code (basic) \ncoordinated values established with plottermap.pdf schema, \ninto cartesian data (exemple-xy.baz) or polar data (exemple-ra.baz) \nby Andres aka Loz, 2011\nversion 0.0.8\n\n"
print "root: " + root +"\n"


alphabet = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","x","y","z",
"0","1","2","3","4","5","6","7","8","9"]

params = "rem * "

msg = """
o------- x
|
|
|
y
"""

print msg

# msg = raw_input("other rotation init value ? or default (value 0) [press return]: ")

msg = ""
div = 0

if msg != "" :
	try:
		div = int(msg)
	except:
		div = float(msg)
		
if div != 0:
	startAng = math.radians(div)
else:
	startAng = 0

initRot = "%.3f" % startAng

# print "\nyou choose " + str(div) + " degrees then init rot val in radians = " + str(initRot)

params += "factor " + str(div) + "degrees ;init rot radians:" + str(initRot) + ";"

xCoords = 35
yCoords = 35

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
msg = """
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
1) hgr mixed screen (text+image) image height max is 159px
basic space between points = 3.2
with 3.2 the square side = 112px (and image rotation fit screen) 
or with 4.4 the square side = 154px (the image fit fullscreen)

2) hgr2 fullscreen (only image) image height max is 189px
basic space between points = 3.8
with 3.8 the square side = 133px (and image rotation fit screen) 
or with 5.4 the square side = 189px (the image fit fullscreen)
"""

print msg

side = 3.2
 
msg = raw_input("choose other space between points? or default (3.2) [press return] : ")

if msg != "" :
	try:
		side = int(msg)
	except:
		side = float(msg)
		
AB = BC = side * 35 
AB2 = BC2 = AB * AB
AC = math.sqrt( AB2 + BC2 )
params += "dist:" + str(side) + ";width:" + str( int(AB)) + ";diagVal:" +  str( int(AC) ) + ";halfdiag:" + str( int(AC / 2) ) + ";"
print "\nyou choose distance " + str(side) + " => height & witdh values are " + str(35 * side) + "px"

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
print "\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
msg = raw_input("choose source plot code file ! or cancel [press return]: ")

if msg == "" :
	print "\ncanceled\n"
	sys.exit(0)
	
ficimport = ""
if extension(msg) == "baz":
	ficimport = msg
	arr = msg.split('.')
	ext = arr.pop()
	myfileWithoutExt = ".".join(arr)
else:
	ficimport = msg + ".baz"
	myfileWithoutExt = msg

print "you choose "+ ficimport + "\n"
msg = raw_input("choose file name for .....-ra.baz et .....-xy.baz ? \nor default(" + myfileWithoutExt + "-ra.baz " + myfileWithoutExt + "-xy.baz) [press return]: ")

ficexport = ""
if msg != "" :
	ficexport = msg
else:
	ficexport,ext = ficimport.split(".")

params += "fic:" + ficimport + ";\n"
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

sideX = sideY = side

i = 0;j = 0
cartesianMap = {}
polarMap = {}

while i < yCoords:
	while j < xCoords:
		key = alphabet[i] + alphabet[j]
		
		distX = (sideX * j);
		distY = (sideY * i);
		
		distX = "%d" % distX
		distY = "%d" % distY
		
		cartesianMap[key]  = "x2= x1+" + str(distX) + ":"
		cartesianMap[key] += "y2= y1+" + str(distY) + ":"
		cartesianMap[key] += "gosub @checkxy:"
		
		distXrot = int(distX)
		distYrot = int(distY)
		
		rayon = math.sqrt( (distXrot * distXrot) + (distYrot * distYrot) )
		angle = math.atan2( distXrot, distYrot )
		
		# ajust rotation
		angle = angle + startAng
		
		rayon = "%.2f" % rayon
		angle = "%.2f" % angle
		
		# av = angle variation
		polarMap[key]  = "x2= (x1+(" + str(rayon) + "*sin(" + str(angle) + "+av))):"
		polarMap[key] += "y2= (y1+(" + str(rayon) + "*cos(" + str(angle) + "+av))):"
		polarMap[key] += "gosub @checkxy:"
		j +=1
	j = 0
	i +=1

# ********************************************************************************************************************************************* #
# coordonnées de l'image, vectorielles
fileData = []
linesfic = []

try:
	f = open(ficimport,"r")
	linesfic = f.readlines()
	f.close()
except:
	print "file not exist"
	sys.exit(0)
	
comments = re.compile("^\s*\#")
emptyLines = re.compile("^\s*$")

lines = []
for line in linesfic:
	if not ( comments.search(line) or emptyLines.search(line) ):
		if line[-1] == '\n': line = line[:-1]
		line = line.lower()
		tmp = line.split(" ")
		fileData.append(tmp)

# exterior frame
# fileData.append("aa a9 99 9a aa".split(" "))
# fileData.append("hh h2 22 2h hh".split(" "))

# inner frame
# fileData.append("qr sr".split(" "))
# fileData.append("rq rs".split(" "))

code = params;i = 1
for arr in fileData:
	for element in arr:
		if element != "":
			code += polarMap[element]
			if i == 1:
				code +="hplot x2,y2"
			else:
				code += "hplot to x2,y2"
				
			if "i" in arguments:
				code += ":rem "+element
				
			code += "\n"
		i += 1
	i = 1

fichier = root + "/" + ficexport + "-ra.baz"
f = open(fichier,"w")
f.write(code)
f.close()
print "polar data     => " + ficexport + "-ra.baz"

# ********************************************************************************************************************************************* #
code = params;i = 1
for arr in fileData:
	for element in arr:
		if element != "":
			code += cartesianMap[element]
			if i == 1:
				code +="hplot x2,y2"
			else:
				code += "hplot to x2,y2"
				
			if "i" in arguments:
				code += ":rem "+element
				
			code += "\n"
		i += 1
	i = 1

fichier = root + "/" + ficexport + "-xy.baz"
f = open(fichier,"w")
f.write(code)
f.close()
print "\ncartesian data => " + ficexport + "-xy.baz"

print "process done"

#! /usr/bin/env python
# *-* codhttps://www.facebook.com/?sk=h_chring: iso-8859-1 *-*
"""
Virtual Basic tool version 0.2.1 
Copyright  2011, andres lozano aka loz
Copyleft: This work is free, you can redistribute it and / or modify it
under the terms of the Free Art License. You can find a copy of this license
on the site Copyleft Attitude well as http://artlibre.org/licence/lal/en on other sites.
"""

# fonctions ******************************************************************
def printcode(lignes=[]):
    print ("".join(lignes))


def extension(val):
    "detect extension file"
    arr = val.split('.')
    result = arr.pop()
    return result

# actions ********************************************************************	
import virtualbasic as vir
import sys
import os
import re
import argparse
from time import gmtime, strftime
import pprint
import logging
import time


parser = argparse.ArgumentParser()
parser.add_argument("infile", help="The VirtualBasic source file to convert")
parser.add_argument("-o","--outfile", help="The file to write the AppleSoft source to (default: infile.bas)")
parser.add_argument("-c","--compact",help="Compact the BASIC code",action="store_true")
parser.add_argument("-u","--ultracompact",help="Ultracompact the BASIC code",action="store_true")
parser.add_argument("-remgo","--remgosubcomments",help="Add REM->GO SUB-NAME comment",action="store_true")
parser.add_argument("-l","--loz",help="Add loz's signature to the output file",action="store_true")
parser.add_argument("-D","--define", help="Define a symbol",action="append")
args = parser.parse_args()

# Open logger based on the in filename



myFullPath = os.path.realpath(args.infile)
(mypath,myfile) = os.path.split(myFullPath)
print("Root dir: " + mypath)

(myfileWithoutExt,myext) = os.path.splitext(myfile)

logger = logging.getLogger('VirtualBasic')
logger.setLevel(logging.INFO)
# Write to a file as well
log_file_name = os.path.join(mypath, myfileWithoutExt + '.log')
file_handler = logging.FileHandler(log_file_name, mode='w')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.info("{0} Compiling {1}".format(time.strftime('%c'),args.infile))

try:
    f = open(args.infile,"r")
    lignes = f.readlines()
    f.close()
except Exception as e:
    logger.fatal("Error reading source file {0}: {1}".format(myFullPath, str(e)))
    sys.exit(0)


# print "myfileWithoutExt: " + myfileWithoutExt + " myext"  + myext
bas = vir.Basic(lignes,args,myfileWithoutExt)
bas.root = mypath
codeBasic = bas.basic()
# messages = bas.msg


myfile = ""
if (args.outfile):
    myfile = args.outfile
else: 
    myfile = os.path.join(mypath,myfileWithoutExt + ".bas")

# myfile = root + "/"+ myfileWithoutExt + ".bas"
logger.info("Writing to: " + myfile)

f = open(myfile,"w")
f.write( codeBasic)
f.close()
# messages += "\nFile created: " + myfile

# record errors
gotosKeys = bas.gotos.keys()
gotosKeys.sort
# callsResult = "Goto, Gosub not found:\n"

# Follwing is broken.
# for myKey in gotosKeys:
#    if (bas.appels.has_key(myKey) == False):
#        # callsResult += myKey.lower() + "\n"
#        logger.error("Goto or gosub not found: {0}".format(myKey.lower()))

# logger.info("Complete at {0}".format(time.strftime('%c')))

#if not os.path.exists('logs'):
#    os.makedirs('logs',o755)

#myfile = mypath + "/logs/" + myfileWithoutExt + ".txt"
#f = open(myfile,"w")
#f.write(callsResult)
#f.close()

#print(messages)




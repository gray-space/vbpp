#! /usr/bin/env python
# *-* coding: iso-8859-1 *-*
"""
basic to virtual basic tool version 0.0.4
Copyright © 2012, andres lozano aka loz
Copyleft: This work is free, you can redistribute it and / or modify it
under the terms of the Free Art License. You can find a copy of this license
on the site Copyleft Attitude well as http://artlibre.org/licence/lal/en on other sites.
"""

import virtualbasic as vir
import sys
import os
import re
from time import gmtime, strftime

root = os.getcwd()
rootpath = root.split(os.sep)
currentdir = rootpath.pop()

#myfile = raw_input("pwd=" + root + "\nenter applesoft basic file name to analyse ? or [press return] to exit: ")

if len(sys.argv) < 2 or len(sys.argv) > 3:
	print "Requires one or two filenames."
	sys.exit(0)

	
 
#if myfile == "": sys.exit(0)
infile = sys.argv[1]
print "infile is: " + infile


try:
	f = open(infile,"r")
	lines = f.readlines()
	f.close()
except:
	print "file not found !"
	sys.exit(0)

code = vir.BasToBaz(lines)
text = code.toVirtual()

# Changed hardcoded backslash to os.sep for cross-pathform goodness.

if len(sys.argv) == 3:
	outfile = sys.argv[2]
else:
	outfile = root + os.sep + infile[:-4] + "_to.baz"

#myfile = root + os.sep + myfile[:-4] + "_to.baz"
print "process done\nconverted to " + outfile
f = open(outfile,"w")
f.write(text)
f.close()



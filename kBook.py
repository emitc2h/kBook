#!/usr/bin/env python

##########################################################
## kBook.py                                             ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : Main executable of kBook               ##
##                                                      ##
##########################################################

from core.commandline import CommandLine
import logging, time

## Create and configure logging services
logging.basicConfig(
	filename="log.%s.txt" % time.strftime("%Y-%m-%d_%H-%M-%S"),
	filemode='w',
	format='%(levelname) - 8s : %(message)s',
	level=logging.DEBUG
	)

## Also print to terminal
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('kBook > %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

the_commandline = CommandLine()
the_commandline.run()



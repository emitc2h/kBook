#!/usr/bin/env python

##########################################################
## kBook.py                                             ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : Main executable of kBook               ##
##                                                      ##
##########################################################

import logging, time, pickle, argparse
from core.commandline import CommandLine
from core.preferences import Preferences

## - - - - - - - - - - - - - - - - - - - - - - - - 
## Handle arguments

parser = argparse.ArgumentParser()
parser.add_argument('--scriptmode', default='', dest='commands', help='runs kBook in script mode command1 arg1;command2 arg2; ...')
args = parser.parse_args()

## - - - - - - - - - - - - - - - - - - - - - - - - 
## Loading preferences (or creating)

try:
	preferences_file = open('.kPrefs')
	preferences = pickle.load(preferences_file)
	preferences_file.close()
except IOError:
	print 'Creating new preferences (with default values) ...'
	preferences = Preferences()
except EOFError:
	print 'WARNING: preferences weren\'t saved correctly (unrecoverable), creating new preferences ...'
	preferences = Preferences()

preferences.update()

## - - - - - - - - - - - - - - - - - - - - - - - - 
## Create and configure logging services

if preferences.dated_log_file:
	log_file_name = 'log.{0}.txt'.format(time.strftime("%Y-%m-%d_%H-%M-%S"))
else:
	log_file_name = 'log.txt'

if preferences.write_log_file:
	logging.basicConfig(
		filename=log_file_name,
		filemode='w',
		format='%(levelname) - 8s : %(message)s',
		level=getattr(logging, preferences.log_file_level)
		)

	## Also print to terminal
	console = logging.StreamHandler()
	console.setLevel(logging.DEBUG)
	formatter = logging.Formatter('kBook : %(message)s')
	console.setFormatter(formatter)
	logging.getLogger('').addHandler(console)
else:
	logging.basicConfig(
		format='kBook : %(message)s',
		level=logging.DEBUG
		)


the_commandline = CommandLine(preferences)
if not args.commands:
	the_commandline.run()
else:
	the_commandline.execute(args.commands)



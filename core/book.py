##########################################################
## book.py                                              ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : The main kBook class, dealing with the ##
##               user interface                         ##
##########################################################

import os, shutil, sys, subprocess, readline, pickle, time
import logging as log
from subprocess import Popen, PIPE
from chain import Chain
from preferences import Preferences
from navigable import Navigable
from pandatools import PsubUtils

## =======================================================
class Book(Navigable):
	"""
	The kBook user interface
	"""


	## -------------------------------------------------------
	def __init__(self, name, preferences):
		"""
		Constructor
		"""

		Navigable.__init__(self, name, None, '')

		self.path             = '.book'
		self.cwd              = ''
		self.preferences      = preferences
		self.location         = self

		self.private += [
			'prepare',
			'preferences',
			'submit',
			'save_preferences',
			'save_chain',
			'save_chains',
			'create_chain',
			'submit',
			'location'
		]

		self.level = 0


	## --------------------------------------------------------
	def prepare(self):
		"""
		prepare kBook, load chains, check environment
		"""

		log.info('Preparing ...')
		log.info('')

		## Make the path absolute
		self.cwd = os.getcwd()
		self.path = os.path.join(self.cwd, self.path)

		## - - - - - - - - - - - - - - - - - - - - - - - - 
		## Make books directory if it doesn't exist
		log.debug('Checking that \'books\' directory is there ...')

		try:
			os.mkdir(self.path)
			log.debug('    ... created')
		except OSError:
			log.debug('    ... already created')
			pass
		log.debug('')


		## - - - - - - - - - - - - - - - - - - - - - - - - 
		## Check that PANDA is setup correctly
		log.debug('Checking PANDA setup ...')

		## Terminate program, kBook cannot operate without a proper PANDA setup
		if (not os.environ.has_key('PANDA_SYS')) or (not os.environ.has_key('PATHENA_GRID_SETUP_SH')):
			log.error('    Environment variables PANDA_SYS and/or PATHENA_GRID_SETUP_SH not set, please setup the panda tools (setupATLAS; localSetupPandaClient). Exiting.')
			sys.exit()
		else:
			log.debug('    ... correctly set')
		log.debug('')


		## - - - - - - - - - - - - - - - - - - - - - - - - 
		## Check that there is a grid proxy
		log.debug('Checking grid proxy ...')
		p = Popen(args = 'voms-proxy-info', stdout=PIPE, stderr=PIPE, shell = True)
		p.wait()
		pout_voms, perr_voms = p.communicate()
 
		if pout_voms.find('subject') == -1:
			log.error('    Grid proxy is not set, setup now:')
			PsubUtils.checkGridProxy('',True,False)
 
		pout_voms_lines = pout_voms.rstrip('\n').split('\n')

		for line in pout_voms_lines:
			log.debug('    ' + line)
		log.debug('')


		## - - - - - - - - - - - - - - - - - - - - - - - - 
		## Update book
		if self.preferences.update_on_start:
			log.debug('Updating everything ...')
			self.update()
			log.debug('')


		## - - - - - - - - - - - - - - - - - - - - - - - - 
		## Show preferences
		log.debug('The current preferences are:')
		self.preferences.print_all()

		self.location = self


	## --------------------------------------------------------
	def save_preferences(self):
		"""
		Saves the preferences to the current directory
		"""

		os.chdir(self.cwd)
		preferences_file = open('.kPrefs', 'w')
		pickle.dump(self.preferences, preferences_file)
		preferences_file.close()


	## --------------------------------------------------------
	def create_chain(self, name, chain_type, input_file_path, panda_options, **kwargs):
		"""
		Create a chain
		"""

		chain_path = os.path.join(self.path, '{0}_v0'.format(name))

		try:
			os.mkdir(chain_path)
		except OSError:
			log.error('Could not create chain with name {0}, another chain with the same name already exists.'.format(name))
			return


		new_chain = Chain(name, self, panda_options, chain_path, chain_type, input_file_path, **kwargs)
		self.append(new_chain)







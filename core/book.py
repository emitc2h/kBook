##########################################################
## book.py                                              ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : The main kBook class, dealing with the ##
##               user interface                         ##
##########################################################

import os, sys, subprocess
import logging as log
from subprocess import Popen, PIPE
from chain import Chain

## =======================================================
class Book:
	"""
	The kBook user interface
	"""


	## -------------------------------------------------------
	def __init__(self):
		"""
		Constructor
		"""

		log.info('='*40)
		log.info('Welcome to kBook 2.0.0!')
		log.info('-'*40)

		self.chains = []
		self.path   = 'books'
		self.cwd    = ''

		self.prepare()


	## --------------------------------------------------------
	def prepare(self):
		"""
		prepare kBook, load chains, check environment
		"""

		log.info('Preparing ...')

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

		p = Popen(args = 'echo $PANDA_SYS', stdout=PIPE, shell = True)
		pout_pan1 = p.communicate()[0]

		p = Popen(args = 'echo $PATHENA_GRID_SETUP_SH', stdout=PIPE, shell = True)
		pout_pan2 = p.communicate()[0]

		## Terminate program, kBook cannot operate without a proper PANDA setup
		if pout_pan1 == '\n' or pout_pan2 == '\n':
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
			log.error('    Grid proxy is not set, (voms-proxy-init -voms atlas), Exiting.')
			sys.exit()
 
		pout_voms_lines = pout_voms.rstrip('\n').split('\n')

		for line in pout_voms_lines:
			log.debug('    ' + line)
		log.debug('')
 



	## --------------------------------------------------------
	def run(self):
		"""
		runs the user interface
		"""


	## --------------------------------------------------------
	def create_chain(self):
		"""
		Create a new chain
		"""





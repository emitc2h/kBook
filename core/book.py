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
		self.download_path    = 'downloads'
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
			'location',
			'acquire_crontab',
			'add_to_crontab',
			'clean_crontab',
			'list_of_attributes'
		]

		self.level = 0


	## --------------------------------------------------------
	def prepare(self, preferences):
		"""
		prepare kBook, load chains, check environment
		"""

		log.info('Preparing ...')
		log.info('')

		## Assign external preferences
		self.preferences = preferences

		## Make the path absolute
		self.cwd = os.getcwd()
		self.path = os.path.join(self.cwd, self.path)
		self.download_path = os.path.join(self.cwd, self.download_path)

		## - - - - - - - - - - - - - - - - - - - - - - - - 
		## Make directories if they don't exist
		log.debug('Checking that \'.book\' directory is there ...')

		try:
			os.mkdir(self.path)
			log.debug('    ... created')
		except OSError:
			log.debug('    ... already created')
			pass
		log.debug('')


		log.debug('Checking that \'download\' directory is there ...')
		try:
			os.mkdir(self.download_path)
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

		proxy_is_expired = False

		for line in pout_voms_lines:
			if 'timeleft' in line:
				if '00:00:00' in line: proxy_is_expired = True
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

		return proxy_is_expired


	## --------------------------------------------------------
	def acquire_crontab(self):
		"""
		Acquire cron jobs
		"""

		p = Popen(args='acrontab -l', stdout=PIPE, stderr=PIPE, shell=True)
		p.wait()
		pout, perr = p.communicate()
		pout += '\n' + perr

		return pout


	## --------------------------------------------------------
	def add_to_crontab(self, arg):
		"""
		Add a job to the crontab to follow-up jobs automatically
		"""

		## Obtain current machine
		lxplus_node = os.environ['HOSTNAME']

		## Schedule the first cron job 2 minutes from now
		minutes = time.ctime(time.time())
		minute = int(minutes.split(' ')[-2].split(':')[1]) + 2

		if minute > 60:
			minute -= 60

		crontab = self.acquire_crontab()

		updated_crontab = open('crontab.tmp', 'w')
		for line in crontab.split('\n'):
			if './kBook.py' in line:
				log.info('track : A kBook cron job already exists in the crontab:')
				log.info('{0}'.format(line))
				overwrite = raw_input('kBook : track : Overwrite? (y/n) > ')
				if not overwrite == 'y':
					log.info('Will not overwrite current cron job.')
					return
				else:
					continue
			if line:
				updated_crontab.write('{0}\n'.format(line))

		cronjob = '{0} * * * * {1} export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase/; source $ATLAS_LOCAL_ROOT_BASE/packageSetups/atlasLocalPandaClientSetup.sh; cd /afs/cern.ch/user/m/mtm/kBook; ./kBook.py --scriptmode="{2}"\n'.format(minute, lxplus_node, ';'.join(['update', 'retry', arg]))

		log.info('Adding the following cron job to the cron tab:')
		log.info(cronjob)

		updated_crontab.write(cronjob)
		updated_crontab.close()

		p = Popen(args='acrontab < crontab.tmp', stdout=PIPE, stderr=PIPE, shell=True)
		os.remove('crontab.tmp')


		return


	## --------------------------------------------------------
	def clean_crontab(self):
		"""
		Cleans up the crontab of any kBook cron jobs
		"""

		crontab = self.acquire_crontab()

		updated_crontab = open('crontab.tmp', 'w')
		for line in crontab.split('\n'):
			if not './kBook.py' in line :
				if line:
					updated_crontab.write('{0}\n'.format(line))
		updated_crontab.close()

		p = Popen(args='acrontab < crontab.tmp', stdout=PIPE, stderr=PIPE, shell=True)
		os.remove('crontab.tmp')

		return


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
	def create_chain(self, name, input_file_path, panda_options, job_specific):
		"""
		Create a chain
		"""

		chain_path = os.path.join(self.path, '{0}_v0'.format(name))

		try:
			os.mkdir(chain_path)
		except OSError:
			log.error('Could not create chain with name {0}, another chain with the same name already exists.'.format(name))
			return


		new_chain = Chain(name, self, panda_options, chain_path, input_file_path, job_specific)
		self.insert(0, new_chain)


	## --------------------------------------------------------
	def append_to_chain(self, chain, panda_options, job_specific):
		"""
		Append a new job to a chain
		"""

		chain.append_job(panda_options, job_specific)

		return







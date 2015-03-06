##########################################################
## job.py                                               ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : Job class, to house common arugments   ##
##               and config used on many input datasets ##
##########################################################

import os, shutil, time, subprocess, select
import logging as log
from pandatools import PsubUtils
from submission import Submission
from versioned import Versioned

## =======================================================
class Job(Versioned):
	"""
	A class to contain a single job comfiguration, but to
	be used on many input datasets
	"""

	## -------------------------------------------------------
	def __init__(self, name, parent, path, input_file_path, job_specific):
		"""
		Constructor
		"""

		Versioned.__init__(self, name, parent, '')

		self.status           = 0
		self.type             = ''
		self.path             = path
		self.input_file_path  = input_file_path
		self.job_specific     = job_specific
		self.command          = ''
		self.private += [
			'read_input_file',
			'create_directory',
			'construct_command',
			'generate_output_dataset_names',
			'shell',
			'job_specific',
			'shell_command',
			'start_shell',
			'initialize'
		]

		self.level = 2

		self.finished_processes = 0
		self.total_processes    = 0
		self.completion         = '0.0%'

		self.completion_time_series = []

		self.legend_string = 'index : status        : progress : version'
		self.ls_pattern    = ('{0:<5} : {2:<22} : {2:<8} : {3:<5}', 'index', 'status', 'completion', 'version')

		self.shell = None
		self.poll  = None


	## -------------------------------------------------------
	def __getstate__(self):
		"""
		Exclude shell and poll from being pickled
		"""

		d = dict(self.__dict__)
		del d['shell']
		del d['poll']
		return d


	## -------------------------------------------------------
	def __setstate__(self, d):
		"""
		Exclude shell and poll from being pickled
		"""

		self.shell = None
		self.poll  = None

		self.__dict__.update(d)


	## -------------------------------------------------------
	def initialize(self):
		"""
		initialize the job directory, command, etc.
		"""

		self.create_directory()
		self.construct_command()
		self.read_input_file()
		self.generate_output_dataset_names()


	## -------------------------------------------------------
	def read_input_file(self):
		"""
		opens the input file and create the submissions
		"""

		f = open(self.input_file_path)
		lines = f.readlines()
		for i, line in enumerate(lines):
			self.append(Submission('submission{0}'.format(str(i).zfill(4)), self, line.rstrip('\n'), self.command, self.path))


	## -------------------------------------------------------
	def create_directory(self):
		"""
		creates the job directory that contains everything
		necessary to submit the job
		"""

		try:
			os.mkdir(self.path)
		except OSError:
			log.error('Could not create job directory, it already exists.')
			return

		## Copy the files over
		os.chdir(self.path)
		shutil.copyfile(self.input_file_path, './input_file.txt')


	## -------------------------------------------------------
	def construct_command(self):
		"""
		must be implemented by the derived classes
		"""


	## -------------------------------------------------------
	def generate_output_dataset_names(self):
		"""
		must be implemented by the derived classes
		"""


	## --------------------------------------------------------
	def recreate(self):
		"""
		recreates the submissions
		"""

		del self[:]

		self.create_directory()
		self.construct_command()
		self.read_input_file()
		self.generate_output_dataset_names()


	## ---------------------------------------------------------
	def update(self, locator=''):
		"""
		Updates completion information
		"""

		Versioned.update(self, locator)

		self.finished_processes   = 0
		self.total_processes      = 0
		raw_percentage            = 0.0
		self.completion           = '0.0%'

		for submission in self:
			self.finished_processes += submission.finished_processes
			self.total_processes += submission.total_processes

		if not self.total_processes == 0:
			raw_percentage  = float(self.finished_processes)/float(self.total_processes)
			self.completion = '{0:.1%}'.format(raw_percentage)

		self.completion_time_series.append((time.time(), raw_percentage))


	## ---------------------------------------------------------
	def start_shell(self):
		"""
		Start the job's shell
		"""

		if self.shell is not None: return False

		log.info('Starting shell...')

		## Start the shell
		self.shell = subprocess.Popen(['bash'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

		## Associate poll to shell
		self.poll = select.poll()
		self.poll.register(self.shell.stdout.fileno(), select.POLLIN)

		## Setup ATLAS
		self.shell_command('export ATLAS_LOCAL_ROOT_BASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase', silent=True)
		self.shell_command('source $ATLAS_LOCAL_ROOT_BASE/user/atlasLocalSetup.sh', silent=True)
		self.shell_command('localSetupPandaClient --noAthenaCheck', silent=True)

		## Check that grid proxy is in order
		pout_voms = self.shell_command('voms-proxy-info', silent=True)
 
		if pout_voms.find('subject') == -1:
			log.error('    Grid proxy is not set, setup now:')
			PsubUtils.checkGridProxy('',True,False)
 
		pout_voms_lines = pout_voms.rstrip('\n').split('\n')

		proxy_is_expired = False

		for line in pout_voms_lines:
			if 'timeleft' in line:
				if '00:00:00' in line: proxy_is_expired = True

		if proxy_is_expired: PsubUtils.checkGridProxy('',True,False)

		return True


   	## ---------------------------------------------------------
	def shell_command(self, command, silent=False):
		"""
		Send a command to the shell
		"""

		if self.shell is None: self.start_shell()

		output = ''
		## Send command
		self.shell.stdin.write(command + '; echo ergzuidengrutelbitz\n')
		self.shell.stdin.flush()
		## Wait for output
		print 'kBook : executing \'{0}\''.format(command)
		while True:
			if self.poll.poll(500):
				result = self.shell.stdout.readline()

				if 'ergzuidengrutelbitz' in result:
					output += result.rstrip('ergzuidengrutelbitz\n')
					break

				## Print and record output
				output += result
				if not silent:
					print 'kBook : ', result,

		return output





		

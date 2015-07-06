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
import definitions

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

		self.status           = definitions.NOT_SUBMITTED
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
			'poll',
			'job_specific',
			'shell_command',
			'start_shell',
			'initialize',
			'create_submissions',
			'create_submissions_from_parents',
			'generate_output_dataset_extensions'
		]

		self.level = 2

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
		if isinstance(self.input_file_path, str):
			self.create_submissions(self.read_input_file(self.input_file_path))
		else:
			self.create_submissions_from_parents(self.job_specific['datasets'])


	## -------------------------------------------------------
	def read_input_file(self, input_file_path):
		"""
		opens the input file and create the submissions
		"""

		f = open(input_file_path)
		lines = f.readlines()
		input_datasets = []

		for line in lines:
			line = line.strip(' \n\t')
			input_datasets.append(line)

		return input_datasets


	## -------------------------------------------------------
	def create_submissions(self, list_of_inputs):
		"""
		Create the submissions from a list of input datasets
		"""

		## Measure the number of submissions already in
		nsubs_in = len(self)

		## Compile list of current input datasets, to ensure no overlap
		current_input_datasets = [submission.input_dataset for submission in self]

		for i, input_dataset in enumerate(list_of_inputs):
			if not input_dataset in current_input_datasets:
				self.append(Submission('submission{0}'.format(str(i + nsubs_in).zfill(4)), self, input_dataset.strip(' \n\t'), self.command, self.path))
			else:
				log.warning('Dataset {0} is already part of {1}'.format(input_dataset, self.name))

		self.generate_output_dataset_names()


	## -------------------------------------------------------
	def create_submissions_from_parents(self, inputs):
		"""
		Create the submissions from a list of input datasets
		"""

		## Measure the number of submissions already in
		nsubs_in = len(self)

		## Compile list of current input datasets, to ensure no overlap
		current_input_datasets = [submission.input_dataset for submission in self]

		for i, input_submission in enumerate(inputs):

			input_dataset = input_submission.output_dataset
			if 'extension' in self.job_specific.keys():
				input_dataset += self.job_specific['extension']

			if not input_dataset in current_input_datasets:
				new_submission = Submission('submission{0}'.format(str(i + nsubs_in).zfill(4)), self, input_dataset.strip(' \n\t'), self.command, self.path)
				new_submission.parent_submission = input_submission
				self.append(new_submission)
			else:
				log.warning('Dataset {0} is already part of {1}'.format(input_dataset, self.name))

		self.generate_output_dataset_names()


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
		if not self.input_file_path is None:
			shutil.copyfile(self.input_file_path, './input_file.txt')


	## -------------------------------------------------------
	def construct_command(self):
		"""
		must be implemented by the derived classes
		"""


	## -------------------------------------------------------
	def generate_output_dataset_names(self, skip_datatype_rules=False):
		"""
		must be implemented by the derived classes
		"""

		output_name_rules = self.parent.parent.preferences.output_name_rules.split(' ')

		for submission in self:

			dataset_string = submission.input_dataset

			for rule in output_name_rules:
				if skip_datatype_rules:
					if self.input_dataset_type in rule or self.output_dataset_type in rule: continue
				strings = rule.split(':')
				input_string  = strings[0][1:-1]
				output_string = strings[-1][1:-1]
				dataset_string = dataset_string.replace(input_string, output_string)

			if skip_datatype_rules:
				dataset_string = dataset_string.replace(self.input_dataset_type, self.output_dataset_type)

			version_tag = 'v{0}.{1}'.format(self.parent.version, self.version)
			if version_tag in dataset_string:
				dataset_string = dataset_string.replace('.' + version_tag, '')

			if self.parent.name in dataset_string:
				dataset_string = dataset_string.replace('.' + self.parent.name, '')

			outDS = 'user.{0}.{1}.{2}.{3}'.format(
				self.parent.parent.preferences.user,
				dataset_string,
				self.parent.name,
				version_tag,
				)
			submission.output_dataset = outDS


	## --------------------------------------------------------
	def recreate(self):
		"""
		recreates the submissions
		"""

		del self[:]

		## Detect previous job in chain
		job_index = None

		self.parent.sort_by_index()
		for i, job in enumerate(self.parent):
			if (job.name == self.name) and (job.version == self.version):
				job_index = i

		if not (job_index is None) and not (job_index == 0):
			previous_job = self.parent[job_index - 1]
			self.job_specific['datasets'] = [submission for submission in previous_job.get_latest()]

		self.initialize()


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


	## ---------------------------------------------------------
	def generate_output_dataset_extensions(self):
		"""
		generate a list of extensions characterizing the different output datasets created
		"""

		extensions = []

		for submission in self:
			submission_extensions = submission.generate_output_dataset_extensions()
			if len(submission_extensions) > len(extensions):
				extensions = submission_extensions

		return extensions

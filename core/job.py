##########################################################
## job.py                                               ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : Job class, to house common arugments   ##
##               and config used on many input datasets ##
##########################################################

import os, shutil
import logging as log
from submission import Submission
from versioned import Versioned

## =======================================================
class Job(Versioned):
	"""
	A class to contain a single job comfiguration, but to
	be used on many input datasets
	"""

	## -------------------------------------------------------
	def __init__(self, name, parent, path, input_file_path):
		"""
		Constructor
		"""

		Versioned.__init__(self, name, parent, '')

		self.status           = 'not submitted'
		self.type             = ''
		self.path             = path
		self.input_file_path  = input_file_path
		self.command          = ''
		self.private += [
			'read_input_file',
			'create_directory',
			'construct_command',
			'generate_output_dataset_names',
			'next',
			'previous'
			'copy'
		]

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


	## -------------------------------------------------------
	def retrieve(self, locator='', one_file=True):
		"""
		Retrieve output datasets
		"""

		if (not locator) or (locator == 'all'):
			for submission in self:
				submission.retrieve('', one_file)
		else:
			i, submission = self.locate(locator)
			if i < 0:
				log.error('{0} does not exist in {1}'.format(locator, self.name))
				return
			submission.retrieve('', one_file)



		

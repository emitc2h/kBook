##########################################################
## submission.py                                        ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : Submission class, to hold a single     ##
##               submission                             ##
##########################################################

import os
import logging as log
from subprocess import Popen, PIPE

## =======================================================
class Submission:
	"""
	A class to handle the submission of a single grid
	command
	"""

	## -------------------------------------------------------
	def __init__(self, preferences, input_dataset, command, path):
		"""
		Constructor
		"""

		self.path             = path
		self.preferences      = preferences
		self.command          = command
		self.input_dataset    = input_dataset
		self.output_dataset   = ''
		self.current_panda_id = -1
		self.past_panda_ids   = []
		self.status           = 'not submitted'


	## -------------------------------------------------------
	def ls(self, locator=''):
		"""
		prints out information about the submission
		"""

		log.info('-'*40)
		log.info('input dataset    : {0}'.format(self.input_dataset))
		log.info('output dataset   : {0}'.format(self.output_dataset))
		log.info('status           : {0}'.format(self.status))
		log.info('current panda ID : {0}'.format(self.current_panda_id))
		log.info('command          : {0}'.format(self.command))
		log.info('-'*40)


	## -------------------------------------------------------
	def cd(self, locator=''):
		"""
		does nothing
		"""
		return False


	## --------------------------------------------------------
	def submit(self, locator=''):
		"""
		submits the one submission
		"""

		if not self.status == 'not submitted':
			log.info('already submitted, skipping.')
			return

		os.chdir(self.path)

		## Finish constructing the command
		command = '{0} {1}'.format(self.command.format(input=self.input_dataset, output=self.output_dataset), self.preferences.panda_options)

		log.info('='*40)
		log.info('Submitting ...')
		log.info('-'*40)
		log.info(command)

		p = Popen(args=command, stdout=PIPE, shell=True)
		p.wait()
		pout, perr = p.communicate()

		pout_lines = pout.split('\n')
		for line in pout_lines:
			if 'JobsetID' in line:
				self.current_panda_id = int(line.split(':')[-1])

		log.info(pout)
		log.info(perr)

		if (perr is None) or (not 'ERROR' in pout):
			self.status = 'submitted'
		else:
			self.status = 'error'









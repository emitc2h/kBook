##########################################################
## submission.py                                        ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : Submission class, to hold a single     ##
##               submission                             ##
##########################################################

import logging as log

## =======================================================
class Submission:
	"""
	A class to handle the submission of a single grid
	command
	"""

	## -------------------------------------------------------
	def __init__(self, input_dataset):
		"""
		Constructor
		"""

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
		log.info('-'*40)


	## -------------------------------------------------------
	def cd(self, locator=''):
		"""
		does nothing
		"""
		return False



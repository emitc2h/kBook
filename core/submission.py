##########################################################
## submission.py                                        ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : Submission class, to hold a single     ##
##               submission                             ##
##########################################################

## =======================================================
class Submission:
	"""
	A class to handle the submission of a single grid
	command
	"""

	## -------------------------------------------------------
	def __init__(self):
		"""
		Constructor
		"""

		self.input_dataset  = ''
		self.output_dataset = ''
		self.job_id         = -1
		self.status         = -1


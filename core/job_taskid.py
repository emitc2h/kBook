##########################################################
## job_taskid.py                                        ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : specialization of the Job class for    ##
##               track tasks submitted by other means   ##
##########################################################

import os, shutil, glob
from job import Job
import logging as log
from submission import Submission
from pandatools import Client

## -------------------------------------------------------
def gather(ask_for_path):
	"""
	Gather the information from the user to create the job
	"""

	job_specific = {}
	job_specific['job_type'] = 'taskid'

	return job_specific


## =======================================================
class JobTaskID(Job):
	"""
	A class to contain a single job comfiguration, but to
	be used on many input datasets
	"""


	## -------------------------------------------------------
	def __init__(self, *args, **kwargs):
		"""
		Constructor
		"""

		Job.__init__(self, *args, **kwargs)

		self.type = 'taskid'

		self.legend_string = 'index : type         : status        : progress'
		self.ls_pattern    = ('{0:<5} : {1:<12} : {2:<22} : {3:<8}', 'index', 'type', 'status', 'completion')

		self.initialize()


	## -------------------------------------------------------
	def read_input_file(self):
		"""
		opens the input file and create the submissions
		"""

		f = open(self.input_file_path)
		lines = f.readlines()
		i = 0
		for line in lines:
			if 'jediTaskID' in line:
				new_panda_task_id = -1
				line_elements = line.split(' ')
				for line_element in line_elements:
					if 'jediTaskID' in line_element:
						new_panda_task_id = int(line_element.split('=')[-1])
				
				log.info('Adding task ID {0} ...'.format(new_panda_task_id))
				jedi_task_dict = {}
				jedi_task_dict['jediTaskID'] = new_panda_task_id
				status, new_jedi_task_dict = Client.getJediTaskDetails(jedi_task_dict, True, True)
				
				new_submission = Submission('submission{0}'.format(str(i).zfill(4)), self, '', '', self.path)
				new_submission.input_dataset = new_jedi_task_dict['inDS'].split(',')[0]

				## Obtain the relevant output datasets
				output_datasets = new_jedi_task_dict['outDS'].split(',')
				new_submission.output_dataset = ','.join(filter(lambda d : not '.log' in d, output_datasets))
				new_submission.jedi_task_dict = new_jedi_task_dict
				new_submission.command = new_jedi_task_dict['cliParams']
				self.append(new_submission)
				i += 1
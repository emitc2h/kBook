##########################################################
## versioned.py                                         ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : A base class to provide a versioning   ##
##               system                                 ##
##########################################################

import copy, os, time
import logging as log
from navigable import Navigable

## =======================================================
class Versioned(Navigable):
	"""
	A base class to provide links between diferrent versions
	of the same navigable
	"""

	## -------------------------------------------------------
	def __init__(self, *args, **kwargs):
		"""
		Constructor
		"""

		Navigable.__init__(self, *args, **kwargs)

		self.version  = 0
		self.previous = None
		self.next     = None
		self.path     = ''


	## --------------------------------------------------------
	def copy(self):
		"""
		Spawns a copy of the current versioned and increments the version number
		"""

		if not self.next is None:
			log.error('Please spawn from the most recent version.')
			return None

		new_version = copy.deepcopy(self)
		new_version.creation_time = time.time()
		new_version.modified_time = time.time()
		new_version.version = self.version + 1
		self.next = new_version
		self.hide = -1
		new_version.previous = self
		new_version.path = self.path.replace('v{0}'.format(self.version), 'v{0}'.format(new_version.version))
		os.mkdir(new_version.path)

		return new_version


	## ---------------------------------------------------------
	def show_versions(self):
		"""
		lists previous versions
		"""

		current_version = self
		versions = []
		while not current_version is None:
			versions.append(current_version)
			current_version = current_version.previous

		current_version = self.next
		versions.reverse()
		while not current_version is None:
			versions.append(current_version)
			current_version = current_version.next

		versions.reverse()

		log.info('-'*40)
		log.info('version : creation time')
		log.info('- '*20)
		for version in versions:
			if self.version == version.version:
				log.info('{0:<7} : {1:<24} *'.format(version.version, time.ctime(version.creation_time)))
			else:
				log.info('{0:<7} : {1:<24}'.format(version.version, time.ctime(version.creation_time)))


	## ---------------------------------------------------------
	def recreate(self):
		"""
		To be implemented by the inheriting classes
		"""



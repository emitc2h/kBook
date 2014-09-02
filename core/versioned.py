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
		self.current  = True
		self.path     = ''
		self.private += [
			'copy',
			'previous',
			'next',
			'show_versions',
			'recreate',
			'get_latest',
			'get_version'
		]


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
		self.current = False
		new_version.previous = self
		new_version.next = None
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

		log.info('{0} versions:'.format(self.name))
		log.info('-'*40)
		log.info('version : creation time')
		log.info('- '*20)
		for version in versions:
			if version.current:
				log.info('{0:<7} : {1:<24} *'.format(version.version, time.ctime(version.creation_time)))
			else:
				log.info('{0:<7} : {1:<24}'.format(version.version, time.ctime(version.creation_time)))
		log.info('-'*40)


	## ---------------------------------------------------------
	def get_version(self, locator=-1):
		"""
		returns the specified version, while hiding all others
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

		new_current_version = None

		if 0 <= locator < len(versions):
			for version in versions:
				if version.version == locator:
					version.hide = 1
					version.current = True
					new_current_version = version
				else:
					version.hide = -1
					version.current = False
			return new_current_version
		else:
			log.error('Version {0} for {1} does not exist.'.format(locator, self.name))
				


	## ---------------------------------------------------------
	def get_latest(self):
		"""
		get the latest version
		"""

		current_version = self
		while not current_version is None:
			if current_version.next is None:
				return current_version
			current_version = current_version.next
		return self


	## ---------------------------------------------------------
	def recreate(self):
		"""
		To be implemented by the inheriting classes
		"""



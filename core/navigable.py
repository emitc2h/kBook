##########################################################
## navigable.py                                         ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : A base class that can be embedded in a ##
##               hierachy of other navigables           ##
##########################################################

import time
import logging as log
from subprocess import Popen, PIPE

## =======================================================
class Navigable(list):
	"""
	A base class to form a hierarchy, which can then be
	navigated a la bash shell (cd, ls). It also provides
	basic functions to get and set nabigable properties
	"""

	## -------------------------------------------------------
	def __init__(self, name, parent, panda_options):
		"""
		Constructor
		"""

		self.name          = name
		self.parent        = parent
		self.index         = -1
		self.panda_options = panda_options
		self.creation_time = time.time()
		self.modified_time = time.time()
		self.comment       = ''
		self.private       = [
			'rebuild_hierarchy',
			'locate',
			'cd',
			'ls',
			'get',
			'set',
			'parent',
			'private',
			'sort_by_time',
			'append',
			'count',
			'extend',
			'insert',
			'pop',
			'remove',
			'reverse',
			'sort',
			'legend_string',
			'ls_pattern',
			'index',
			'retrieve'
			]

		self.legend_string = 'index : name'
		self.ls_pattern    = ('{0:<5} : {1:<20}', 'index', 'name')


	## -------------------------------------------------------
	def rebuild_hierarchy(self):
		"""
		rebuilds the links between parents and children navigables
		"""

		for navigable in self:
			navigable.parent = self
			navigable.rebuild_hierarchy()



	## --------------------------------------------------------
	def locate(self, locator=''):
		"""
		return child navigable with index
		"""

		if len(self) == 0:
			return -1, None

		## locator interpretation: name or index?
		is_index = False
		try:
			index = int(locator)
			is_index = True
		except ValueError:
			pass

		if is_index:
			try:
				return index, self[index]
			except IndexError:
				log.error('The index provided must from 0 to {0}'.format(len(self)-1))
				return -1, None
		else:
			for i, navigable in enumerate(self):
				if navigable.name == locator: return i, navigable
			log.error('Could not locate {0}'.format(locator))
			return -1, None


	## --------------------------------------------------------
	def sort_by_time(self):
		"""
		sort the children by modified time
		"""

		self.sort(key=lambda navigable: navigable.modified_time, reverse=True)
		for i, navigable in enumerate(self):
			navigable.index = i


	## --------------------------------------------------------
	def ls(self, locator=''):
		"""
		lists information about the children
		"""

		self.sort_by_time()

		## figure out path
		current_navigable = self
		navigable_path    = self.name
		while not current_navigable.parent is None:
			navigable_path = current_navigable.parent.name + '/' + navigable_path
			current_navigable = current_navigable.parent

		if not locator:
			try:
				log.info('In {0} : '.format(navigable_path))
				log.info('-'*40)
				log.info(self[0].legend_string)
				log.info('- '*20)
			except IndexError:
				log.error('{0} is empty'.format(self.name))
				return
			for i, navigable in enumerate(self):

				## Gather arguments
				args = []
				for i in range(len(navigable.ls_pattern)-1):
					args.append(getattr(navigable, navigable.ls_pattern[i+1]))

				log.info(navigable.ls_pattern[0].format(*args))

			log.info('-'*40)

		elif locator == 'all':
			if len(self) == 0:
				log.error('No lower hierarchy.')
				return
			for navigable in self:
				navigable.ls()

		else:
			i, navigable = self.locate(locator)
			if i < 0:
				log.error('{0} does not exist in {1}'.format(locator, self.parent.name))
				return
			navigable.ls()


	## --------------------------------------------------------
	def cd(self, locator=''):
		"""
		Go to a job
		"""

		if (not locator) or (locator=='..'):
			if not self.parent is None:
				return self.parent
			else:
				log.error('There is no higher step in the hierarchy.')
				return self
		elif '/' in locator:
			recursions = locator.split('/')
			current_navigable = self
			try:
				for recursion in recursions:
					current_navigable = current_navigable.cd(recursion)
				return current_navigable
			except AttributeError:
				log.error('{0} is an invalid path'.format(locator))
				return self
		else:
			i, navigable = self.locate(locator)
			if i < 0:
				log.error('{0} does not exist in {1}'.format(locator, self.name))
				return self
			return navigable


	## --------------------------------------------------------
	def get(self, locator='', attribute=''):
		"""
		Get the value for a given parameter of either the current object
		or a child
		"""

		if not locator and not attribute:
			log.info('{0} attributes are:'.format(self.name))
			log.info('-'*40)
			for att in dir(self):
				if '__' in att: continue
				if att in self.private: continue
				if '_time' in att:
					log.info('{0:<20} = {1:<30}'.format(att, time.ctime(getattr(self, att))))
				else:
					log.info('{0:<20} = {1:<30}'.format(att, getattr(self, att)))
			return

		elif locator == 'self':
			try:
				if '_time' in attribute:
					log.info('{0:<20} = {1:<30}'.format(attribute, time.ctime(getattr(self, attribute))))
				else:
					log.info('{0:<20} = {1:<30}'.format(attribute, getattr(self, attribute)))
			except AttributeError:
				log.error('{0} is not an attribute of {1}'.format(attribute, self.name))
				return

		elif locator == 'all' and not attribute:
			if len(self) == 0:
				log.error('No lower hierarchy.')
				return
			for navigable in self:
				navigable.get()

		elif locator == 'all':
			if len(self) == 0:
				log.error('No lower hierarchy.')
				return
			for navigable in self:
				navigable.get('self', attribute)


		elif not attribute:
			i, navigable = self.locate(locator)
			if i < 0:
				log.error('{0} does not exist in {1}'.format(locator, self.name))
				return
			navigable.get()
		else:
			i, navigable = self.locate(locator)
			if i < 0:
				log.error('{0} does not exist in {1}'.format(locator, self.name))
				return
			navigable.get('self', attribute)


	## --------------------------------------------------------
	def set(self, locator='', attribute='', value=''):
		"""
		Set the value for a given parameter of either the current object
		or a child
		"""

		if attribute in self.private:
			log.error('{0} is a private attribute.'.format(attribute))
			return

		## Some value interpretation
		if   value == 'False':	  value = False
		elif value == 'True' :    value = True
		else:
			try:
				value = int(value)
			except ValueError:
				try:
					value = float(value)
				except ValueError:
					pass

		if locator == 'all':
			for navigable in self:
				if attribute in dir(navigable):
					setattr(navigable, attribute, value)
					log.info('Setting {0} to \'{1}\' for {2}'.format(attribute, value, navigable.name))
					self.modified_time = time.time()
				else:
					log.error('{0} has no attribute called {1}'.format(self[0].name, attribute))
					return

		elif locator == 'self':
			if attribute in dir(self):
				setattr(self, attribute, value)
				log.info('Setting {0} to \'{1}\' for {2}'.format(attribute, value, self.name))
				self.modified_time = time.time()
			else:
				log.error('{0} has no attribute called {1}'.format(self.name, attribute))
				return

		else:
			i, navigable = self.locate(locator)
			if i < 0:
				log.error('{0} does not exist in {1}'.format(locator, self.name))
				return
			if attribute in dir(navigable):
				setattr(navigable, attribute, value)
				log.info('Setting {0} to \'{1}\' for {2}'.format(attribute, value, navigable.name))
				self.modified_time = time.time()
			else:
				log.error('{0} has no attribute called {1}'.format(navigable.name, attribute))
				return


	## --------------------------------------------------------
	def submit(self, locator=''):
		"""
		Submit jobs
		"""

		if not locator:
			for navigable in self:
				navigable.submit()
		elif locator == 'all':
			for navigable in self:
				navigable.submit()
		elif locator == 'self':
			self.submit()
		else:
			i, navigable = self.locate(locator)
			if i < 0:
				log.error('{0} does not exist in {1}'.format(locator, self.name))
				return
			navigable.submit()


	## --------------------------------------------------------
	def retrieve(self, locator='', one_file=True):
		"""
		Retrieve output datasets
		"""

		## Check for DQ2 tools
		p = Popen(args = 'echo $DQ2_HOME', stdout=PIPE, shell = True)
		pout = p.communicate()[0]

		if pout == '\n':
			log.error('cannot proceed, dq2 is not setup: setupATLAS; localSetupDQ2Client')
			return False

		if not self.status == 'finished':
			log.warning('dataset is not finished, do you want to proceed (y/n) ?')
			answer = raw_input('kBook > ')
			if answer == 'y':
				return True
			else:
				return False

		return True













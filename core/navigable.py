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
import definitions

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
		self.index         = 0
		self.panda_options = panda_options
		self.creation_time = time.time()
		self.modified_time = time.time()
		self.status        = 0
		self.comment       = ''
		self.hide          = 1
		self.private       = [
			'rebuild_hierarchy',
			'locate',
			'navigate',
			'ls',
			'info',
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
			'submit',
			'status_string',
			'evaluate_status',
			'update',
			'generate_list'
			]

		self.level = 0

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
			log.error('{0} does not have children'.format(self.name))
			return -1, self

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
				return -1, self
		else:
			for i, navigable in enumerate(self):
				if navigable.name == locator: 
					return i, navigable
			log.error('Could not locate {0}'.format(locator))
			return -1, self


	## --------------------------------------------------------
	def navigate(self, locator=''):
		"""
		returns a different navigable in the navigable hierarchy
		"""

		## Reference to current navigable
		if not locator or locator == 'self':
			return self.index, self


		## Reference to parent navigable
		elif locator == '..':
			if not self.parent is None:
				return self.parent.index, self.parent
			else:
				log.error('{0} does not have a parent'.format(self.name))
				return -1, self


		## Reference to navigable through path
		elif '/' in locator:
			recursions = locator.split('/')
			current_navigable = self
			try:
				for recursion in recursions:
					index, current_navigable = current_navigable.navigate(recursion)
				return index, current_navigable
			except AttributeError:
				log.error('{0} is an invalid path'.format(locator))
				return -1, self


		## Reference to children in current navigable
		else:
			return self.locate(locator)


	## --------------------------------------------------------
	def sort_by_time(self):
		"""
		sort the children by modified time
		"""

		self.sort(key=lambda navigable: navigable.modified_time*navigable.hide, reverse=True)
		for i, navigable in enumerate(self):
			navigable.index = i


	## --------------------------------------------------------
	def ls(self, locator=''):
		"""
		lists information about the children
		"""

		if locator == 'all':
			if len(self) == 0:
				log.error('{0} does not have children'.format(self.name))
				return
			for navigable in self:
				navigable.ls()

		else:
			## Obtain navigable to ls
			i, current_navigable = self.navigate(locator)
			if i < 0: return

			## prints info if navigable has no children
			if len(current_navigable) == 0:
				current_navigable.info()
				return
	
			## sorting items to list by time
			current_navigable.sort_by_time()
	
			## figure out path to print
			current_navigable_for_path = current_navigable
			navigable_path = current_navigable_for_path.name
			while not current_navigable_for_path.parent is None:
				navigable_path = current_navigable_for_path.parent.name + '/' + navigable_path
				current_navigable_for_path = current_navigable_for_path.parent

			log.info('In {0} : '.format(navigable_path))
			log.info('-'*len(current_navigable[0].legend_string))
			log.info(current_navigable[0].legend_string)
			log.info('- '*(len(current_navigable[0].legend_string)/2))


			for i, navigable in enumerate(current_navigable):

				## skip hidden
				if navigable.hide < 0: continue

				## Gather arguments
				args = []
				for j in range(len(navigable.ls_pattern)-1):
					if navigable.ls_pattern[j+1] == 'status':
						args.append(definitions.kbook_status[navigable.status])

					else:
						args.append(getattr(navigable, navigable.ls_pattern[j+1]))

				log.info(navigable.ls_pattern[0].format(*args))

			log.info('-'*len(current_navigable[0].legend_string))


	## --------------------------------------------------------
	def info(self):
		"""
		A function to print out info when ls is called on a navigable with no children
		"""
		return


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
					log.info('{0:<23} = {1:<30}'.format(att, time.ctime(getattr(self, att))))
				else:
					log.info('{0:<23} = {1:<30}'.format(att, getattr(self, att)))
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
			i, navigable = self.navigate(locator)
			if i < 0:
				log.error('{0} does not exist in {1}'.format(locator, self.name))
				return
			navigable.get()
		else:
			i, navigable = self.navigate(locator)
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
		elif value.startswith('[') and value.endswith(']'):
			items = value.lstrip('[').rstrip(']').split(',')
			value_list = []
			for item in items:
				try:
					value_list.append(int(item))
				except ValueError:
					try:
						value_list.append(float(item))
					except ValueError:
						value_list.append(item)
			value = value_list

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

		else:
			i, navigable = self.navigate(locator)
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
		else:
			i, navigable = self.navigate(locator)
			if i < 0:
				log.error('{0} does not exist in {1}'.format(locator, self.name))
				return
			navigable.submit()


	## ---------------------------------------------------------
	def status_string(self):
		"""
		returns a human readable string for the status
		"""

		return definitions.kbook_status[self.status]


	## ---------------------------------------------------------
	def update(self, locator=''):
		"""
		update the status
		"""

		if self.hide == -1: return

		if hasattr(self, 'version'):
			log.debug('{0}updating {1} v{2} ...'.format('    '*self.level, self.name, self.version))
		else:
			log.debug('{0}updating {1} ...'.format('    '*self.level, self.name))

		if not locator:
			for navigable in self:
				navigable.update()
			self.evaluate_status()
		elif locator == 'all':
			for navigable in self:
				navigable.update()
			self.evaluate_status()
		else:
			i, navigable = self.navigate(locator)
			if i < 0:
				log.error('{0} does not exist in {1}'.format(locator, self.name))
				return
			navigable.update()


	## ---------------------------------------------------------
	def generate_list(self, attribute, locator=''):
		"""
		generates a list containing a particular attribute of the lowest level navigable
		"""

		values = []

		if hasattr(self, attribute):
			return self.parent, [getattr(self, attribute)]
		else:
			for navigable in self:
				current_parent, current_list = navigable.generate_list(attribute)
				values += current_list
			return current_parent, values





	## ---------------------------------------------------------
	def evaluate_status(self):
		"""
		Evaluates the status from the children
		"""

		if len(self) == 0:
			return self.status
		else:
			minimum_status = 5
			for navigable in self:
				navigable_status = navigable.evaluate_status()
				if navigable_status < minimum_status:
					minimum_status = navigable_status
			self.status = minimum_status
			return self.status













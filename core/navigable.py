##########################################################
## navigable.py                                         ##
## author      : Michel Trottier-McDonald <mtm@cern.ch> ##
## date        : July 2014                              ##
## description : A base class that can be embedded in a ##
##               hierachy of other navigables           ##
##########################################################

import time, os
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
		self.status        = definitions.NOT_SUBMITTED
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
			'close',
			'open',
			'parent',
			'private',
			'sort_by_time',
			'sort_by_index',
			'append',
			'count',
			'extend',
			'level',
			'insert',
			'pop',
			'remove',
			'reverse',
			'sort',
			'legend_string',
			'ls_pattern',
			'submit',
			'kill',
			'retry',
			'index',
			'status_string',
			'evaluate_status',
			'update',
			'generate_list',
			'list_of_attributes',
			'make_completion_graph',
			'is_not_submitted',
			'is_cancelled',
			'is_unfinished',
			'is_running',
			'is_finished',
			'is_closed',
			'is_hidden',
			]

		self.level = 0

		self.finished_processes   = 0
		self.total_processes      = 0
		self.completion         = '0.0%'
		self.completion_time_series = []

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
			return (-1, self)


		## locator interpretation: name or index?
		try:
			index = int(locator)
		except ValueError:
			log.info('argument {0} is not an index'.format(locator))
			return (-1, self)

		try:
			return (index, self[index])
		except IndexError:
			log.error('The index provided must from 0 to {0}'.format(len(self)-1))
			return (-1, self)


	## --------------------------------------------------------
	def navigate(self, locator=''):
		"""
		returns a different navigable in the navigable hierarchy
		"""

		## Reference to current navigable
		if not locator or locator == 'self':
			return [(self.index, self)]


		## Reference to parent navigable
		elif locator == '..':
			if not self.parent is None:
				return [(self.parent.index, self.parent)]
			else:
				log.error('{0} does not have a parent'.format(self.name))
				return [(-1, self)]


		## Reference to navigable through path
		elif '/' in locator:
			recursions = locator.split('/')
			current_navigables = [(-1, self)]
			try:
				for recursion in recursions:
					current_navigables = current_navigables[0][1].navigate(recursion)
				return current_navigables
			except AttributeError:
				log.error('{0} is an invalid path'.format(locator))
				return [(-1, self)]


		## Reference to several navigables by intervals
		elif ('-' in locator) or (',' in locator):
			navigables = []
			intervals = locator.split(',')
			for interval in intervals:
				bounds = interval.split('-')

				if len(bounds) == 1:
					navigables.append(self.locate(bounds[0]))

				elif len(bounds) == 2:
					try:
						lo = int(bounds[0])
						hi = int(bounds[1])
					except ValueError:
						log.info('Invalid interval syntax')
						return [(-1, self)]

					if not (hi >= lo):
						log.info('Intervals should be specified from smaller value to larger value. Ex: \'3-6\', not \'6-3\'.')
						return [(-1, self)]

					for i in range(lo, hi+1):
						navigables.append((i, self[i]))

				else:
					log.info('Intervals must be composed of two numbers separated by a \'-\'. Ex: \'3-\'6.')
					return [(-1, self)]

			return navigables

		## Reference to several navigable by status
		elif (locator in definitions.kbook_status_list):
			navigables = []
			for i, navigable in enumerate(self):
				if navigable.status == definitions.kbook_status_reversed[locator]:
					navigables.append((i, self[i]))

			return navigables



		## Reference to children in current navigable
		else:
			return [self.locate(locator)]


	## --------------------------------------------------------
	def sort_by_time(self):
		"""
		sort the children by modified time
		"""

		self.sort(key=lambda navigable: navigable.modified_time*navigable.hide, reverse=True)
		for i, navigable in enumerate(self):
			navigable.index = i


	## --------------------------------------------------------
	def sort_by_index(self):
		"""
		sort the children by modified time
		"""

		self.sort(key=lambda navigable: navigable.index + 100000*navigable.is_hidden())
		for i, navigable in enumerate(self):
			navigable.index = i


	## --------------------------------------------------------
	def ls(self, locator='', option=''):
		"""
		lists information about the children
		"""

		if locator == 'all':
			if len(self) == 0:
				log.error('{0} does not have children'.format(self.name))
				return
			for navigable in self:
				navigable.ls()

		elif locator in definitions.kbook_status_list:

			## prints info if navigable has no children
			if len(self) == 0:
				self.info()
				return
	
			## sorting items to list by time, unless it is a chain in which the order is determined by what feed into what
			if self.level == 1:
				self.sort_by_index()
			else:
				self.sort_by_time()
	
			## figure out path to print
			current_navigable_for_path = self
			navigable_path = current_navigable_for_path.name
			while not current_navigable_for_path.parent is None:
				navigable_path = current_navigable_for_path.parent.name + '/' + navigable_path
				current_navigable_for_path = current_navigable_for_path.parent

			book = current_navigable_for_path

			log.info('in {0} : '.format(navigable_path))
			log.info('-'*len(self[0].legend_string))
			log.info(self[0].legend_string)
			log.info('- '*(len(self[0].legend_string)/2))

			## Obtain navigables to ls
			navigables = self.navigate(locator)
			for j, navigable in navigables:

				## skip hidden
				if not option == 'hidden':
					if navigable.hide < 0: continue

				## Gather arguments
				args = []
				for k in range(len(navigable.ls_pattern)-1):
					if navigable.ls_pattern[k+1] == 'status':
						if book.use_color:
							args.append(definitions.kbook_status[navigable.status])
						else:
							args.append(definitions.kbook_status_no_color[navigable.status])

					elif 'time' in navigable.ls_pattern[k+1]:
						args.append(time.ctime(getattr(navigable, navigable.ls_pattern[k+1])))

					else:
						args.append(getattr(navigable, navigable.ls_pattern[k+1]))

				log.info(navigable.ls_pattern[0].format(*args))

			log.info('-'*len(self[0].legend_string))


		else:
			## Obtain navigable to ls
			navigables = self.navigate(locator)
			for i, current_navigable in navigables:
				if i < 0: return

				## skip hidden
				if not option == 'hidden':
					if current_navigable.hide < 0: continue
	
				## prints info if navigable has no children
				if len(current_navigable) == 0:
					current_navigable.info()
					continue
		
				## sorting items to list by time
				if current_navigable.level == 1:
					current_navigable.sort_by_index()
				else:
					current_navigable.sort_by_time()
		
				## figure out path to print
				current_navigable_for_path = current_navigable
				navigable_path = current_navigable_for_path.name
				while not current_navigable_for_path.parent is None:
					navigable_path = current_navigable_for_path.parent.name + '/' + navigable_path
					current_navigable_for_path = current_navigable_for_path.parent

				book = current_navigable_for_path
	
				log.info('in {0} : '.format(navigable_path))
				log.info('-'*len(current_navigable[0].legend_string))
				log.info(current_navigable[0].legend_string)
				log.info('- '*(len(current_navigable[0].legend_string)/2))

				## In case jobs are being browsed, make sure to print a new header if jobs are of a different type
				if current_navigable[0].level == 2:
					current_type = current_navigable[0].type


				for j, navigable in enumerate(current_navigable):
	
					## skip hidden
					if not option == 'hidden':
						if navigable.hide < 0: continue

					## In case the job type changes, print header again
					if (navigable.level == 2):
						if not navigable.type == current_type:
							log.info('')
							log.info(navigable.legend_string)
							log.info('- '*(len(navigable.legend_string)/2))
							current_type = navigable.type

	
					## Gather arguments
					args = []
					for k in range(len(navigable.ls_pattern)-1):
						if navigable.ls_pattern[k+1] == 'status':
							if book.use_color:
								args.append(definitions.kbook_status[navigable.status])
							else:
								args.append(definitions.kbook_status_no_color[navigable.status])
	
						elif 'time' in navigable.ls_pattern[k+1]:
							args.append(time.ctime(getattr(navigable, navigable.ls_pattern[k+1])))

						else:
							args.append(getattr(navigable, navigable.ls_pattern[k+1]))
	
					log.info(navigable.ls_pattern[0].format(*args))
	
				log.info('-'*len(current_navigable[-1].legend_string))


	## --------------------------------------------------------
	def info(self):
		"""
		A function to print out info when ls is called on a navigable with no children
		"""
		return


	## --------------------------------------------------------
	def list_of_attributes(self):
		"""
		obtain a list of attributes
		"""

		attributes = []
		for att in dir(self):
			if '__' in att: continue
			if att in self.private: continue
			attributes.append(att)

		return attributes



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
				if '_time' in att and not 'series' in att:
					log.info('{0:<5} : {1:<23} = {2:<30} ({3})'.format(self.index, att, time.ctime(getattr(self, att)), getattr(self, att)))
				else:
					log.info('{0:<5} : {1:<23} = {2:<30}'.format(self.index, att, getattr(self, att)))
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
			navigables = self.navigate(locator)
			for i, navigable in navigables:
				if i < 0:
					log.error('{0} does not exist in {1}'.format(locator, self.name))
					return
				navigable.get()
		else:
			navigables = self.navigate(locator)
			for i, navigable in navigables:

				if i < 0:
					log.error('{0} does not exist in {1}'.format(locator, self.name))
					return
					
				if '__' in attribute or attribute in navigable.private:
					log.info('{0} is private'.format(attribute))
					return

				if not attribute in navigable.list_of_attributes():
					log.error('{0} is not an attribute of {1}'.format(attribute, self.name))
					return
	
				if '_time' in attribute and not 'series' in attribute:
					log.info('{0:<5} : {1:<23} = {2:<30} ({3})'.format(navigable.index, attribute, time.ctime(getattr(navigable, attribute)), getattr(navigable, attribute)))
				else:
					log.info('{0:<5} : {1:<23} = {2:<30}'.format(navigable.index, attribute, getattr(navigable, attribute)))


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
			navigables = self.navigate(locator)
			for i, navigable in navigables:
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
	def close(self, locator=''):
		"""
		Close the navigable for further updates
		"""

		if self.is_hidden(): return

		if not locator:
			self.status = definitions.CLOSED
			for navigable in self:
				navigable.close()
		elif locator == 'all':
			for navigable in self:
				navigable.close()
		else:
			navigables = self.navigate(locator)
			for i, navigable in navigables:
				if i < 0:
					log.error('{0} does not exist in {1}'.format(locator, self.name))
					return
				navigable.close()


	## --------------------------------------------------------
	def open(self, locator=''):
		"""
		Close the navigable for further updates
		"""

		if self.is_hidden(): return

		if not locator:
			if self.is_closed():
				self.status = definitions.NOT_SUBMITTED
			else:
				log.error('{0} is already open'.format(self.name))
			for navigable in self:
				navigable.open()
		elif locator == 'all':
			for navigable in self:
				navigable.open()
		else:
			navigables = self.navigate(locator)
			for i, navigable in navigables:
				if i < 0:
					log.error('{0} does not exist in {1}'.format(locator, self.name))
					return
				navigable.open()


	## --------------------------------------------------------
	def submit(self, locator=''):
		"""
		Submit jobs
		"""

		if self.is_closed(): return
		if self.is_hidden(): return

		if not locator:
			for navigable in self:
				navigable.submit()
		elif locator == 'all':
			for navigable in self:
				navigable.submit()
		else:
			navigables = self.navigate(locator)
			for i, navigable in navigables:
				if i < 0:
					log.error('{0} does not exist in {1}'.format(locator, self.name))
					return
				navigable.submit()


	## --------------------------------------------------------
	def retry(self, locator=''):
		"""
		Retry jobs
		"""

		if self.is_closed(): return
		if self.is_hidden(): return

		log.debug('{0}retrying {1} ...'.format('    '*self.level, self.name))

		if not locator:
			for navigable in self:
				navigable.retry()
		elif locator == 'all':
			for navigable in self:
				navigable.retry()
		else:
			navigables = self.navigate(locator)
			for i, navigable in navigables:
				if i < 0:
					log.error('{0} does not exist in {1}'.format(locator, self.name))
					return
				navigable.retry()

		self.status = definitions.RUNNING


	## --------------------------------------------------------
	def kill(self, locator=''):
		"""
		Kill jobs
		"""

		if self.is_closed(): return
		if self.is_hidden(): return
		
		log.debug('{0}killing {1} ...'.format('    '*self.level, self.name))

		if not locator:
			for navigable in self:
				navigable.kill()
		elif locator == 'all':
			for navigable in self:
				navigable.kill()
		else:
			navigables = self.navigate(locator)
			for i, navigable in navigables:
				if i < 0:
					log.error('{0} does not exist in {1}'.format(locator, self.name))
					return
				navigable.kill()

		self.status = definitions.CANCELLED


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

		if not (self.is_hidden() or self.is_closed()):
			if hasattr(self, 'version'):
				log.info('{0}updating {1} v{2} ...'.format('    '*self.level, self.name, self.version))
			else:
				log.info('{0}updating {1} ...'.format('    '*self.level, self.name))

		if not locator:

			if self.is_closed(): return
			if self.is_hidden(): return

			for navigable in self:
				navigable.update()
			self.evaluate_status()


		elif locator == 'all':
			for navigable in self:
				navigable.update()
			self.evaluate_status()

		else:
			navigables = self.navigate(locator)
			for i, navigable in navigables:
				if i < 0:
					log.error('{0} does not exist in {1}'.format(locator, self.name))
					return

				if navigable.is_closed(): continue
				if navigable.is_hidden(): continue

				navigable.update()

		if not self.parent is None:
			self.parent.evaluate_status()

		self.finished_processes   = 0
		self.total_processes      = 0
		raw_percentage            = 0.0
		self.completion           = '0.0%'

		for navigable in self:
				self.finished_processes += navigable.finished_processes
				self.total_processes += navigable.total_processes

		if not self.total_processes == 0:
			raw_percentage  = float(self.finished_processes)/float(self.total_processes)
			self.completion = '{0:.1%}'.format(raw_percentage)

			self.completion_time_series.append((time.time(), raw_percentage))


	## ---------------------------------------------------------
	def generate_list(self, attribute, locator='', status=None):
		"""
		generates a list containing a particular attribute of the lowest level navigable
		"""

		values = []

		if hasattr(self, attribute):
			if status is None:
				return self.parent, [getattr(self, attribute)]
			else:
				if self.status == definitions.kbook_status_reversed[status]:
					return self.parent, [getattr(self, attribute)]
				else:
					return self.parent, []

		else:
			for navigable in self:
				current_parent, current_list = navigable.generate_list(attribute, status=status)
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
			minimum_status = definitions.CLOSED
			for navigable in self:
				if navigable.is_hidden(): continue
				navigable_status = navigable.evaluate_status()
				if navigable_status < minimum_status:
					minimum_status = navigable_status
			self.status = minimum_status
			return self.status


	## ---------------------------------------------------------
	def make_completion_graph(self, path):
		"""
		Generates a graph of the completion time
		"""

		try:
			import ROOT
		except ImportError:
			log.error('ROOT is not setup. Please setup ROOT if you wish to make completion graphs.')
			return

		colors = [ROOT.kBlue-2, ROOT.kGreen-2, ROOT.kRed-2, ROOT.kCyan+2, ROOT.kOrange-3, ROOT.kViolet+2]

		graph = ROOT.TGraph()

		for i, datum in enumerate(self.completion_time_series):
		    unix_time = datum[0]
		    completion = datum[1]
		
		    graph.SetPoint(i, unix_time, completion*100.0)
		
		canvas = ROOT.TCanvas()
		canvas.SetGrid(1,1)
		
		xaxis = graph.GetXaxis()
		yaxis = graph.GetYaxis()
		
		xaxis.SetTitle('Time')
		xaxis.SetTimeDisplay(1)
		xaxis.SetTimeFormat('%d/%m %H')
		xaxis.SetTitleSize(0.05)
		xaxis.SetTitleOffset(0.7)
		
		yaxis.SetTitle('Completion [%]')
		yaxis.SetTitleSize(0.06)
		yaxis.SetTitleOffset(0.7)
		
		current_navigable_for_graph_name = self
		graph_name = current_navigable_for_graph_name.name
		while not current_navigable_for_graph_name.parent.name == 'book':
			if hasattr(current_navigable_for_graph_name.parent, 'version'):
				graph_name = '{0}.v{1}-{2}'.format(current_navigable_for_graph_name.parent.name, current_navigable_for_graph_name.parent.version, graph_name)
			else:
				graph_name = '{0}-{1}'.format(current_navigable_for_graph_name.parent.name, graph_name)
			current_navigable_for_graph_name = current_navigable_for_graph_name.parent

		graph.SetTitle(graph_name)
		graph.SetLineColor(ROOT.TColor.GetColor('#1F78B4'))
		graph.SetLineWidth(2)
		graph.SetMarkerStyle(20)
		graph.SetMarkerSize(0.5)

		graph.SetMinimum(0)
		graph.SetMaximum(100)
		
		graph.Draw('APL')

		if self.level == 1:
			for i, job in enumerate(self):
			    box = ROOT.TBox()
			    #box.SetFillColorAlpha(colors[i%len(colors)], 0.45)
			    box.SetFillColor(colors[i%len(colors)])
			    box.SetFillStyle(3001)
			    box.DrawBox(max(job.creation_time, self.completion_time_series[0][0]), 5+5*i, self.completion_time_series[-1][0], 9+5*i)

			    line = ROOT.TLine()
			    line.SetLineColorAlpha(colors[i%len(colors)], 0.45)
			    line.SetNDC(False)
			    line.DrawLine(max(job.creation_time, self.completion_time_series[0][0]), 5+5*i, max(job.creation_time, self.completion_time_series[0][0]), 100)
			    
			    tex = ROOT.TLatex()
			    tex.SetTextColor(ROOT.kBlack)
			    tex.SetTextAlign(30)
			    tex.SetTextSize(0.03)
			    tex.SetNDC(False)
			    tex.DrawLatex(self.completion_time_series[-1][0] - 0.01*(self.completion_time_series[-1][0] - self.completion_time_series[0][0]), 5+5*i, job.name)
		
		canvas.Print(os.path.join(path, '{0}.png'.format(graph_name)))


	## ---------------------------------------------------------
	def is_not_submitted(self) : return self.status == definitions.NOT_SUBMITTED
	def is_cancelled(self)     : return self.status == definitions.CANCELLED
	def is_unfinished(self)    : return self.status == definitions.UNFINISHED
	def is_running(self)       : return self.status == definitions.RUNNING
	def is_finished(self)      : return self.status == definitions.FINISHED
	def is_closed(self)        : return self.status == definitions.CLOSED
	def is_hidden(self)        : return self.hide < 0











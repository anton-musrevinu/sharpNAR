from .SddBaseManager import SddBaseManager
from .Algorithm_ModelEnumeration import Algorithm_ModelEnumeration
from .SddStructure import BoolNode, DecNode, LitNode
from BitVector import BitVector
import itertools
import threading
from queue import Queue
import traceback

class Algorithm_ModelEnumeration_Par(Algorithm_ModelEnumeration):

	VERSION_RAM = "VERSION_RAM"
	VERSION_DISK = "VERSION_DISK"

	def __init__(self,name, logger,threads = 1,pathToModels = None,version = VERSION_RAM):
		super(Algorithm_ModelEnumeration,self).__init__(name,logger)
		self._processed = 0
		self._pathToModels = pathToModels		
		if threads < 1:
			raise Exception("Number of desired threads to low: {}".format(threads))
		self._threads = threads
		self._version = version
		if version == Algorithm_ModelEnumeration_Par.VERSION_RAM:
			self.models = {}
		self._lock = threading.Lock()
		self._queue = None
		self._processedNodes = {}

	def startAlgorithm(self, stopEvent):
		self._stopEvent = stopEvent

		if self._isFalse(self._root):
			self._logger.writeToLog("\tProblem in UNSAT")
			self.setResult([])
			return

		self._processed = 2
		self._queue = list()
		workers = []
		for nodeId in self._nodes.keys():
			self._processedNodes[nodeId] = threading.Event()
		# Create 8 worker threads
		for nodeId in self._originalOrder[::-1]:
			if not isinstance(self._nodes[nodeId],BoolNode):
				self._queue.append(nodeId)

		for x in range(self._threads):
			worker = threading.Thread( target=self.runThread, args=('Thread-{}'.format(x),))
			# Setting daemon to True will let the main thread exit even though the workers are blocking
			#worker.daemon = True
			worker.start()
			workers.append(worker)
		# Put the tasks into the queue as a tuple
		# Causes the main thread to wait for the queue to finish processing all the tasks
		if self._stopEvent.is_set():
			self._logger.error('Stop flag is set after queue.join()')
			self.setResult([])
			return
		#print('queue finished, waiting on workers now',workers)
		for w in workers:
			w.join()
		
		if self._version == Algorithm_ModelEnumeration_Par.VERSION_RAM:
			models = modelsEnumeration[self._root] 
		elif self._version == Algorithm_ModelEnumeration_Par.VERSION_DISK:
			models = self.readModelsFromFile(self._root)	
			models, leng = self._getLengthOfGen(models)

		if self._varFullCount != len(self._varMap):
			self._logger.writeToLog('\t\t4.5/5 Finished traversing the tree, completing the models.')
			mask1 = self._vtreeMan.getScope(self._nodes[self._root].vtreeId) #List of Varids
			mask2 = self._vtreeMan.getScope(self._vtreeMan.getRoot())
			missing = list(set(mask2) - set(mask1))
			models = self._completeModelsGen(models,missing)

		self.setResult(models)
		return

	def runThread(self,name):
		#self._logger.test("Starting : {}, id: {}, #threads: {}".format(name, threading.currentThread(), threading.active_count()))
		nodeId = -1
		try:
			while True:
				# Get the work from the queue and expand the tuple
				nodeId = -1
				with self._lock:
					if not self._queue:
						break
					nodeId = self._queue.pop()
				t = self._computeNodeME(nodeId)
				self._saveModels(nodeId,t)
				self._processedNodes[nodeId].set()
				if self._stopEvent.is_set():
					return
		except Exception as e:
			self._logger.error("ERROR \"{}\" caught in thread name: {}, {}".format(e, name,threading.currentThread()))
			self._logger.error(traceback.format_exc())
			self._stopEvent.set()
			while True:
				if self._queue.empty():
					break
				t = self._queue.get()
				self._queue.task_done()

			self._logger.error("queue {} is empty now: {}, #threads: {}".format(self._queue ,self._queue.empty(),threading.active_count()))
			return
		return

			#print('====> Setting and notifyieng the lock of {} by thread: {}'.format(nodeId, threading.currentThread()))
			#print(self.queue)

	def _saveModels(self,nodeId, models):
		if self._version == self.VERSION_DISK:
			self.writeModelsToFile(nodeId,models)
		elif self._version == self.VERSION_RAM:
			with self._lock:
				self.models[nodeId] = models  
			#print('Saving : len: {}'.format(sum(1 for x in returnModels)))

	def _readModels(self,nodeId):
		if self._version == self.VERSION_DISK:
			return self.readModelsFromFile(nodeId)
		elif self.version == self.VERSION_RAM:
			saveModels, returnModels = itertools.tee(self.models[nodeId],2)
			self._models[nodeId] = saveModels   
			return returnModels

	def _computeNodeME(self,nodeId):
		#self.findPermutation()
		"""Retruns a list of models that satisry this node.

		Each Model is a dict between varId's and Truth assignments (True, Flase)
		"""
		node = self._nodes[nodeId]

		if isinstance(node,LitNode):
			model = BitVector(size = self._varFullModelLength)
			model[node.varId] = (0 if node.negated else 1)
			node.models = list([model])
			return node.models

		if not isinstance(node,DecNode):
			raise Exception("WRONG FORMAT: {}".format(type(node)))

		nodeModels = []
		tmpModels = []
		singleValue = []
		nodeMask = node.scope
		for i,(p,s) in enumerate(node.children):
			if self._isFalse(p) or self._isFalse(s):
				continue
			if self._isTrue(p):
				self._processedNodes[s].wait()
				tmpModels = self._readModels(s)
			elif self._isTrue(s):
				#read prime
				self._processedNodes[p].wait()
				tmpModels = self._readModels(p)
			else:
				self._processedNodes[p].wait()
				self._processedNodes[s].wait()
				#read both nodes (ether dec nodes or lit nodes)
				tmpModels= self._product(self._readModels(p),\
					self._readModels(s))

			#------ complete the computed models
			try:
				if node.scopeCount != self._nodes[p].scopeCount + self._nodes[s].scopeCount:
					tmpModels = self._completeModelsNew(tmpModels,nodeMask,p, s)
			except Exception as e:
				self._logger.error("{},{},{},{},{}".format(node.id,p,s, node, self._nodes))
				self._logger.error("{},{},{}".format(node.scopeCount, self._nodes[p].scopeCount,\
				 self._nodes[s].scopeCount))
				raise e

			#------ Store the models(to disk or into the node)
			nodeModels = itertools.chain(nodeModels,tmpModels)

		#------ return the models
		return nodeModels

	def getModelCount(self):
		if not self._resultComputed:
			return None

		if self._version == Algorithm_ModelEnumeration_Par.VERSION_DISK:
			modelCount = self.getModelCountFromFile(self._root)
		elif self._version == Algorithm_ModelEnumeration_Par.VERSION_RAM:
			self._result, modelCount = self._getLengthOfGen(self._result)

		return modelCount

	def setResult(self,result):
		if not result:
			return None

		if self._version == Algorithm_ModelEnumeration_Par.VERSION_DISK:
			modelCount = self.writeModelsToFile(self._root,result)
		elif self._version == Algorithm_ModelEnumeration_Par.VERSION_RAM:
			self._result = result

		self._resultComputed = True










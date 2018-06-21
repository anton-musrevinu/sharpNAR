import z3
import logging
import itertools
from .Interval import Interval
import math
from .Predicate import Predicate
from .Manager import Manager
from .mylogger import Mylogger
from .AbstractionManager import AbstractionManager
from .myExceptions import AbstractionCondition
import time


class QueryManager(object):
	#hold a formula and the corresponding Vars and stuff

	INTEGRATION_MI = 'INTEGRATION_MI'
	INTEGRATION_WMI = 'INTEGRATION_WMI'
	
	def __init__(self,name,tmpDir,logger = None):
		# this dictonary identifies a number with a propositional letter and the abstraction
		if logger == None:
			self._logger = MyLogger()
		else:
			self._logger = logger
		self._logger = logger
		self._name = name
		self._queryName = name + '-query'
		self._tmpDir = tmpDir
		self._baseSMT = None
		self._smtFormat = None

		self._baseManager = None
		self._baseAbstractionManager = None
		self._baseWeightFucntionString = None
		self._computedIntervals = None

		self._baseWMI = None

	def _listToStringList(self,listl):
		t = []
		for i in listl:
			t.append(str(i))
		return t

	def initBaseManager(self,smtString,weihtFucntionString = None,smt = 'SMT',verbose = False):
		if not smt == 'SMT1':
			raise Execption('INVALID SMT FORMAT')
		self._smtFormat = smt

		#INIT Base Abstraction Manager
		self._baseAbstractionManager = AbstractionManager(self._name, self._logger)
		try:
			self._baseAbstractionManager.parseSmt1String(smtString)
			if weihtFucntionString != None:
				self._baseAbstractionManager.parseSmt1WeightFunction(weihtFucntionString, self._tmpDir)
		except AbstractionCondition as e:
			#print("Conditions on input not met: {}".format(e))
			self._logger.error("Conditions on input not met: {}".format(e))
			return False

		#Write abstracted KB to CNF file
		self._baseAbstractionManager.saveToDemacs(self._tmpDir + self._name)

		self._baseManager = Manager(self._name,tmpDir = self._tmpDir, cnfDir =  self._tmpDir,sddDir = self._tmpDir, logger = self._logger)
		compiled, compileTime = self._baseManager.compileSDD(verbose = False)
		if compiled != Manager.INDICATOR_ALLGOOD:
			raise Exception("!!!!! FAILED: compiling:  {}, {}".format(self._tmpDir, compileTime))

		self._baseSMT = smtString
		self._baseWeightFucntionString = weihtFucntionString
		self._computedIntervals = {}

		return True

	def performQuery(self,smtQuery, smt = 'SMT1', verbose = False, integration = INTEGRATION_MI,intError = None):
		if smt != self._smtFormat:
			raise Execption('NOT MATCHING SMT FORMATS')

		if not self._baseManager:
			self._logger.error("BASE MANAGER NOT INITIALIZED YET")
			return

		time_start = time.time()

		#Initialize query Abstraction manager]
		queryAbst = AbstractionManager(self._queryName, self._logger)
		queryAbst.parseSmt1String(self._baseSMT)
		if self._baseWeightFucntionString != None:
			queryAbst.parseSmt1WeightFunction(self._baseWeightFucntionString, self._tmpDir)

		queryAbst.parseAndAppendSmt1String(smtQuery)
		#Write abstracted KB conjoined with query to CNF file
		queryAbst.saveToDemacs(self._tmpDir + self._queryName)
		queryAbst.setComputedIntervals(self._computedIntervals)
		
		#compile propositional kb to sdd
		queryMan = Manager(self._queryName,tmpDir = self._tmpDir, cnfDir =  self._tmpDir,sddDir = self._tmpDir, logger = self._logger)
		indicator, compileTime = queryMan.compileSDD(verbose = False)
		if indicator != Manager.INDICATOR_ALLGOOD:
			raise Exception("!!!!! FAILED: compiling:  {}, {}".format(self._tmpDir, compileTime))

		if integration == QueryManager.INTEGRATION_MI:
			if self._baseWMI == None:
				self._baseWMI = self.getSharpSmt(self._baseManager, self._baseAbstractionManager,verbose = verbose)
				#self._logger.test('\tMI Original: ({},{},{})'.format(*self._baseWMI))
			(modelIntegrationO, errorO, exectime) = self._baseWMI

			(modelIntegrationQ, errorQ, exectime) = self.getSharpSmt(queryMan, queryAbst, verbose = verbose)
			intData = None
			#self._logger.test('\tMI Query: ({},{},{})'.format(modelIntegrationQ, errorQ, exectime))
		elif integration == QueryManager.INTEGRATION_WMI:
			if self._baseWMI == None:
				self._baseWMI = self.getWMISmt(self._baseManager, self._baseAbstractionManager,verbose = verbose, intError = intError)
				(modelIntegrationO, errorO, exectime1, (iTime1, inb1)) = self._baseWMI
				(modelIntegrationQ, errorQ, exectime, (iTime, inb)) = self.getWMISmt(queryMan, queryAbst, verbose = verbose, intError = intError)
				exectime = exectime + exectime1
				intData = (iTime + iTime1, inb + inb1)
				#self._logger.test('\tMI Original: ({},{},{})'.format(*self._baseWMI):
			else:
				(modelIntegrationO, errorO, exectime, intData) = self._baseWMI
				(modelIntegrationQ, errorQ, exectime, intData) = self.getWMISmt(queryMan, queryAbst, verbose = verbose, intError = intError)
			#self._logger.test('\tMI Query: ({},{},{}), intervals: {}'.format(modelIntegrationQ, errorQ, exectime, len(self._computedIntervals)))
			#self._logger.test("\t --> Intervals: {}".format(str(self._computedIntervals)))

		end_time = time.time()

		del queryMan


		#self._logger.test('Resulting probability Pr(q,e) = MI(A and Q)/MI(A) = {}/{} = {}'.format(modelIntegrationQ,modelIntegrationO,modelIntegrationQ/modelIntegrationO))
		if modelIntegrationQ == 0 and modelIntegrationO == 0:
			return 0, (end_time - time_start), exectime, intData
		else:
			return modelIntegrationQ/modelIntegrationO, (end_time - time_start), exectime, intData

	def getSharpSmt(self,sddManager, abstractionManager, algorithm = Manager.ALGORITHM_ME_RAM,\
		timeout = Manager.DEF_TIMEOUT_ME, verbose = False):
		"""Calculates the Model Integration for a fiven SDD(sddManager)
			Inputs: sddManager to perform representing the KB we want to query"""
		
		(indicator, models, execTime) = sddManager.getModelEnumerate(algorithm, timeout, verbose)
		if indicator != Manager.INDICATOR_ALLGOOD:
			raise Exception("!!!!! FAILED: Enumerating with algorithm {}, errorCode: {}".format(algorithm, indicator))

		start_time = time.time()
		modelIntegrate = 0
		for i,model in enumerate(models):
			#self._logger.test('Model {} :\t {}\n{}'.format(i,model, models))
			vol = abstractionManager.vol_no_weight(model)
			modelIntegrate += vol

		end_time = time.time()
		total_time = (end_time - start_time) + execTime

		return (modelIntegrate, '-1', total_time)

	def getWMISmt(self,sddManager, abstractionManager, algorithm = Manager.ALGORITHM_ME_RAM,\
			timeout = Manager.DEF_TIMEOUT_ME, verbose = False,intError = None):
		"""Calculates the Model Integration for a fiven SDD(sddManager)
			Inputs: sddManager to perform representing the KB we want to query"""
		
		(indicator, models, execTime) = sddManager.getModelEnumerate(algorithm, timeout, verbose)
		if indicator != Manager.INDICATOR_ALLGOOD:
			raise Exception("!!!!! FAILED: Enumerating with algorithm {}, errorCode: {}".format(algorithm, indicator))

		self._logger.setVerbose(False)
		start_time = time.time()
		wmi = 0
		integrationError = 0
		intTime = 0
		intnb = 0
		for i,model in enumerate(models):
			#self._logger.test('Model {} :\t {}\n{}'.format(i,model, models))
			(vol,error,integrationData) = abstractionManager.vol_single_weight(model,intError)
			wmi += vol
			integrationError += error
			intTime += integrationData[0]
			intnb += integrationData[1]

		end_time = time.time()
		total_time = (end_time - start_time) + execTime

		self._logger.setVerbose(False)

		self._computedIntervals.update(abstractionManager.getComputedIntervals())
		return (wmi, integrationError, total_time,(intTime, intnb))











#logger
import traceback
import logging
import datetime
from .myExceptions import TestException

class Mylogger(object):

	def __init__(self,logger = None, loggerResults = None, name = None):
		self._logger = logger
		self._loggerResults = loggerResults
		self._verboseAlgorithm = False
		self._currentlyTesting = False
		self._leng = 160
		self._indent = 20
		self._processed = 0


		if name != None:
			self.startBenchMarkProblem(name,phrase = "Starting Benchmark : ", sym = '=')
			self.endBenchMark()

	def setVerbose(self,verbose):
		self._verboseAlgorithm = verbose

	def getVerbose(self):
		return self._verboseAlgorithm

	def testing(self):
		return self._currentlyTesting

	def logProcessed(self,nodeId,maxP):
		self._logger.debug('\t Processed: {}/{} -- NodeId: {}'.format(self._processed, nodeId, maxP))
		self._processed += 1

	def resetProgress(self):
		self._processed = 0

	def writeToLog(self,message,level = 'debug'):

		if self._currentlyTesting and self._verboseAlgorithm:
			print(level + ' --> ' + message)
			return
		if self._currentlyTesting and level == 'info' or level == 'error':
			print(level + '--> ' + message)
			return

		if self._logger == None:
			return

		if level == 'debug':
			if self._verboseAlgorithm:
				self._logger.debug(message)
		elif level =='info':
			self._logger.info(message)
		elif level == 'error':
			self._logger.error(message)


	def result(self,message):
		if self._loggerResults and not self._currentlyTesting:
			self._loggerResults.info(message)
		#self.writeToLog("===== Result: " + message,'info')
		if self._logger == None:
			print(message)


	def startBenchMarkProblem(self,name,inputs = None,phrase = 'Starting on BenchMarkProbelm', sym = '-'):

		self.writeToLog(sym * self._leng,'info')
		msg = '{} {}'.format(phrase,name)
		spaces = int((self._leng - (2 * self._indent + len(msg)))/2)
		self.writeToLog(sym * self._indent + ' ' * spaces + msg + ' ' * spaces + sym * self._indent,'info')
		if inputs != None:
			self.benchmarkAddInput(inputs)


	def benchmarkAddInput(self,inputs):
		self.writeToLog("\t" + 'Input: {}'.format(inputs),'info')


	def endBenchMark(self, sym = '='):
		self.writeToLog(sym * self._leng,'info')
		self.writeToLog('\n\n','info')



	def error(self,message):
		if self._currentlyTesting:
			print('ERROR: {}'.format(message))
		if self._logger:
			self._logger.error(message)
			#self._logger.error(traceback.format_exc())

	def testFail(self,message):
		if self._logger:
			self._logger.error(message)
		else:
			print(message)
		raise TestException

	def test(self,message):
		if self._currentlyTesting and self._logger:
			self._logger.debug(message)
		elif self._currentlyTesting:
			print('TESTING: {}'.format(message))

	def __str__(self):
		return 'logger: self.logger: {}, self._loggerResults: {}, self._verboseAlgorithm: {}, self._currentlyTesting: {}'.format(self._logger,self._loggerResults,self._verboseAlgorithm,self._currentlyTesting)






import os
import time
import sys
import datetime
import logging
from sharpsmt.Manager import Manager
from sharpsmt.mylogger import Mylogger
from sharpsmt.QueryManager import QueryManager
from tests.TestModel import TestModel
from subprocess import STDOUT, check_output
import psutil
import platform
import gc
import traceback
from z3me.enumerate_z3 import Z3Manager
import numpy as np

class Benchmark(object):

	def __init__(self,console1 = False,console2 = False):
		self._console1 = console1
		self._console2 = console2

	def initLogging(self,name,level,console):
		path = './benchmarks/out/'
		filename = path + "{}_{}.log".format(name,datetime.datetime.now())
		#logging.basicConfig(filename=filename, level=logging.INFO)

		l = logging.getLogger(name)
		formatter = logging.Formatter('%(asctime)s ; %(message)s')
		fileHandler = logging.FileHandler(filename, mode='w')
		fileHandler.setFormatter(formatter)
		streamHandler = logging.StreamHandler()
		streamHandler.setFormatter(formatter)

		l.setLevel(level)
		l.addHandler(fileHandler)

		if console:
			l.addHandler(streamHandler) 
		#l.disabled = False
		return l

	def benchmarkSddCompile(self,path,timeout):
		allLogger = self.initLogging("benchmark_sdd_compile",logging.DEBUG,self._console1)
		resultsLogger = self.initLogging("benchmark_sdd_compile_results",logging.INFO,self._console2)
		logger = Mylogger(allLogger, resultsLogger,'benchmark_sdd_compile')

		inputDir = './../mcbenchmarks/cnf/'
		outputDir = './../mcbenchmarks/sdd/'


		fileDir = os.path.dirname(os.path.realpath('__file__'))
		filename = os.path.join(fileDir, inputDir)
		inputDirAbs = os.path.abspath(os.path.realpath(filename))

		filename = os.path.join(fileDir, outputDir)
		outputDirAbs = os.path.abspath(os.path.realpath(filename))

		logger.setVerbose(False)
		problems = []

		with open(path, "r") as file:
			for i,problem in enumerate(file):
				problems.append(problem)
		sdd = ''

		for problem in problems:
			if problem[0] == '#':
				continue
			try:
				problem = problem.split(',')
				#logging.debug(problem)
				sdd = '/' + str(problem[0]).replace('\n','')
				for line in open('{}.cnf'.format(inputDirAbs +  sdd)):
					if line[0] == 'c':
						continue
					elif line[0] == 'p':
						line = line.split()
						nbVars = int(line[2])
						nbClauses = int(line[3])
						break
					else:
						logging.debug(line)
						continue 

				logger.startBenchMarkProblem(sdd,' nbVars: {}, nbClauses: {}, freeMemory {}'.format(\
					nbVars,nbClauses,psutil.virtual_memory()[2]))

				manager = Manager(sdd,tmpDir = None, sddDir = outputDirAbs, cnfDir = inputDirAbs, logger = logger)
				if not manager.checkIfFilesExist('cnf'):
					logger.result('COMPILE,{},{}'.format(sdd,'NOT COMPUTED: FILE DOES NOT EXIST'))
					continue


				compiled, compileTime = manager.compileSDD(timeout = timeout, verbose = False)

				logger.writeToLog('\tComiling to SDD finished after ,{},s'.format(compileTime))
				logger.result('SddCompile,{},{}\t,{}\t,{}\t,{}'.format(sdd,nbVars,nbClauses, compileTime,compiled))
			except Exception as e:
				logger.result('SddCompile,{},{}'.format(sdd,'NOT COMPUTED: ' + str(e)))
				logger.error(e)
				logger.error(traceback.format_exc())
			finally:
				logger.endBenchMark()

	def benchmarkZ3Enumerate(self,path,timeout):
		allLogger = self.initLogging("benchmark_z3_enumerate",logging.DEBUG,self._console1)
		resultsLogger = self.initLogging("benchmark_z3_enumerate_results",logging.INFO,self._console2)
		logger = Mylogger(allLogger, resultsLogger,'benchmark_z3_enumerate')

		inputDir = './../mcbenchmarks/cnf/'


		fileDir = os.path.dirname(os.path.realpath('__file__'))
		filename = os.path.join(fileDir, inputDir)
		inputDirAbs = os.path.abspath(os.path.realpath(filename))

		problems = []

		with open(path, "r") as file:
			for i,problem in enumerate(file):
				problems.append(problem)
		sdd = ''

		for problem in problems:
			if problem[0] == '#':
				continue
			try:
				problem = problem.split(',')
				#logging.debug(problem)
				sdd = '/' + str(problem[0]).replace('\n','')

				manager = Z3Manager(inputDirAbs,sdd, logger = logger)
				modelCountTime,modelCount = manager.enumerateModels(timeout)
				logger.result('ME,#threads {},{},{}\t,{}\t,{}\t,{}\t,{}\t,{}'.format(1,"Z3_Enumerate",sdd,"-","-",modelCountTime,modelCount,"-"))

			except Exception as e:
				logger.error(e)
				logger.error(traceback.format_exc())
			# finally:
			# 	#return

	def benchmarkModelCounting(self,path,timeout,threads = 1):
		allLogger = self.initLogging("benchmark_ALGORITHM_MC_BASIC",logging.DEBUG,self._console1)
		resultsLogger = self.initLogging("benchmark_ALGORITHM_MC_BASIC_results",logging.INFO,self._console2)

		logger = Mylogger(allLogger,resultsLogger,'benchmark_mc_basic')

		logger.setVerbose(False)

		myDir = './../mcbenchmarks/sdd/'

		fileDir = os.path.dirname(os.path.realpath('__file__'))
		filename = os.path.join(fileDir, myDir)
		inputDirAbs = os.path.abspath(os.path.realpath(filename))

		
		problems = []
		with open(path, "r") as file:
			for i,problem in enumerate(file):
				problems.append(problem)
		sdd = ''
		for problem in problems:

			manager = None
			if problem[0] == '#':
				continue
			try:

				problem = problem.split(',')

				#for i in range(threads):

				sdd = str(problem[0]).replace('\n','')
				logger.startBenchMarkProblem(sdd)

				manager = Manager(name = sdd,sddDir = inputDirAbs, logger = logger)
				if not manager.checkIfFilesExist('sdd'):
					logger.result('MC,{},{}\t,{}'.format('basic',sdd,'NOT COMPUTED: FILE DOES NOT EXIST'))
					continue
				
				modelCount, modelCountTime = manager.getModelCount(algorithm = Manager.ALGORITHM_MC_BASIC,\
				 timeout = timeout, verbose = False, threads= threads)

				varCount = manager.getTotalVariabelCount()
				nodeCount = manager.getNodeCount()
				logger.writeToLog('\t ModelCount finished after ,{}, s with ModelCount ,{}'.format(modelCountTime,modelCount),'info')
				logger.result('MC,basic,#threads: {},{}\t,{}\t,{}\t,{}\t,{}'.format(1,sdd,nodeCount,varCount,modelCountTime,modelCount))

			except Exception as e:
				logger.result('MC,{},{}\t,{}'.format('basic',sdd,'NOT COMPUTED: ' + str(e)))
				logger.error(e)
				logger.error(traceback.format_exc())
			finally:
				logger.endBenchMark()
				if manager:
					manager.freeMemory()
				del manager

	def benchmarkModelEnumeration(self,path,timeout,algorithm,threads = 1):
		allLogger 		= self.initLogging("benchmark_{}".format(algorithm),logging.DEBUG,self._console1)
		resultsLogger	= self.initLogging("benchmark_{}_results".format(algorithm),logging.INFO,self._console2)
		logger = Mylogger(allLogger,resultsLogger,'benchmark_{}'.format(algorithm))

		myDir = './../mcbenchmarks/sdd/'
		tmpDir = './tmp_files/'

		fileDir = os.path.dirname(os.path.realpath('__file__'))
		filename = os.path.join(fileDir, myDir)
		inputDirAbs = os.path.abspath(os.path.realpath(filename))

		filename = os.path.join(fileDir, tmpDir)
		tmpDirAbs = os.path.abspath(os.path.realpath(filename))

		problems = []
		with open(path, "r") as file:
			for i,problem in enumerate(file):
				problems.append(problem)
		sdd = ''
		for problem in problems:
			if problem[0] == '#':
				continue

			manager = None
			try:

				problem = problem.split(',')

				#for numThreads in range(threads):
				numThreads = threads


				sdd = str(problem[0]).replace('\n','')
				logger.startBenchMarkProblem(sdd)

				manager = Manager(sdd,tmpDir = tmpDir, sddDir = inputDirAbs, logger = logger)
				if manager.checkIfFilesExist('sdd') != True:
					logger.result('ME,{},{},{}\t, -> Not Computed since file: {} does not exist'.format(algorithm,numThreads,sdd,manager.checkIfFilesExist('sdd')))
					continue

				manager.initAlgorithm(algorithm = algorithm,verbose = False, threads = numThreads)
				varCount = manager.getTotalVariabelCount()
				sddSize = manager.getSddSize()

				logger.benchmarkAddInput('#threads: {} sddSize: {}, varCount: {}, freeMemory {}'.format(\
				numThreads, sddSize,varCount,psutil.virtual_memory()[2]))
				
				modelCount, modelCountTime = manager.getModelCount(timeout = timeout, verbose = False)
				nodesTraversed = manager.getNodesTraversed()

				sdd = sdd + " " * (35 - len(sdd))

				logger.writeToLog('\t Model Enumeration {} finished after ,{}, s with ModelCount ,{}, traversedNodes,{},'.format(algorithm,modelCountTime,modelCount,nodesTraversed),'info')
				logger.result('ME,#threads {},{},{}\t,{}\t,{}\t,{}\t,{}\t,{}'.format(numThreads,algorithm,sdd,sddSize,varCount,modelCountTime,modelCount,nodesTraversed))
			except Exception as e:
				logger.result('ME,{},{}\t,{}'.format(algorithm,sdd,'NOT COMPUTED: ' + str(e)))
				logger.error(e)
				logger.writeToLog(traceback.format_exc(),'error')
			finally:
				logger.endBenchMark()
				if manager:
					manager.freeMemory()
				del manager
				gc.collect()
				time.sleep(1)



	def benchmarkCalculateSize(self,path,timeout):
		myDir = './../mcbenchmarks/sdd/'
		logger = Mylogger()

		fileDir = os.path.dirname(os.path.realpath('__file__'))
		filename = os.path.join(fileDir, myDir)
		inputDirAbs = os.path.abspath(os.path.realpath(filename))

		problems = []
		with open(path, "r") as file:
			for i,problem in enumerate(file):
				problems.append(problem)
		sdd = ''
		for problem in problems:
			if problem[0] == '#':
				continue

			manager = None
			try:

				problem = problem.split(',')

				sdd = str(problem[0]).replace('\n','')
				manager = Manager(sdd, sddDir = inputDirAbs, logger = logger)
				if manager.checkIfFilesExist('sdd') != True:
					logger.result('ME,{},{},{}\t, -> Not Computed since file: {} does not exist'.format(algorithm,numThreads,sdd,manager.checkIfFilesExist('sdd')))
					continue

				manager.initAlgorithm(algorithm = Manager.ALGORITHM_COMPILE,verbose = False, threads = 1)
				print(sdd, manager.getSddSize())

			except Exception as e:
				logger.error(e)
				logger.writeToLog(traceback.format_exc(),'error')

	def doBenWMI(self):
		path = "/input.txt"
		error = (1,1)
		benchName = 'WMI'
		allLogger 		= self.initLogging("benchmark_{}".format(benchName),logging.DEBUG,self._console1)
		resultsLogger	= self.initLogging("benchmark_{}_results".format(benchName),logging.INFO,self._console2)
		logger = Mylogger(allLogger,resultsLogger,'benchmark_{}'.format(benchName))
		
		# for i in np.arange(1,0,-.1):
		# 	for j in np.arange(1,0,-.1):
		# 		error = (i,j)
		# 		self.benchmarkWMI(path,logger,intError = error, algorithm = QueryManager.INTEGRATION_WMI)
		error = (1,1)
		
		self.benchmarkWMI(path,logger,intError = error, algorithm = QueryManager.INTEGRATION_WMI)

	def doBenMI(self):
		path = "/input.txt"
		benchName = 'MI'
		allLogger 		= self.initLogging("benchmark_{}".format(benchName),logging.DEBUG,self._console1)
		resultsLogger	= self.initLogging("benchmark_{}_results".format(benchName),logging.INFO,self._console2)
		logger = Mylogger(allLogger,resultsLogger,'benchmark_{}'.format(benchName))

		self.benchmarkWMI(path,logger, algorithm = QueryManager.INTEGRATION_MI)


	def benchmarkWMI(self,path,logger,intError = None, algorithm = QueryManager.INTEGRATION_MI):
		if algorithm == QueryManager.INTEGRATION_WMI:
			instName = "{}-{}".format(algorithm,intError)
			logger.startBenchMarkProblem(instName)

		benchDir = './../smtbenchmarks/XADD'
		mytmpDir = './tmp_files/'



		fileDir = os.path.dirname(os.path.realpath('__file__'))
		tmpDir = os.path.join(fileDir, mytmpDir)
		tmpDir = os.path.abspath(os.path.realpath(tmpDir))

		files = []
		with open(benchDir + path, "r") as inputFile:
			for file in inputFile:
				file = '/' + file.replace('\n','')
				files.append(file)

		queryResults = []
		for file in files:

			propName = file

			logger.writeToLog('--- Starting on input: {}'.format(file),'info')

			testModel = TestModel(logger)
			testModel.setFunctionFromFile(benchDir + file)

			queryManager = QueryManager(propName, tmpDir, logger)
			indicator = queryManager.initBaseManager(testModel.getFunctionAsSmt1String(), testModel.getWeightFucntionAsString(),smt = 'SMT1',verbose = False)
			if not indicator:
				continue

			if not os.path.isfile(tmpDir + propName + '.cnf'):
					logger.writeToLog("!!!!! FAILED: FIle:  {} does not exist".format(tmpDir + propName + '.cnf'))
			if not os.path.isfile(tmpDir + propName + '.sdd'):
					logger.writeToLog("!!!!! FAILED: FIle:  {} does not exist".format(tmpDir + propName + '.sdd'))
			if not os.path.isfile(tmpDir + propName + '.vtree'):
					logger.writeToLog("!!!!! FAILED: FIle:  {} does not exist".format(tmpDir + propName + '.vtree'))
			if not os.path.isfile(tmpDir + propName + '_weightfunc.py'):
					logger.writeToLog("!!!!! FAILED: FIle:  {} does not exist".format(tmpDir + propName + '_weightfunc.py'))

			timeList = []
			diffList = []
			for i in testModel.getQueries():

				query = i[0]

				result,totalExectime, wmiExectime, intData = queryManager.performQuery(\
					query,smt = 'SMT1',verbose = False, integration = algorithm, intError = intError)

				diff = (result - float(i[1]))**2
				queryResults.append((diff,totalExectime, wmiExectime, intData))
				if algorithm == QueryManager.INTEGRATION_WMI:
					logger.result('{},{},\t{:.10f},\t{:.10f},\t{:.10f},\t{:.10f},\t{}'.format(intError[0],intError[1],diff,totalExectime, wmiExectime, intData[0], intData[1]))
					logger.writeToLog('iErr: {}, Name: {}, q: {}, lse: {:.10}, tT: {:.10}s, wmiT: {:.10}s, iT: {:.10}s, nbInts: {}'.format(\
						intError, propName, query, diff, totalExectime, wmiExectime, intData[0], intData[1]),'info')
				else:
					logger.result('{},{},\t{:.10f},\t{:.10f},\t{:.10f},\t{:.10f},\t{}'.format(-1,-1,diff,totalExectime, wmiExectime, -1, -1))
					logger.writeToLog('iErr: {}, Name: {}, q: {}, lse: {:.10f}, tT: {:.10f}s, wmiT: {:.10f}s, iT: {:.10f}s, nbInts: {}'.format(\
						-1, propName, query, diff, totalExectime, wmiExectime, -1, -1),'info')

if __name__ =='__main__':

	benchmark = Benchmark(True,False)
	#benchmark.doBenMI()
	benchmark.doBenWMI()
	#benchmark.benchmarkZ3Enumerate(path, 60 * 60)
	# benchmark.benchmarkCalculateSize(path,60 * 60)
	# benchmark.benchmarkModelCounting(path, 60 * 60)
	# benchmark.benchmarkModelEnumeration(path, 60 * 30,SddManager.VERSION_DISK)




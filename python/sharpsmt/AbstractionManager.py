#Predicate abstraction
import z3
import logging
import itertools
from .Interval import Interval
import math
from .Predicate import Predicate
from .Function import Function
from scipy import integrate
import time

class AbstractionManager(object):
	#hold a formula and the corresponding Vars and stuff
	
	def __init__(self,name,logger):
		self._name = name
		self._smtInString = None
		# this should hold a Propositional Knowlege base
		self._kb = None
		# this dictonary identifies a number with a propositional letter and the abstraction
		self._predicates = {}
		self._groundVarRefernces = {}
		self._predicateToIndx = {}
		self._logger = logger
		self._weightFunction = None
		self._computedIntervals = {}


	'''-----------------------------------------------------------------------------------------'''
	'''----------                            General Methods                          ----------'''
	'''-----------------------------------------------------------------------------------------'''
	def getOriginalVarCount(self):
		return len(self._predicates)

	def getLogger(self):
		return self._logger

	def toCnf(self):
		#t = Then('simplify','nnf')
		#subgoal = t(simplify(self._kb))
		#self._logger.writeToLog("subgoal",subgoal)
		cnf = z3.simplify(self._toCnf(self._kb))
		cnflist = []
		if z3.is_and(cnf):
			for i in cnf.children():
				tmp = []
				if z3.is_or(i):
					for ii in i.children():
						if z3.is_const(ii) or z3.is_not(ii) and z3.is_const(ii.children()[0]):
							tmp.append(ii)
						else:
							self._logger.writeToLog("Wrongly formulated CNF")
							raise Exception
				elif z3.is_not(i) and z3.is_const(i.children()[0]):
					tmp.append(i)
				elif z3.is_const(i):
					tmp.append(i)
				else:
					self._logger.writeToLog("Wonrgly formulated CNF")
				cnflist.append(tmp)
		elif z3.is_or(cnf):
			tmp = []
			for i in cnf.children():
				if z3.is_const(i) or z3.is_not(i) and z3.is_const(i.children()[0]):
					tmp.append(i)
				else:
					self._logger.writeToLog("Wonrgly formulated CNF")
			cnflist.append(tmp)

		self._logger.writeToLog("Full Propositional KB in CNF: {}".format(cnflist))
		return cnflist
		#self._logger.writeToLog("RESULT: CNF",cnf)
		# return subgoal[0]

	def _toCnf(self, formula):
		if z3.is_or(formula):
			tmp = []
			ground = []
			for i in formula.children():
				tmp.append(self._toCnf(i))
			for i in tmp:
				if z3.is_and(i):
					ground.append(i.children())
				elif z3.is_const(i):
					ground.append([i])
				elif z3.is_not(i) and z3.is_const(i.children()[0]):
					ground.append([i])
				elif z3.is_or(i) and all(z3.is_const(elem) or z3.is_not(elem) and z3.is_const(elem.children()[0]) for elem in i.children()):
					for j in i.children():
						ground.append([j])
				else:
					self._logger.writeToLog("is_or, {},{}".format(formula,i))
					raise Exception
			result = []
			self._logger.writeToLog("CROSS: {}".format(ground))
			for i in itertools.product(*ground):
				self._logger.writeToLog('Writing to rsults: {},{}'.format(i,list(i)))
				result.append(z3.Or(i))
			self._logger.writeToLog('Resutl: {}'.format(result))
			result = z3.And(result)
			self._logger.writeToLog('ResutAnd: {}'.format(result))
			resultS = z3.simplify(result)
			self._logger.writeToLog("Result simplified: {}".format(resultS))
			return resultS

		elif z3.is_and(formula):
			tmp = []
			ground = []
			for i in formula.children():
				tmp.append(self._toCnf(i))
			for i in tmp:
				if z3.is_and(i):
					ground.extend(i.children())
				elif z3.is_const(i):
					ground.append(i)
				elif z3.is_not(i) and z3.is_const(i.children()[0]):
					ground.append(i)
				elif z3.is_or(i) and all(z3.is_const(elem) or z3.is_not(elem) and z3.is_const(elem.children()[0]) for elem in i.children()):
					ground.append(i)

				# SHoueld be ----> (1 v 2) and 3 --> (1 and 3 or 2 and 3) not just adding them to the and statement.... right ?
				else:
					self._logger.error("is_and, {}, {}".format(formula, i))
					raise Exception
			return z3.simplify(z3.And(ground))
		elif z3.is_not(formula):
			if z3.is_const(formula.children()[0]):
				return formula
			elif z3.is_not(formula.children()[0]):
				return self._toCnf(formula.children()[0])
			elif z3.is_and(formula.children()[0]):
				return self._toCnf(z3.Or([z3.Not(elem) for elem in formula.children()[0].children()]))
			elif z3.is_or(formula.children()[0]):
				return self._toCnf(z3.And([z3.Not(elem) for elem in formula.children()[0].children()]))
			else:
				self._logger.writeToLog("is_not({}) problem".formula(formula))
				raise Exception
		elif z3.is_const(formula):
			return formula
		else:
			self._logger.writeToLog("is_nothing problem",formula)

	def _isVar(self,elem):
		return any([z3.is_int_value(z3.simplify(elem)),z3.is_rational_value(z3.simplify(elem)),z3.is_algebraic_value(z3.simplify(elem)), is_const(z3.simplify(elem))])

	def kbToString(self):
		return str(self._kb)

	def getKb(self):
		return self._kb

	def getWeightFunction(self):
		return self._weightFunction

	def getPred(self):
		return self._predicates

	def letterMapToString(self):
		tmp = {}
		for k,v in self._predicates.items():
			tmp[k] = str(v)
		return tmp

	def __str__(self):
		return "FULL AbstractionManager as String: " + \
			"\n\tKB: {}\n\tPredicateMap: {}\n\tPredicateToIndx: {}\n\tGroundVars: {}".format(self.kbToString(), self.letterMapToString(),self._predicateToIndx, self._groundVarRefernces)


	def _abstraction(self, formula):
		newFormula = z3.simplify(formula)
		formula = newFormula

		if formula in self._predicateToIndx:
			return self._predicates[self._predicateToIndx[formula]].getBoolRef()
		idx = len(self._predicates) + 1
		p = Predicate(idx,formula)
		self._predicateToIndx[p.formula] = idx
		self._predicates[idx] = p
		for subVar in p.getSubVars():
			if subVar in self._groundVarRefernces:
				self._groundVarRefernces[subVar].append(idx)
			else:
				self._groundVarRefernces[subVar] = [idx]
		return p.getBoolRef()

	'''-----------------------------------------------------------------------------------------'''
	'''----------                            SMT 1.0 Methods                          ----------'''
	'''-----------------------------------------------------------------------------------------'''

	def _mapFunctionSymbol(self,symbol):
		if symbol == '&':
			return z3.And
		elif symbol == '|':
			return z3.Or
		elif symbol == '~':
			return z3.Not
		elif symbol == '<=':
			return self._leq
		elif symbol == '<':
			return self._le
		elif symbol == '*':
			return self._times
		elif symbol == '+':
			return self._plus
		elif symbol == '-':
			return self._minus
		else:
			raise Exception("WRONG SYMBOL FOUND : {}".format(symbol))

	def _le(self,lst):
		#self._logger.setVerbose(True)
		if len(lst) != 2:
			raise Exception('WRONG INPUT for _le: {}'.format(lst))
		#print('_le',lst,lst[0], lst[1])
		abstract = z3.simplify(lst[0] < lst[1])
		if z3.is_ge(abstract):
			return abstract
		else:
			abstract = lst[1] >= lst[0]
			abstract = self._abstraction(abstract)
			return z3.Not(abstract)

	def _leq(self,lst):
		if len(lst) != 2:
			raise Exception('WRONG INPUT for _le: {}'.format(lst))
		abstract = self._abstraction(lst[0] <= lst[1])
		return abstract

	def _ge(self,lst):
		if len(lst) != 2:
			raise Exception('WRONG INPUT for _le: {}'.format(lst))
		return self._abstraction(lst[0] >= lst[1])

	def _times(self,lst):
		if len(lst) != 2:
			raise Exception('WRONG INPUT for _times: {}'.format(lst))
		return lst[0] * lst[1]

	def _plus(self,lst):
		result = 0
		for i in lst:
			result += i
		return result

	def _minus(self,lst):
		result = 0
		for i in lst:
			result +- i
		return result

	def parseSmt1WeightFunction(self,functionAsString,tmpdir):
		self._weightFunction = Function(self._name,self._logger,functionAsString, tmpdir)
		return


	def parseSmt1String(self,string):
		
		self._kb = self._parseSmt1String(string)
		self._logger.writeToLog('ALL DONE PARSING with AbstractionManager: {}'.format(self))
		return

	def parseAndAppendSmt1String(self,query):
		
		tmpKb = self._parseSmt1String(query)
		self._kb = z3.And(self._kb,tmpKb)
		self._logger.writeToLog('ALL DONE PARSING with AbstractionManager: {}'.format(self))
		
		return

	def _parseSmt1String(self,string):
		#self._logger.setVerbose(True)
		stack = list()
		functionSymbols = '&|~<=*+-'
		try:
			string = string.replace('\n','').split('(')
			idx = 0
			for pos,elem in enumerate(string):
				self._logger.writeToLog('{} - reading :{}:'.format(pos,elem))
				if elem == '':
					continue

				elemL = elem.split()
				# ALL lines should start with '('
				if elemL[0] in functionSymbols:
					stack.append(elemL[0])
				elif elemL[0] == 'var':
					varName = elemL[2].replace(')','')
					if elemL[1] == 'bool':
						formula = z3.Bool(varName)
						stack.append(self._abstraction(formula))
					elif elemL[1] == 'real':
						formula = z3.Real(varName)
						stack.append(formula)
					elif elemL[1] == 'int':
						formula = z3.Int(varName)
						stack.append(formula)
					else:
						raise Exception('Unknown Variable format: {}'.format(elemL))
				elif elemL[0] == 'const':
					const = elemL[2].replace(')','')
					if elemL[1] == 'real':
						stack.append(z3.RealVal(const))
					elif elemL[1] == 'int':
						stack.append(z3.IntVal(const))
					else:
						raise Exception('Unknown Constant format: {}'.format(elemL))
				else:
					raise Exception('Unknown format : {}'.format(elemL))


				closedBrackets = elem.count(')') - 1
				self._logger.writeToLog("{} - new element in stack: {}\t,cB {}".format(pos ,stack[-1],closedBrackets))
				
				if closedBrackets < 1:
					continue

				while closedBrackets > 0:
					self._logger.writeToLog('{} - stack: {},{}'.format(pos,stack, closedBrackets))
					tmpPredi = []
					pred = None
					while True:
						pred = stack.pop()
						#if isinstance(pred,Predicate) or isinstance(pred,z3.BoolRef) or str(pred).replace('.','',1).isdigit():
						#if z3.is_rational_value(pred) or z3.is_int_value(pred) or z3.is_int(pred) or z3.is_real(pred) or z3.is_bool(pred):
						if isinstance(pred,float) or isinstance(pred,int) or z3.is_int(pred) or z3.is_real(pred) or z3.is_bool(pred):
							tmpPredi.append(pred)
						else:
							if len(tmpPredi) == 1:
								tmpPredi = tmpPredi[0]
							else:
								tmpPredi = tmpPredi[::-1]
							break
					self._logger.writeToLog('{} - {} is applied to {}'.format(pos, pred,tmpPredi))
					newElem = self._mapFunctionSymbol(pred)(tmpPredi)
					# newElemSimplified = z3.simplify(newElem)
					stack.append(newElem)
					self._logger.writeToLog("{} - new element in stack: {}\t,cB {}".format(pos ,stack[-1],closedBrackets))
					closedBrackets -= 1
				self._logger.writeToLog('{} - finished :{}:'.format(pos,stack))
		except Exception as e:
			self._logger.writeToLog("Some Error : {}\n\t Occured parsing formula: {}".format(e,string))
			raise e

		if len(stack) != 1:
			raise Exception("Parsing Error, stack != 1")
		return self._recusiveSimplification(stack[0])

	def _recusiveSimplification(self,formula):
		if formula.children() == 0:
			decl = formula.decl()
			children = []
			for child in formula.children():
				children.append(self._recusiveSimplification(z3.simplify(child)))
			if len(children) == 1:
				return decl([children[0]])
			else:
				return decl(children)
		else:
			return formula


	'''-----------------------------------------------------------------------------------------'''
	'''----------                            SMT 2.0 Methods                          ----------'''
	'''-----------------------------------------------------------------------------------------'''

	def parseSmt2String(self,smt2String,decl):

		formula = z3.parse_smt2_string(smt2String,decls=decl)
		self._smtInString = smt2String
		self._kb = z3.simplify(self._parseSmt2String(formula))

		for var,idx in self._groundVarRefernces.items():
			if len(idx) > 1:
				self._logger.writeToLog("Variable: {} is referenced by nodes: {}".format(var, [str(self._predicates[i]) for i in idx]))

	def _parseSmt2String(self,formula):
		try:
			if z3.is_or(formula):
				return z3.Or(self._parseSmt2String(formula.children()))
			elif z3.is_and(formula):
				return z3.And(self._parseSmt2String(formula.children()))
			elif isinstance(formula, list):# and len(formula) > 1:
				tmp = []
				for elem in formula:
					tmp.append(self._parseSmt2String(elem))
				return tmp
			elif z3.is_not(formula):
				return z3.Not(self._parseSmt2String(formula.children()[0]))
			else:
				return self._abstraction(formula)
		except:
			self._logger.writeToLog("Some Error Occured parsing formula: {}".format(formula))
			raise Exception

	'''-----------------------------------------------------------------------------------------'''
	'''----------                                 MI Methods                          ----------'''
	'''-----------------------------------------------------------------------------------------'''

	def vol_no_weight(self,model):
		vol = 1
		#self._logger.setVerbose(True)
		for groundVar in self._groundVarRefernces.keys():
			try:
				interval =  self._get_Interval(groundVar,model).asFloat()
				vol *= interval
			except Exception as e:
				self._logger.error('Coulnd not compute Interval for {}, model: {}, error: {}'.format(groundVar, model, e))
				raise Exception
		return vol

	# def vol_no_weight(self,model):
	# 	vol = 1
	# 	for subVar, refVars in self._groundVarRefernces.items():
	# 		trueRefVars = [item for item in refVars if model[item - 1] == 1]
	# 		interval =  self._getIntervalasFloat(subVar,trueRefVars)
	# 		vol *= interval
	# 		self._logger.setVerbose(True)
	# 		self._logger.writeToLog('Interval for model: ' + str(model) + \
	# 			',\tvar: {},\trefVars: {},\ttrueRefVars: {}'.format(subVar, refVars,trueRefVars) + \
	# 			',\interval: {},\tweight total: {}'.format(interval,vol))
	# 	return vol

	def _getIntervalasFloat(self,subVar,referencedVars):
		if not referencedVars:
			return 1
		interval = Interval()
		for varId in referencedVars:
			self._logger.writeToLog(self._predicates[varId])
			interval.combine(self._predicates[varId].interval)
		return interval.asFloat()


	'''-----------------------------------------------------------------------------------------'''
	'''----------                                 WMI Methods                         ----------'''
	'''-----------------------------------------------------------------------------------------'''

	def _get_Interval(self,groundVar,model):
		self._logger.writeToLog('Interval for model: ' + str(model) + ',\tvar: {}'.format(groundVar))
		if groundVar in self._groundVarRefernces.keys():
			refPropositionalVars = self._groundVarRefernces[groundVar]
			trueRefPredicates = [item for item in refPropositionalVars if model[item - 1] == 1]

			if not trueRefPredicates:
				return 1

			interval = Interval()
			for varId in trueRefPredicates:
				interval.combine(self._predicates[varId].interval)

			# self._logger.writeToLog('Interval for model: ' + str(model) + \
			# 	',\tvar: {},\trefVars: {},\ttrueRefVars: {}'.format(groundVar, refPropositionalVars,trueRefPredicates) + \
			# 	',\interval: {}'.format(interval))

		else:
			interval = Interval()

		return interval

	def _get_Bool_Interval(self,boolVar,model):
		if boolVar in self._predicateToIndx:
			truth = model[self._predicateToIndx[boolVar] -1] == 1
			interval = [truth]
		else:
			interval = [True, False]
		return interval

	def vol_single_weight(self,model, intError = None):
		vol = 1
		#self._logger.setVerbose(True)
		variableOrder = self._weightFunction.getVariableOrder()
		variableOrderBool = self._weightFunction.getVariableOrderBool()
		self._logger.writeToLog("Computing volume for model: {} ".format(model)+ \
			'with bound variables: {} '.format(self._groundVarRefernces) + \
			'and variabels declared in function: {}'.format(variableOrder))
		intervals = []
		for idx in range(len(variableOrder)):
			groundVar = variableOrder[idx]

			interval = self._get_Interval(groundVar,model).asList()
			intervals.append(interval)
			# if var in self._groundVarRefernces:
			# 	refVars = self._groundVarRefernces[var]
			# 	trueRefVars = [item for item in refVars if model[item - 1] == 1]
			# 	interval =  self._getIntervalasList(var,model)

				# self._logger.writeToLog('Interval for model: ' + str(model) + \
				# 	',\tvar: {},\tinterval: {}'.format(var,interval) + \
				# 	',\trefVars: {},\ttrueRefVars: {}'.format(refVars,trueRefVars))


		intervalsBool = []
		for idx in range(len(variableOrderBool)):
			var = variableOrder[idx]

			interval = self._get_Bool_Interval(var, model)
			intervalsBool.append(interval)
			# if var in self._predicateToIndx:
			# 	truth = model[self._predicateToIndx[var] -1] == 1
			# 	interval = [truth]

			# 	self._logger.writeToLog('Interval for model: ' + str(model) + \
			# 		',\tvar: {}'.format(var) + \
			# 		',\tinterval: {}, truth: {}, index: {}'.format(interval,truth, self._predicateToIndx[var]))
			# else:
			# 	interval = [True, False]

			# 	self._logger.writeToLog('Interval for model: ' + str(model) + \
			# 		',\tvar: {}'.format(var) + \
			# 		',\tinterval: {}'.format(interval))


		self._logger.writeToLog('The ordered      intervals are: {}'.format(intervals))
		self._logger.writeToLog('The ordered Bool intervals are: {}'.format(intervalsBool))
		#self._logger.writeToLog('with the weight function: {}'.format(self._weightFunction))

		(vol, error, integrationData) = self.combineIntervals(intervals, intervalsBool, intError)

		self._logger.writeToLog('The computed Model Integral for the model is: {}, {}'.format(vol, error))

		return (vol, error, integrationData)

	def combineIntervals(self,intervalsReal, intervalsBool, intError):
		#numIntervals = sum([len(x) for x in intervalsBool])
		totalVol = 0
		totalErr = 0
		fullTable = itertools.product([False, True], repeat=len(intervalsBool))
		actualBoolIntervlas = []
		for row in fullTable:
			skip = False
			for i,elem in enumerate(row):
				if not elem in intervalsBool[i]:
					skip = True
					break
			if skip == True:
				continue
			actualBoolIntervlas.append(tuple(row))
		start_time = time.time()
		tmpNb = len(self._computedIntervals)
		for intance in actualBoolIntervlas:
			(vol, error) = self.integrateOver(intervalsReal, args = intance, intError = intError)
			totalVol += vol
			totalErr += error
		end_time = time.time()
		return (totalVol, totalErr, ((end_time - start_time), len(self._computedIntervals) - tmpNb))


	def integrateOver(self, intervals, args, intError):
		intervalIdentifier = str(intervals) + "-" + str(args)
		if intervalIdentifier in self._computedIntervals.keys():
			(vol,error) = self._computedIntervals[intervalIdentifier]
		elif intError != None and intError != (0,0):
			(vol, error) = integrate.nquad(self._weightFunction.get(), intervals, args = args, opts = {'epsabs': intError[0], 'epsrel': intError[1]})
			self._computedIntervals[intervalIdentifier] = (vol,error)
		else: 
			(vol, error) = integrate.nquad(self._weightFunction.get(), intervals, args = args)
			self._computedIntervals[intervalIdentifier] = (vol,error)

		return (vol, error)

	def setComputedIntervals(self,computedIntervals):
		self._computedIntervals = computedIntervals

	def getComputedIntervals(self):
		return self._computedIntervals

	# def weight(self,model,varCount):
	# 	'''The Original wieght mehtod to return the weight of a model, as the producto of the '''
	# 	'''	weight function applied to each variable with instantiation''' 
	# 	product = 1
	# 	for i in range(varCount):
	# 		product *= self._w(i, model[i] == 1)
	# 	return product

	# def _w(self,VarId,truethAssignment):
	# 	'''this method represents the weight function of the current KB, so far it is initialized'''
	# 	'''	to return 1 for all variables true or fase'''
	# 	return 1

	'''-----------------------------------------------------------------------------------------'''
	'''----------                            I/O Methods                              ----------'''
	'''-----------------------------------------------------------------------------------------'''

	def saveToDemacs(self,file):
		#self._logger.test("SAVING KB TO DEMACS: {}".format(file))
		formula = self.toCnf()
		f = open('{}.cnf'.format(file),'w')
		f.write('c this the Abstacted SMT Formalu in CNF (DEMACS)\n')
		f.write('p cnf {} {}\n'.format(len(self._predicates), len(formula)))
		for disj in formula:
			for var in disj:
				if z3.is_not(var):
					f.write('-{} '.format(str(var.children()[0])))
				else:
					f.write('{} '.format(str(var)))
			f.write('0\n')
		f.close()





















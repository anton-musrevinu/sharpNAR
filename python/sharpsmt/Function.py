import types
import sys, imp,ast
import importlib.util
import z3

class Function:

	def __init__(self, name, logger, string, tmpDir):
		self._name = name
		self._variables = []
		self._foo = None
		self._asString = string
		self._logger = logger
		self._tmpFile = tmpDir + self._name + '_weightfunc.py'
		self._variableOrder = {}
		self._variableOrderBool = {}

		if string != None:
			self._parseWriteAndRead(string)

	def getVariableOrder(self):
		return self._variableOrder

	def getVariableOrderBool(self):
		return self._variableOrderBool

	def eval(self):
		return self._foo(variables)

	def get(self):
		return self._foo

	def _parseWriteAndRead(self,fucntionAsString):
		functionAsPythonString = self._parseStringToPythonCode(fucntionAsString)
		with open(self._tmpFile,'w') as f:
			for line in functionAsPythonString:
				f.write(line)

		spec = importlib.util.spec_from_file_location("weightFunction", self._tmpFile)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		self._foo = module.trueWeightFunc
		return

	def _parseStringToPythonCode(self, fucntionAsString):
		stack = list()
		functionSymbols = '&|*+-<=>=~^ite'
		stringVariables = []
		stringVariablesBool = []
		string = ""
		try:
			string = fucntionAsString.replace('\n','').split('(')
			idx = 0
			for pos,elem in enumerate(string):
				self._logger.writeToLog('{} - reading :{}:'.format(pos,elem))
				if elem == '':
					continue

				elemL = elem.split()
				# ALL lines should start with '('
				if elemL[0] in functionSymbols:
					#print('adding to stack : {}'.format(elemL[0]))
					stack.append(elemL[0])
				elif elemL[0] == 'var':
					varName = elemL[2].replace(')','')
					stack.append(varName)
					formula = None
					isBool = False
					if elemL[1] == 'bool':
						formula = z3.Bool(varName)
						isBool = True
					elif elemL[1] == 'real':
						formula = z3.Real(varName)
					elif elemL[1] == 'int':
						formula = z3.Int(varName)
					else:
						raise Exception('Unknown Variable format: {}'.format(elemL))

					if not varName in stringVariables and not isBool:
						self._variableOrder[len(self._variableOrder)] = formula					
						stringVariables.append(varName)
					if not varName in stringVariablesBool and isBool:
						self._variableOrderBool[len(self._variableOrderBool)] = formula
						stringVariablesBool.append(varName)

				elif elemL[0] == 'const':
					const = elemL[2].replace(')','')
					stack.append(const)
				else:
					self._logger.writeToLog("Unknown sequence : {}\n\t Occured parsing formula: {}".format(elemL[0],string))
					raise Exception


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
						if not pred in functionSymbols:
							tmpPredi.append(pred)
						else:
							tmpPredi = tmpPredi[::-1]
							break
					self._logger.writeToLog('{} - {} is applied to {}'.format(pos, pred,tmpPredi))

					stack.append(self._createFunctionForSymbol(pred,tmpPredi))

					self._logger.writeToLog("{} - new element in stack: {}\t,cB {}".format(pos ,stack[-1],closedBrackets))
					closedBrackets -= 1

				self._logger.writeToLog('{} - finished :{}:'.format(pos,stack))
		except Exception as e:
			self._logger.writeToLog("Some Error : {}\n\t Occured parsing formula: {}".format(e,string))
			raise Exception

		if len(stack) != 1:
			raise Exception("Parsing Error, stack != 1, stack: {}".format(stack))

		body = '\treturn {}\n'.format(stack[0])
		self._logger.writeToLog('Body of the Function: {}'.format(body))

		head = 'def trueWeightFunc({}'.format(stringVariables[0])
		for var in stringVariables[1::]:
			head += ',{}'.format(var)
		for var in stringVariablesBool:
			head += ',{}'.format(var)
		head += '):\n'
		self._logger.writeToLog('Init of the function: {}'.format(head))

		fullFuncAsString = head + body
		self._logger.writeToLog('Full Function: \n\n{}'.format(fullFuncAsString))
		self._logger.writeToLog('Full Var Order: {}'.format(self._variableOrder))
		return fullFuncAsString

	def _createFunctionForSymbol(self,funcSym,variables):
		arithmeticFucntions = "*+&|-<=>="
		singletonFunctions = '~'
		doubleFunctions = '^'
		ifelseStatement = 'ite'
		if funcSym in arithmeticFucntions:
			term = '( ' + variables[0] + ' '
			for var in variables[1::]:
				term += self._mapFunctionSymbol(funcSym) + ' ' + var + ' '
			term += ")"
		elif funcSym in singletonFunctions and len(variables) == 1:
			term = '{}({})'.format(self._mapFunctionSymbol(funcSym),variables[0])
		elif funcSym in doubleFunctions and len(variables) == 2:
			term = '({}{}{})'.format(variables[0],self._mapFunctionSymbol(funcSym),variables[1])
		elif funcSym in ifelseStatement and len(variables) == 3:
			term = '({} if {} else {})'.format(variables[1], variables[0],variables[2])
		else:
			raise Exception("WRONG SYMBOL FOUND : {}, len: {}, type: {}".format(funcSym,len(variables), type(variables)))
		return term

	def _mapFunctionSymbol(self,symbol):
		if symbol == '&':
			return 'and'
		elif symbol == '|':
			return 'or'
		elif symbol == '~':
			return 'not'
		elif symbol == '^':
			return '**'
		elif symbol in '- * + < <= > >=':
			return symbol
		else:
			raise Exception("WRONG SYMBOL FOUND : {}".format(symbol))

	def __str__(self):
		return self._asString
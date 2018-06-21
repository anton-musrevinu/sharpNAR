import z3
import math
from .Interval import Interval
from .myExceptions import AbstractionCondition

class Predicate(object):
	"""A frist version of the predicate class"""

	def __init__(self, idx, formula):
		self.id = idx
		self.subVars = []
		self.interval = None

		self.hasRefinement = self.checkFormat(formula)
		self.formula = formula

		if self.hasRefinement:
			self.initInterval()

	def checkFormat(self,formula):
		"""Check if the formula for a given predicate is of the supported format
			Supported formats include: 1. A Bool Ref such as A_x
									   2. An Arithmetic Ref such as a <= x or x <= a where a is number and x is Real/IntRef
									   3. An Arithmetic Ref such as a >= x or x >= a where a is number and x is Real/IntRef
		"""

		nbGroundAtoms = self.countGroundAtoms(formula)
		if not z3.is_bool(formula):
			raise Exception("Predicate formula is not Bool: {}".format(formula))

		#print("Bool formula: {},{},{}, nbGroundAtoms: {}".format(formula, type(formula), formula.children(),nbGroundAtoms))
		if len(formula.children()) == 0:
			#print("Boring old Variables such as A_x")
			return False
		if len(formula.children()) == 2:
			if nbGroundAtoms == 1:
				if z3.is_le(formula) or z3.is_ge(formula):
					#print("Two Children, and <= or => and nbGroundAtoms == 1")
					return True
				else:
					raise Exception("Not supported expression type f: {}, type: {}, nbGroundAtoms: {}".format(\
						formula,type(formula), nbGroundAtoms))
			else:
				raise AbstractionCondition("Not supported number of groundVariables: {}, nbGroundAtoms: {}".format(formula, nbGroundAtoms))
		else:
			raise Exception("Predicate formula has an unsupported number of children: {}, type: {}, nbChidren: {}".format(\
				formula,type(formula),formula.children()))

	def countGroundAtoms(self,refinement):
		#print(refinement,type(refinement))
		if z3.is_bool(refinement):
			count = 0
			for elem in refinement.children():
				#print(elem,type(elem))
				count += self.countGroundAtoms(elem)
		elif self._isNum(refinement):
			count = 0
		elif z3.is_arith(refinement) and len(refinement.children()) > 1:
			count = 0
			for elem in refinement.children():
				count += self.countGroundAtoms(elem)
			#print('is arith, r: {}, parms: {}, decl: {}, num_args: {}'.format(refinement, refinement.params(), refinement.decl(), refinement.num_args()))
		elif z3.is_arith(refinement) and len(refinement.children()) == 0:
			count = 1
			#print("heyo")
		else:
			raise AbstractionCondition("Unknown Expression: {}, {}".format(refinement,type(refinement)))

		#print('count: {}, = {}, {}'.format(refinement, count, type(refinement)))
		return count

	def initInterval(self):
		for i, elem in enumerate(self.formula.children()):
			if self._isVar(elem):
				self.subVars.append(elem)
			else:
				elem = str(elem).split('/')
				if z3.is_le(self.formula) and i == 0 or z3.is_ge(self.formula) and i == 1:
					if len(elem) > 1:
						minRange = float(elem[0]) / float(elem[1])  
					else: 
						minRange = float(elem[0])

					maxRange = math.inf
					self.interval = Interval(minRange, maxRange)
				elif z3.is_le(self.formula) and i == 1 or z3.is_ge(self.formula) and i == 0:
					minRange = -math.inf
					if len(elem) > 1:
						maxRange = float(elem[0]) / float(elem[1])  
					else: 
						maxRange = float(elem[0])
					self.interval = Interval(minRange,maxRange)
				else:
					raise AbstractionCondition("Unkonw Expression for refinement: {} and elem: {}, refType: {}".format(\
						self.formula, elem,type(self.formula)))

	def getBoolRef(self):
		return z3.Bool(str(self.id))

	def _isVar(self,elem):
		return not any([z3.is_int_value(z3.simplify(elem)),z3.is_rational_value(z3.simplify(elem)),z3.is_algebraic_value(z3.simplify(elem))])

	def _isNum(self,elem):
		return z3.is_rational_value(elem) or z3.is_int_value(elem)

	def __str__(self):
		return "({}, {}, {}, {})".format("ID:" + str(self.id),self.formula, self.subVars, self.interval)

	def getSubVars(self):
		return self.subVars

	def __eq__(self,other):
		if other == None:
			return False
		if self.hasRefinement != other.hasRefinement:
			print("pred: {} != {}, hasRefinement not equal: {} != {}".format(self,other,self.hasRefinement, other.hasRefinement))
		
		if not self.interval == other.interval:
			print("pred: {} != {}, Interval not equal: {} != {}".format(self,other,self.interval, other.interval))

		if not self.subVars == other.subVars:
			print("pred: {} != {}, subVars not equal: {} != {}".format(self,other,self.subVars, other.subVars))

		if self.id != other.id:
			print("pred: {} != {}, id not equal: {} != {}".format(self,other,self.id, other.id))

		return self.hasRefinement == other.hasRefinement \
			and self.subVars == other.subVars \
			and self.interval ==other.interval \
			and self.id == other.id
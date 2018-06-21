import z3
import time

class Z3Manager(object):

	INDICATOR_TIMEOUT = -2

	def __init__(self,cnfdir, name, logger):
		self._cnfFile = cnfdir + '/' + name + '.cnf'
		self._name = name
		self._logger = logger

	def enumerateModels(self,timeout):
		solver = z3.Solver()
		solver.set("complete",True)
		props = []
		with open(self._cnfFile, 'r') as f:
			for line in f:
				if line.startswith('c') or line.startswith('p'):
					continue
				letters = []
				for conj in line.split(' '):
					if conj == '0\n':
						break
					letters.append(z3.Bool(conj))
				props.extend(letters)
				solver.add(z3.Or(letters))
		models = []
		count = 0
		start_time = time.time()
		while True:
		#solver.check()
			tmp_time = time.time()
			if tmp_time - start_time > timeout:
				return Z3Manager.INDICATOR_TIMEOUT, tmp_time - start_time
			t = solver.check().r ==z3.Z3_L_TRUE
			#print(i,t,type(t), t.r == z3.Z3_L_TRUE)
			if not t:
				break
			model = solver.model()
			conj = []
			for p in props:
				if model[p]:
					conj.append(p)
				else:
					conj.append(z3.Not(p))
			solver.add(z3.Not(z3.And(conj)))
			count += 1
		#print("Model Count: {}".format(len(models)))

		end_time = time.time()
		compileTime = end_time - start_time
		return count,compileTime



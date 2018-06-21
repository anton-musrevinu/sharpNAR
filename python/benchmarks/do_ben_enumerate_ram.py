#Do enumeration benchmarks
from benchmarks.Benchmarks import Benchmark
from sharpsmt.Manager import Manager

if __name__=='__main__':
	pathE = './../mcbenchmarks/algorithms_specs/enumeration_input.csv' 
	pathC = './../mcbenchmarks/algorithms_specs/enumeration_input.csv' 

	benchmark = Benchmark(False,True)
	benchmark.benchmarkModelEnumeration(pathE,6 * 60 * 60,Manager.ALGORITHM_ME_RAM) 

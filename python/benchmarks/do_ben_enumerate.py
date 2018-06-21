#Do enumeration benchmarks
from benchmarks.Benchmarks import Benchmark
from sharpsmt.Manager import Manager

if __name__=='__main__':
	pathE = './../mcbenchmarks/algorithms_specs/enumeration_input.csv' 
	pathC = './../mcbenchmarks/algorithms_specs/enumeration_input.csv' 

	benchmark = Benchmark(False,False)
	benchmark.benchmarkModelEnumeration(pathE,6 * 60 * 60,Manager.ALGORITHM_ME_RAM)
	benchmark = Benchmark(False,False)
	benchmark.benchmarkModelEnumeration(pathE,10 * 60 * 60,Manager.ALGORITHM_ME_DISK)

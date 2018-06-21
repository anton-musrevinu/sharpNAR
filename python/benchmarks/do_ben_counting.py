#Do enumeration benchmarks
from benchmarks.Benchmarks import Benchmark
from sharpsmt.Manager import Manager

if __name__=='__main__':
	pathC = './../mcbenchmarks/algorithms_specs/enumeration_input.csv' 

	benchmark = Benchmark(False,True)
	benchmark.benchmarkModelCounting(pathC,3 * 60 * 60,1)

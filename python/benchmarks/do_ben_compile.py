#DO COMPILE BENCHMARK
from benchmarks.Benchmarks import Benchmark

if __name__=='__main__':
	path = './../mcbenchmarks/algorithms_specs/compile_input.csv' 

	benchmark = Benchmark(False,True)
	benchmark.benchmarkSddCompile(path,48 * 60 * 60)
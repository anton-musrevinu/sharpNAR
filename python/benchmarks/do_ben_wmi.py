#DO Model Integration BENCHMARK
from benchmarks.Benchmarks import Benchmark

if __name__=='__main__':

	benchmark = Benchmark(True,False)
	benchmark.doBenWMI()
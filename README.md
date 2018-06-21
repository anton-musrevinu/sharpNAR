The sharpNRA python library
======
This the is the project directory of the sharpNRA Python library for querying NAR formulas (MC/WMC/MI/WMI) by using SDD as the underlying querying language. The project was created as part of my (Anton Fuxjaeger) BSc Hons. Project at the University of Edinburgh. In addition to the code, this repository also holds the accompanying research report within the report directory.


Dependencies for using the python library sharpNAR:  
-------
	- Z3(python)		(https://github.com/Z3Prover/z3/wiki)  
	- Python >= 3.5  
	- Python BitVector 	(https://engineering.purdue.edu/kak/dist/BitVector-3.4.8.html)  
	- numpy 			(http://www.numpy.org/)  
	- scipy				(https://www.scipy.org/)  


The structure of the directory is as follows:
-------

**./c**					This is the directory holding the c files used fo the project, as well as the UCLA library files needed  
**./c/bin**			Here are the UCLA sdd compiler executables    
**./c/benchmarks** 		In this directory you will find my code to run the benchmarks on modelcounting using the SDD UCAL Library  

**./mcbenchmarks**		This directory holds the data used for model counting and model enumeration benchmarks as well as the input specifications to run the benchmarks  
**./smtbenchmarks**		Similar to mcbenchmarks, this directory hold the smt benchmarks files used weighted model integration  

**./python**			This is the main project directory  holding my code only  
**./python/benchmarks** This is the directory holding the .py files for running benchmark  experiments:  
					In order to run the experiments you have to change to the python directory and then run one of the following commands:  
						- "python -m benchmarks.do_ben_compile"			Compiling Benchmarks  
						- "python -m benchmarks.do_ben_counting"		Model Counting Benchmarks  
						- "python -m benchmarks.do_ben_enumerate_disk"	Model Enumeration Benchmarks using the DISK alg.  
						- "python -m benchmarks.do_ben_enumerate_ram"	Model Enumeration Benchmarks using the RAM alg.  
						- "python -m benchamrks.do_ben_mi"				Model Integration Benchmarks  
						- "python -m benchmarks.do_ben_wmi"				Weighted Model Integration Benchmarks  
**./python/benchmarks/out**	All results of running benchmarks will be written to files in this directory  

**./python/sharpsmt**	This is the Python Library developed as part of my project. Using this library one is able to parse SMT formulas, abstract them, compile them to sdds, and perform MC, ME, MI and WMI. As a starting point looking into the code I would suggest the QueryManager, being the top level class handling all Queries and probabilistic  inference. The Manager class on the other hand is responsible for propositional KBs and the corresponding SDDs.  
**./python/sharpsmt/sdd** 	Here the you will find the algorithms used for querying an SDD  

**./python/tests**		Here different test are stored, used throughout the project. They are run similar to the benchmarks with the -m flag  

**./clean.sh** 			This files is used to remove temporal files, and test results (clean the directory)  

**./README**			This file  

**./report**			This directory hold the report of the project as a pdf file  

This the is the project directory of my (Anton Fuxjaegers, s1455952) 4th year Hons Project.  
======

Dependencies for using the python library sharpSMT:  
-------
	- Z3(python)		(https://github.com/Z3Prover/z3/wiki)  
	- Python >= 3.5  
	- Python BitVector 	(https://engineering.purdue.edu/kak/dist/BitVector-3.4.8.html)  
	- numpy 			(http://www.numpy.org/)  
	- scipy				(https://www.scipy.org/)  


The structure of the directory is as follows:
-------

**./c**					This is the directory holding the c files used fo the project, as well as the UCLA library files needed  
**./c/bin**			Here are the UCLA sdd comiler executatbles  
**./c/benchmarks** 		In this directory you will find my code to run the benchmarks on thesting the modelcounting using the SDD UCAL Library  

**./mcbenchmarks**		This directory holds the data used for model counting and model enumeration benchmarks as well as the input specifications to run the benchmarks  
**./smtbenchmarks**		Similar to mcbenchmarks, this directory hold the smt benchmarks files used weighted model integration  

**./python**			This is the main project direcory holding my code only  
**./python/benchmarks** This is the directory holding the .py files for running bencharmk experiments:  
					In order to run the eperiments you have to change to the pytho directory and then run one of the following commands:  
						- "python -m benchmarks.do_ben_compile"			Compiling Benchmarks  
						- "python -m benchmarks.do_ben_counting"		Model Counting Benchmarks  
						- "python -m benchmarks.do_ben_enumerate_disk"	Model Enumeration Benchmarks using the DISK alg.  
						- "python -m benchmarks.do_ben_enumerate_ram"	Model Enumeration Benchmarks using the RAM alg.  
						- "python -m benchamrks.do_ben_mi"				Model Integration Benchmarks  
						- "python -m benchmarks.do_ben_wmi"				Weighted Model Interation Benchmarks  
**./python/benchmarks/out**	All results of running benchmarks will be written to files in this directory  

**./python/sharpsmt**	This is the Python Library Devoloped as part of my project. Using this library one is able to parse SMT fromulas, abstract them, compile them to sdds, and perfom MC, ME, MI and WMI. As a starting point looking into the code I would suggest the QueryManager, being the top level class handeling all Queries and Proabilitic inference. The Manager class on the other hand is responsible for propsitional KBs and the corresponding SDDs.  
**./python/sharpsmt/sdd** 	Here the you will find the algorithms used for querying an SDD  

**./python/tests**		Here different test are stored, used throughout the project. They are run similar to the benchmarks with the -m flag  

**./clean.sh** 			This files is used to remove temporal files, and test results (clean the directory)  

**./README**			This file  

**./report**			This direcotry hold the report of the poject as a pdf file  

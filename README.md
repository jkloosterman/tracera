# Tracera #
Tracera is a trace-based simulator for tightly-coupled GPU architectures. 

### Prerequisites ###
* [Pin 2.13 build 65163](https://software.intel.com/en-us/articles/pintool-downloads)
* [Pypy 2.3.1 or newer](http://pypy.org/download.html)

### Installation ###
* Modify the first line of simulator/simulator.py to point to where pypy is installed. Pypy makes the simulation over 10x faster than using cPython.
* Modify the PIN_ROOT variable in trace_generator/makefile to point to where Pin is installed.

### Usage ###
* Benchmarks need to be annotated before the trace generator is run on them. See [the wiki](https://bitbucket.org/jkloosterman/tracera/wiki/Annotating%20Benchmarks) for how to do so.
* `scripts/trace.sh` shows how to run the trace generator on the benchmark binary.
* The main simulator script is `simulator/simulator.py`. An example simulator configuration file is in `simulator/configs/tau_config.py`. 
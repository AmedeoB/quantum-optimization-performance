# Abstract
This folder contains the test code used to evaluate D-Wave Hybrid technologies and confronting them with IBM CPLEX solver. Complete study and results are published at [this link](https://arxiv.org/abs/2403.10455).


## Project Dependencies
This code make use of several libraries:
- [IBM DOcplex & CPLEX](https://ibmdecisionoptimization.github.io/docplex-doc/index.html);
- [D-Wave Ocean SDK](https://docs.ocean.dwavesys.com/en/stable/getting_started.html#gs-initial-setup);

The recommended Python version is 3.8, since it's the only one supporting both D-Wave and IBM libraries, later versions may work anyway. 

**IMPORTANT:** _D-Wave's SDK isn't required to run the IBM classic solver and viceversa_


## How to Use
After installing the required libraries, head to the main folder containing the .py files.

Here two `main_` files are visible, one for D-Wave Hybrid solver and one for the IBM Classic one. Open the `main_` you want to execute, at the top of the file, after the imports, you'll find the script constants, these manage the whole execution of the script, from tree's settings to time limit, solving iterations o save variables, depending on the file you choose.

Once setup your constants, simply run.

**IMPORTANT:** _Despite the cure we applied developing this test code, it is not primary meant for public use, changing constants values may cause malfunctions_



<!-- =========== NEW SECTION =========== -->
# Classical Solver
`_IBM.py` files handle the execution of the IBM CPLEX Classical solver.


## main_IBM.py
This script contains all the constant a user can change to obtain different execution cycles.

After tree's and constants initialization, it simply creates the various VM, PATH and FULL models using `_cplex_model()` functions and calls for resolution by calling `cplex_solver()`. 


## fun_lib_IBM.py
This script contains all the function useful to execute the resolution cycle of the classical solver.

Specifically, it contains these functions:
- `vm_cplex_model` fills the given CpoModel creating the VM Assignment problem;
- `path_cplex_model` fills the given CpoModel creating the Path Planning problem;
- `full_cplex_model` fills the given CpoModel creating the Full problem;
- `cplex_solver` takes the optimization problem, solves it by calling DOcplex APIs and manages the results;
- `to_dictionary` is a simple functions which transforms CpoSolveResult objects into dictionary for simpler management;



<!-- =========== NEW SECTION =========== -->
# Quantum-Hybrid Solver
`_DWAVE.py` files handle the execution of the DWAVE Quantum-Hybrid solver.


## main_DWAVE.py
This script contains all the constant a user can change to obtain different execution cycles.

After tree's, save manager and constants initialization, it simply creates the various VM, PATH and FULL models using `_model()` functions and calls for resolution by calling `cqm_solver()`. 


## fun_lib_DWAVE.py
This script contains all the function useful to execute the resolution cycle of the classical solver.

Specifically, it contains these functions:
- `vm_model()` fills the given ConstrainedQuadraticModel creating the VM Assignment problem;
- `path_model()` fills the given ConstrainedQuadraticModel creating the Path Planning problem;
- `full_model()` fills the given ConstrainedQuadraticModel creating the Full problem;
- `cqm_solver()` takes the optimization problem, solves it by calling D-Wave Leap's CQM solver and manages the results;
- `print_model_structure()` is a simple functions which prints model's infos (number of variables, constraints, list of both...);
- `print_cqm_extrainfo()` is a simple functions which prints solution's infos (variables ON and OFF) and extra infos;



<!-- =========== NEW SECTION =========== -->
# Structures and General Functions
`structures.py` contains all the common functions and classes, as well as some which are not shared but cause no dependency issue when executing one `main_` without installing the other's needed libraries.

Specifically it contains:
- `Proxytree` a class which creates the tree topology and manages all its settings
- `CQMmanager` a class to manage all the saving options of the Quantum-Hybrid Solver
- `get_nodes()` returns nodes ids given their link index and the link dictionary
- `print_section()` manages standard printing formatting on shell to separate sections
- `dict_filter()` filters an info dictionary (Quantum-Hybrid Solver only) extracting its run_time
- `info_writer()` writes a solution set on file

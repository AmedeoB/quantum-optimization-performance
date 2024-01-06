# ===========================================================================================================================
# This code was published under the MIT License, January 2024.
# GitHub repository: https://github.com/AmedeoB/quantum-optimization-performance

# This code was written as a test unit for the publication "Evaluation of Quantum and Hybrid Solvers for Combinatorial
# Optimization" (Bertuzzi et al.) and is not meant for public nor industrial purposes. Despite being developed with the
# possibility to change some parameters, it is not guaranteed that the code will run as it should if some are changed
# in an erroneous or unpredicted way. 
# Please refere to the README file, available at the upmentioned repository to read how it works.
# _______________________
# Author: AAA
# ____________________________________________________________________
# Collaborators: BBB, CCC, DDD
# ________________________________________________________________________________________________________
# Related Paper: Evaluation of Quantum and Hybrid Solvers for Combinatorial Optimization (AAA et al.)
# ===========================================================================================================================



#================================================================================================================================
# Imports 
#================================================================================================================================

# D_WAVE
import dimod

# CUSTOM
from structures import *
from fun_lib_DWAVE import *


#================================================================================================================================
# Constants & Managers 
#================================================================================================================================

proxytree = Proxytree(
                depth = 2, 
                server_c = 10, 
                link_c = 5, 
                idle_pc = 10, 
                dyn_pc = 2, 
                datar_avg = 4,
                # random_tree = True
            )

manager = CQMmanager(
                save_solution_vm = True, 
                save_info_vm = True, 
                # load_solution = True,     # Uncommet to load solution from saved files
                save_solution_path = True, 
                save_info_path = True,
                save_solution_full = True,
                save_info_full = True
            )

ITERATIONS = 5          # How much times the problem is solved from start to finish
VERBOSE = False          


if VERBOSE:   
    proxytree.print_tree()
    manager.print_manager()


#================================================================================================================================
# Splitted Model 
#================================================================================================================================

#==========
# VM Model |
#==========
# Create and fill
vm_cqm = dimod.ConstrainedQuadraticModel()
vm_model(proxytree, vm_cqm)

if VERBOSE: print_model_structure("vm model", vm_cqm)


for _ in range(ITERATIONS):
    
    # Solve
    print_section("VM Model")
    vm_cqm_solution, vm_cqm_info = cqm_solver(vm_cqm, "vm_model", 
                        proxytree.DEPTH, save_solution = manager.SAVE_VM_SOL,
                        save_info= manager.SAVE_VM_INFO)

    if VERBOSE:   print_cqm_extrainfo(vm_cqm_solution, vm_cqm_info)



    #============
    # Path Model |
    #============
    # Create and fill
    path_cqm = dimod.ConstrainedQuadraticModel()
    path_model(proxytree, path_cqm, vm_solution = vm_cqm_solution, 
            load = manager.LOAD_SOL)

    if VERBOSE: print_model_structure("path model", path_cqm)

    # Solve
    print_section("Path Model")
    path_cqm_solution, path_cqm_info = cqm_solver(path_cqm, "path_model", 
                    proxytree.DEPTH, save_solution = manager.SAVE_PATH_SOL,
                    save_info= manager.SAVE_PATH_INFO)

    if VERBOSE:   print_cqm_extrainfo(path_cqm_solution, path_cqm_info)



#================================================================================================================================
# Full Model
#================================================================================================================================
# Create and fill
full_cqm = dimod.ConstrainedQuadraticModel()
full_model(proxytree, full_cqm)

if VERBOSE: print_model_structure("path model", full_cqm)

for _ in range(ITERATIONS):
    
    # Solve
    print_section("Full Model")
    full_cqm_solution, full_cqm_info = cqm_solver(full_cqm, "full_model", 
                    proxytree.DEPTH, save_solution = manager.SAVE_FULL_SOL,
                    save_info= manager.SAVE_FULL_INFO)

if VERBOSE:   print_cqm_extrainfo(full_cqm_solution, full_cqm_info)

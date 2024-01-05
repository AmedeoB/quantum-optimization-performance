DEBUG = False

'''
TODO
    - run tests
'''


"""------------------- IMPORTS ---------------------"""
# D_WAVE
import dimod

# CUSTOM
from structures import *
from fun_lib_DWAVE import *
"""--------------------------------------------------"""

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
                # load_solution = True, 
                save_solution_path = True, 
                save_info_path = True,
                save_solution_full = True,
                save_info_full = True
            )

ITERATIONS = 5


if DEBUG:   
    proxytree.print_tree()
    manager.print_manager()


# ###################################################################
# |                       VM MODEL                                  |
# ###################################################################
print_section("VM Model")

# Create problem
vm_cqm = dimod.ConstrainedQuadraticModel()
# Variables & Constraints
vm_model(proxytree, vm_cqm)

if DEBUG: print_model_structure("vm model", vm_cqm)

# Solve
for _ in range(ITERATIONS):
    vm_cqm_solution, vm_cqm_info = detailed_cqm_solver(vm_cqm, "vm_model", 
                        proxytree.DEPTH, save_solution = manager.SAVE_VM_SOL,
                        save_info= manager.SAVE_VM_INFO)

    if DEBUG:   print_cqm_extrainfo(vm_cqm_solution, vm_cqm_info)



    # ###################################################################
    # |                       PATH MODEL                                |
    # ###################################################################
    print_section("Path Model")

    # Create problem
    path_cqm = dimod.ConstrainedQuadraticModel()
    # Variables & Constraints
    path_model(proxytree, path_cqm, vm_solution = vm_cqm_solution, 
            load = manager.LOAD_SOL)

    if DEBUG: print_model_structure("path model", path_cqm)

    # Solve
    path_cqm_solution, path_cqm_info = detailed_cqm_solver(path_cqm, "path_model", 
                    proxytree.DEPTH, save_solution = manager.SAVE_PATH_SOL,
                    save_info= manager.SAVE_PATH_INFO)

    if DEBUG:   print_cqm_extrainfo(path_cqm_solution, path_cqm_info)



# ###################################################################
# |                       FULL MODEL                                |
# ###################################################################
print_section("Full Model")

# Create problem
full_cqm = dimod.ConstrainedQuadraticModel()
# Variables & Constraints
full_model(proxytree, full_cqm)

if DEBUG: print_model_structure("path model", full_cqm)

# Solve
for _ in range(ITERATIONS):
    full_cqm_solution, full_cqm_info = detailed_cqm_solver(full_cqm, "full_model", 
                    proxytree.DEPTH, save_solution = manager.SAVE_FULL_SOL,
                    save_info= manager.SAVE_FULL_INFO)

if DEBUG:   print_cqm_extrainfo(full_cqm_solution, full_cqm_info)

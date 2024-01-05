'''
TODO
    
    - find way to set custom automatic stoppers
    - install python 3.10
'''
"""--------------------------------- IMPORTS ------------------------------------"""
# DOCPLEX
from docplex.cp.model import CpoModel, minimize

# CUSTOM
from structures import *
from fun_lib_IBM import *

"""------------------------------------------------------------------------------"""

proxytree = Proxytree(
                depth = 6, 
                server_c = 10, 
                link_c = 5, 
                idle_pc = 10, 
                dyn_pc = 2, 
                datar_avg = 4,
                # random_tree = True
            )
ITERATIONS = 1
VMTIME = 5
PATHTIME = 5
FULLTIME = 1500




############
# VM MODEL #
#####################################################################################################

# # Create
# vm_model = CpoModel()
# vm_cplex_model(vm_model, proxytree)        

# # Solve
# for _ in range(ITERATIONS): 
#     vm_solution = cplex_solver(vm_model, proxytree.DEPTH, "vm_model", VMTIME, save_solution=True)

#     #####################################################################################################


#     ##############
#     # PATH MODEL #
#     #####################################################################################################

#     # Create
#     path_model = CpoModel()
#     path_cplex_model(path_model, proxytree, vm_solution)        

#     # Solve
#     path_solution = cplex_solver(path_model, proxytree.DEPTH, "path_model", PATHTIME, save_solution=True)



##############
# FULL MODEL #
#####################################################################################################

# Create
full_model = CpoModel()
full_cplex_model(full_model, proxytree)        

# Solve
for _ in range(ITERATIONS): full_solution = cplex_solver(full_model, proxytree.DEPTH, "full_model", FULLTIME, save_solution=True)

#####################################################################################################

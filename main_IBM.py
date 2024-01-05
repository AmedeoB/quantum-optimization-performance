#================================================================================================================================
# Imports
#================================================================================================================================

# DOCPLEX
from docplex.cp.model import CpoModel

# CUSTOM
from structures import *
from fun_lib_IBM import *




#================================================================================================================================
# Constants & Managers
#================================================================================================================================

proxytree = Proxytree(
                depth = 6,
                server_c = 10, 
                link_c = 5, 
                idle_pc = 10, 
                dyn_pc = 2, 
                datar_avg = 4,
                # random_tree = True            # Uncomment to make the tree random
            )
ITERATIONS = 1          # How much times the problem is solved from start to finish
VMTIME = 5              # Maximum solving time for VM Model 
PATHTIME = 5            # Maximum solving time for Path Model
FULLTIME = 1500         # Maximum solving time for Full Model
WORKERS = 4             # Number of workers
FIRST_SOLUTION = True   # Execution mode. True -> First Solution Found (Still time restrained) | False -> only Time Restrained
SAVE = True             # Save results (overwrites old ones).




#================================================================================================================================
# Splitted Model 
#================================================================================================================================

#==========
# VM Model |
#==========
# Create
vm_model = CpoModel()
vm_cplex_model(vm_model, proxytree)        


for _ in range(ITERATIONS): 
    
    # Solve
    vm_solution = cplex_solver(
                        model= vm_model, 
                        depth= proxytree.DEPTH, 
                        problem_label= "vm_model", 
                        exec_time= VMTIME,
                        workers= WORKERS, 
                        save_solution= SAVE,
                        first_solution= FIRST_SOLUTION
                    ) 


    #============
    # Path Model |
    #============
    # Create
    path_model = CpoModel()
    path_cplex_model(path_model, proxytree, vm_solution)        

    # Solve
    path_solution = cplex_solver(
                        model= path_model, 
                        depth= proxytree.DEPTH, 
                        problem_label= "path_model", 
                        exec_time= PATHTIME,
                        workers= WORKERS, 
                        save_solution= SAVE,
                        first_solution= FIRST_SOLUTION
                    )



#================================================================================================================================
# Full Model
#================================================================================================================================

# Create
full_model = CpoModel()
full_cplex_model(full_model, proxytree)        

# Solve
for _ in range(ITERATIONS): 
        full_solution = cplex_solver(
                            model= full_model, 
                            depth= proxytree.DEPTH, 
                            problem_label= "full_model", 
                            exec_time= FULLTIME,
                            workers= WORKERS, 
                            save_solution= SAVE,
                            first_solution= FIRST_SOLUTION
                        )
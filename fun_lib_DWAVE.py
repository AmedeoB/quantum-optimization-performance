# ===========================================================================================================================
# This code was published under the MIT License, January 2024.
# GitHub repository: https://github.com/AmedeoB/quantum-optimization-performance

# This code was written as a test unit for the publication "Evaluation of Quantum and Hybrid Solvers for Combinatorial
# Optimization" (Bertuzzi et al.) and is not meant for public nor industrial purposes. Despite being developed with the
# possibility to change some parameters, it is not guaranteed that the code will run as it should if some are changed
# in an erroneous or unpredicted way. 
# Please refere to the README file, available at the upmentioned repository to read how it works.
# _______________________
# Author: Amedeo Bertuzzi
# ____________________________________________________________________
# Collaborators: Michele Amoretti, Davide Ferrari, University of Parma
# ________________________________________________________________________________________________________
# Related Paper: Evaluation of Quantum and Hybrid Solvers for Combinatorial Optimization (Bertuzzi et al.)
# ===========================================================================================================================



"""
 __________________________________ MODEL VARIABLES DICTIONARY ______________________________________________________________
|____________________________________________________________________________________________________________________________|
|Variable Name          |  Type       |  Model             |  Description                                                    |
|_______________________|_____________|____________________|_________________________________________________________________|
| ========================================================================================================================== |
| Binary Variables |                                                                                                         |
| =================                                                                                                          |
| flow_path               dict            p(f,(n1,n2))        part of flow f goes from node n1 to n2 -> 1 | otherwise -> 0   |
| on                      dict            on(n1, n2)          link between nodes n1 and n2 is ON                             |
| server_status           1D list         s_{i}               server i status, 1 ON, 0 OFF                                   |
| switch_status           1D list         sw_{k}              switch k status, 1 ON, 0 OFF                                   |
| vm_status               2D list         v_{ji}              VM j status on server i, 1 ON, 0 OFF                           |
| ========================================================================================================================== |
| Sets |                                                                                                                     |
| =====                                                                                                                      |
| FLOWS                   int             F                   number of flows (server-server paths, = M/2)                   |
| LINKS                   int             L                   number of links (graph links)                                  |
| NODES                   int             ---                 total number of nodes                                          |
| SERVERS                 int             M                   number of servers                                              |
| SWITCHES                int             K                   number of switches                                             |
| VMS                     int             N                   number of VM                                                   |
| ========================================================================================================================== |
| Other Variables |                                                                                                          |
| ================                                                                                                           |
| adjancy_list            2D list         ---                 node's adjancy list                                            |
| cpu_util                1D array        u(v_{ji})           CPU utilization of each VM                                     |
| data_rate               2D array        d_{f,l}             data rate of flow (f) on link (l)                              |
| dyn_powcons             1D list         P^{dyn}_{i}         maximum dynamic power of each node (i server, k switch)        |
| idle_powcons            1D list         P^{idle}_{i}        idle power consumption fo each node (i server, k switch)       |
| link_capacity           1D list         C_{l}               capacity of each link                                          |
| server_capacity         1D list         C_{s}               capacity of each server                                        |
| src_dst                 2D list         ---                 list of vms communicating through a path, identifies flows     |
|____________________________________________________________________________________________________________________________|
"""
#================================================================================================================================
# Imports 
#================================================================================================================================

# D_WAVE
import dimod
import dwave.system

# OTHERS
import json

# CUSTOM
from structures import *



#================================================================================================================================
# Functions 
#================================================================================================================================

def print_model_structure(name: str, model: dimod.ConstrainedQuadraticModel, 
        columns = 10):
    '''
    Simple function to print cqm model structure.

    Args:
        - name (str): name of the cqm model
        - model (ConstrainedQuadraticModel): CQM Model
        - columns (int, optional, default = 10): print columns
    '''

    print(
        f"\n# {name.upper()} STRUCTURE #"
        f"\nLinear Variables:       {model.num_variables()}"
        f"\nQuadratic Variables:    {model.num_quadratic_variables()}"
        f"\nBiases:                 {model.num_biases()}"
        f"\nConstraints:            {model.num_constraints()}"
        f"\nSoft Constraints:       {model.num_soft_constraints()}"
    )

    printer = "Variables Dictionary:\n"
    cols = 0
    for i in model.variables:
        printer += str(i)+"\t"
        cols += 1
        if cols == columns:
            printer += "\n"
            cols = 0
    print(printer)
    
    printer = "Constraints Dictionary:\n"
    cols = 0
    for i in model.constraints:
        printer += str(i)+"\t"
        cols += 1
        if cols == columns:
            printer += "\n"
            cols = 0
    print(printer)



def print_cqm_extrainfo(sample: set, infoset: set, columns = 10):
    '''
    Simple function to print cqm sample infos.

    Args:
        - sample (set): solution sampleset
        - infoset (set): extra info set
        - columns (int, optional, default = 10): print columns 
    '''

    zeroprinter = "\n# VARIABLES OFF #\n"
    activeprinter = "\n# VARIABLES ON #\n"
    zerocols, activecols = 0, 0
    for name, value in sample.items():
        if value == 0.0:
            zeroprinter += f"{name}\t"
            zerocols += 1
        elif value == 1.0:
            activeprinter += f"{name}\t"
            activecols += 1
        else:
            activeprinter += f"{name}: {value}\t"
            activecols += 1
        if zerocols == columns:
            zeroprinter += "\n"
            zerocols = 0
        if activecols == columns:
            activeprinter += "\n"
            activecols = 0
    zeroprinter+="\n"
    activeprinter+="\n"
    print(zeroprinter + activeprinter)

    infoprinter = "\n# EXTRA INFO #\n"
    for name, value in infoset.items():
        infoprinter += f"{name}: {value}\n"
    print(infoprinter+"\n")



def cqm_solver(cqm_problem: dimod.ConstrainedQuadraticModel, problem_label: str, 
            depth: int, save_solution = False, save_info = False):
    '''
    Solves the CQM problem using a CQM Hybrid Solver and returns
    the results.

    Args:
        - cqm_problem (ConstrainedQuadraticModel): BQM to solve
        - problem_label (str): problem label
        - depth (int): tree depth, for saving purposes
        - save_solution (bool, optional, default=False): save option
            for the solution dictionary
        - save_info (bool, optional, default=False): save option
            for the info dictionary

    Returns:
        - Tuple: containing the solution sample and execution info
    '''

    # Sampler
    sampler = dwave.system.LeapHybridCQMSampler()

    # Results
    sampleset = sampler.sample_cqm(cqm_problem, label = problem_label)

    # Exec time & Info
    problem_info = sampleset.info
    exec_time = problem_info.get('run_time')

    # Extract feasible solution
    feasible_sampleset = sampleset.filter(lambda sample: sample.is_feasible)

    if len(feasible_sampleset) != 0:
        # Extract best solution and energy
        best_solution = feasible_sampleset.first[0]
        energy = feasible_sampleset.first[1]

        # Save best solution & info
        if save_solution:
            with open((f"DWAVE LOGS/depth_{depth}/{problem_label}_solution.txt"), "w") as fp:
                json.dump(best_solution, fp)
                print(f"{problem_label} solution updated!")
    else:
        # No solution found, give sample values
        best_solution = {}
        energy = 0.0

    # Save solution info (energy & times)    
    if save_info:
        new_dict = dict(filter(dict_filter, problem_info.items()))
        for k,v in new_dict.items():
            new_dict[k] = v / 10**6     # Convert timers to seconds for better readability
        new_dict["energy"] = energy
        path = f"DWAVE LOGS/depth_{depth}/{problem_label}_info.txt"
        info_writer(new_dict, path)

    # Print solution infos
    print(
        f"\n# CQM SOLUTION #"
        f"\nCQM EXEC TIME:  {exec_time} micros"
        f"\nCQM ENERGY:     {energy}"
    )

    return (best_solution, problem_info)



def vm_model(tree: Proxytree, cqm: dimod.ConstrainedQuadraticModel):
    '''
    Creates the vm assignment model as a Constrained Quadratic Model

    Args:
        - tree (Proxytree): the tree structure to generate the model
        - cqm (ConstrainedQuadraticModel): the CQM to create
    '''

    #______________________________________________________________________________________
    # Variables
    server_status = [
        dimod.Binary("s{}".format(s)) 
        for s in range(tree.SERVERS)
    ]
    vm_status = [
        [
            dimod.Binary("vm{}-s{}".format(vm,s)) 
            for vm in range(tree.VMS)
        ] for s in range(tree.SERVERS)
    ] 


    #______________________________________________________________________________________
    # Objective
    obj1 = dimod.quicksum(
        server_status[s] 
        * tree.idle_powcons[s+tree.SWITCHES] 
        for s in range(tree.SERVERS)
    )
    obj2 = dimod.quicksum(
        tree.dyn_powcons[s+tree.SWITCHES] 
        * dimod.quicksum(
            tree.cpu_util[vm] 
            * vm_status[s][vm] 
            for vm in range(tree.VMS)
        ) for s in range(tree.SERVERS)
    )

    cqm.set_objective(obj1 + obj2)


    #______________________________________________________________________________________
    # Constraints [Numbers refer to mathematical model formulas numbers on the paper]
    # (3) For each server, the CPU utilization of each VM on that server must be less or equal than server's capacity            
    for s in range(tree.SERVERS):
        cqm.add_constraint(
            dimod.quicksum(
                tree.cpu_util[vm] 
                * vm_status[s][vm] 
                for vm in range(tree.VMS)
            ) 
            - tree.server_capacity[s]
            * server_status[s] 
            <= 0, 
            label="C11-N{}".format(s)
        )

    # (4) For each VM, it must be active on one and only one server
    for vm in range(tree.VMS):
        cqm.add_constraint(
            dimod.quicksum(
                vm_status[s][vm] 
                for s in range(tree.SERVERS)
            ) 
            == 1, 
            label="C12-N{}".format(vm)
        )
    


def path_model(tree: Proxytree, cqm: dimod.ConstrainedQuadraticModel, 
            vm_solution: set, load = False):
    '''
    Creates the path planning model as a Constrained Quadratic Model
    
    Args:
        - tree (Proxytree): the tree structure to generate the model
        - cqm (ConstrainedQuadraticModel): the CQM to create
        - vm_solution (tuple(dict, int)): the previous VM assignment solution
        - load (bool, optional, default= False): boolean var for loading saved results
    '''
    
    #______________________________________________________________________________________
    # Variables
    switch_status = [
        dimod.Binary("sw{}".format(sw)) 
        for sw in range(tree.SWITCHES)
    ]

    flow_path = {}
    for f in range(tree.FLOWS):
        for n1 in range(tree.NODES):
            for n2 in range(tree.NODES):
                if tree.adjancy_list[n1][n2]:     # Adjancy Condition (lowers variable number)
                    flow_path["f{}-n{}-n{}".format(f, n1, n2)] = dimod.Binary("f{}-n{}-n{}".format(f, n1, n2))

    on = {}
    for n1 in range(tree.NODES):
        for n2 in range(n1, tree.NODES):
            if tree.adjancy_list[n1][n2]:         # Adjancy Condition (lowers variable number)
                on["on{}-{}".format(n1, n2)] = dimod.Binary("on{}-{}".format(n1, n2))


    # Load VM solution from file
    if load:
        with open(f"DWAVE LOGS/depth_{tree.DEPTH}/vm_model_solution.txt") as fp:
            vm_solution = json.loads(fp.read())
            print("VM Solution Dictionary loaded!")
            print(vm_solution)
            print("\n\n")

    #______________________________________________________________________________________
    # Objective
    obj3 = dimod.quicksum(
        switch_status[sw] 
        * tree.idle_powcons[sw] 
        for sw in range(tree.SWITCHES)
    )
    obj4 = dimod.quicksum(
        tree.dyn_powcons[sw] 
        * (
            flow_path["f{}-n{}-n{}".format(f, n, sw)] 
            + flow_path["f{}-n{}-n{}".format(f, sw, n)]
        )
        for n in range(tree.NODES) 
        for f in range(tree.FLOWS) 
        for sw in range(tree.SWITCHES) 
        if tree.adjancy_list[n][sw] == 1
    )

    cqm.set_objective(obj3 + obj4)


    #______________________________________________________________________________________
    # Constraints [Numbers refer to mathematical model formulas numbers on the paper]    
    # (5) For each flow and server, the sum of exiting flow from the server to all adj switch is = than vms part of that flow
    for f in range(tree.FLOWS):
        for s in range(tree.SWITCHES, tree.SWITCHES + tree.SERVERS):           # Start from switches cause nodes are numerated in order -> all switches -> all servers
            if vm_solution.get("vm{}-s{}".format(tree.src_dst[f][0], s-tree.SWITCHES)) == 0:
                cqm.add_constraint( 
                    dimod.quicksum( 
                        flow_path["f{}-n{}-n{}".format(f, s, sw)] 
                        for sw in range(tree.SWITCHES) 
                        if tree.adjancy_list[s][sw] == 1
                    )
                    == 0, 
                    label="C13-N{}".format(f*tree.SERVERS+s)
                )

    # (6) For each flow and server, the sum of entering flow from the server to all adj switch is = than vms part of that flow
    for f in range(tree.FLOWS):
        for s in range(tree.SWITCHES, tree.SWITCHES + tree.SERVERS):
            if vm_solution.get("vm{}-s{}".format(tree.src_dst[f][1], s-tree.SWITCHES)) == 0:    
                cqm.add_constraint( 
                    dimod.quicksum( 
                        flow_path["f{}-n{}-n{}".format(f, sw, s)] 
                        for sw in range(tree.SWITCHES) 
                        if tree.adjancy_list[sw][s] == 1
                    ) 
                    == 0, 
                    label="C14-N{}".format(f*tree.SERVERS+s)
                ) 

    # (7) For each flow and server, force allocation of all flows     
    for f in range(tree.FLOWS):
        for s in range(tree.SWITCHES, tree.SWITCHES + tree.SERVERS):
            cqm.add_constraint( 
                vm_solution.get("vm{}-s{}".format(tree.src_dst[f][0], s-tree.SWITCHES)) 
                - vm_solution.get("vm{}-s{}".format(tree.src_dst[f][1], s-tree.SWITCHES))
                - ( 
                    dimod.quicksum( 
                        flow_path["f{}-n{}-n{}".format(f, s, sw)] 
                        for sw in range(tree.SWITCHES) 
                        if tree.adjancy_list[s][sw] == 1
                    ) 
                    - dimod.quicksum( 
                        flow_path["f{}-n{}-n{}".format(f, sw, s)] 
                        for sw in range(tree.SWITCHES) 
                        if tree.adjancy_list[sw][s] == 1
                    )
                ) 
                == 0, 
                label="C15-N{}".format(f*tree.SERVERS+s)
            )

    # (8) For each switch and flow, entering and exiting flow from the switch are equal
    for sw in range(tree.SWITCHES):
        for f in range(tree.FLOWS):
            cqm.add_constraint( 
                dimod.quicksum( 
                    flow_path["f{}-n{}-n{}".format(f, n, sw)]  
                    for n in range(tree.NODES) 
                    if tree.adjancy_list[n][sw] == 1
                ) 
                - dimod.quicksum( 
                    flow_path["f{}-n{}-n{}".format(f, sw, n)] 
                    for n in range(tree.NODES) 
                    if tree.adjancy_list[sw][n] == 1
                ) 
                == 0, 
                label="C16-N{}".format(sw*tree.FLOWS+f)
            )

    # (9) For each link, the data rate on it is less or equal than its capacity      
    for l in range(tree.LINKS):
        n1,n2 = get_nodes(l, tree.link_dict)
        cqm.add_constraint( 
            dimod.quicksum( 
                tree.data_rate[f] 
                * (
                    flow_path["f{}-n{}-n{}".format(f, n1, n2)] 
                    + flow_path["f{}-n{}-n{}".format(f, n2, n1)]
                ) for f in range(tree.FLOWS)
            ) 
            - tree.link_capacity[l] 
            * on["on{}-{}".format(n1, n2)] 
            <= 0, 
            label="C17-N{}".format(l)
        )

    # (10)(11) For each link, the link is ON only if both nodes are ON       
    for l in range(tree.LINKS):
        n1,n2 = get_nodes(l, tree.link_dict)

        cqm.add_constraint(
            on["on{}-{}".format(n1, n2)] 
            - switch_status[n1] 
            <= 0, 
            label="C18-N{}".format(l)
        )

        if n2 < tree.SWITCHES:     # If the second node is a switch
            cqm.add_constraint(
                on["on{}-{}".format(n1, n2)] 
                - switch_status[n2] 
                <= 0,
                label="C19-N{}".format(l)
            )
        else:                           # If it's a server
            cqm.add_constraint(
                on["on{}-{}".format(n1, n2)] 
                - vm_solution.get("s{}".format(n2-tree.SWITCHES))
                == 0,
                label="C19-N{}".format(l)
            )



def full_model(tree: Proxytree, cqm: dimod.ConstrainedQuadraticModel):
    '''
    Creates the full optimization model as a Constrained Quadratic Model

    Args:
        - tree (Proxytree): the tree structure to generate the model
            type: Proxytree
        - cqm (ConstrainedQuadraticModel): the CQM to create
    '''
    

    #______________________________________________________________________________________
    # Variables
    server_status = [
        dimod.Binary("s{}".format(s)) 
        for s in range(tree.SERVERS)
    ]
    vm_status = [
        [
            dimod.Binary("vm{}-s{}".format(vm,s)) 
            for vm in range(tree.VMS)
        ] for s in range(tree.SERVERS)
    ] 
    switch_status = [
        dimod.Binary("sw{}".format(sw)) 
        for sw in range(tree.SWITCHES)
    ]

    flow_path = {}
    for f in range(tree.FLOWS):
        for n1 in range(tree.NODES):
            for n2 in range(tree.NODES):
                if tree.adjancy_list[n1][n2]:     # Adjancy Condition (lowers variable number)
                    flow_path["f{}-n{}-n{}".format(f, n1, n2)] = dimod.Binary("f{}-n{}-n{}".format(f, n1, n2))

    on = {}
    for n1 in range(tree.NODES):
        for n2 in range(n1, tree.NODES):
            if tree.adjancy_list[n1][n2]:         # Adjancy Condition (lowers variable number)
                on["on{}-{}".format(n1, n2)] = dimod.Binary("on{}-{}".format(n1, n2))


    #______________________________________________________________________________________
    # Objective
    obj1 = dimod.quicksum(
        server_status[s] 
        * tree.idle_powcons[s+tree.SWITCHES] 
        for s in range(tree.SERVERS)
    )
    obj2 = dimod.quicksum(
        tree.dyn_powcons[s+tree.SWITCHES] 
        * dimod.quicksum(
            tree.cpu_util[vm] 
            * vm_status[s][vm] 
            for vm in range(tree.VMS)
        ) for s in range(tree.SERVERS)
    )
    obj3 = dimod.quicksum(
        switch_status[sw] 
        * tree.idle_powcons[sw] 
        for sw in range(tree.SWITCHES)
    )
    obj4 = dimod.quicksum(
        tree.dyn_powcons[sw] 
        * (
            flow_path["f{}-n{}-n{}".format(f, n, sw)] 
            + flow_path["f{}-n{}-n{}".format(f, sw, n)]
        )
        for n in range(tree.NODES) 
        for f in range(tree.FLOWS) 
        for sw in range(tree.SWITCHES) 
        if tree.adjancy_list[n][sw] == 1
    )

    cqm.set_objective(obj1 + obj2 + obj3 + obj4)


    #______________________________________________________________________________________
    # Constraints [Numbers refer to mathematical model formulas numbers on the paper]
    # (3) For each server, the CPU utilization of each VM on that server must be less or equal than server's capacity            
    for s in range(tree.SERVERS):
        cqm.add_constraint(
            dimod.quicksum(
                tree.cpu_util[vm] 
                * vm_status[s][vm] 
                for vm in range(tree.VMS)
            ) 
            - tree.server_capacity[s]
            * server_status[s] 
            <= 0, 
            label="C11-N{}".format(s)
        )

    # (4) For each VM, it must be active on one and only one server
    for vm in range(tree.VMS):
        cqm.add_constraint(
            dimod.quicksum(
                vm_status[s][vm] 
                for s in range(tree.SERVERS)
            ) 
            == 1, 
            label="C12-N{}".format(vm)
        )
        
    # (5) For each flow and server, the sum of exiting flow from the server to all adj switch is <= than vms part of that flow
    for f in range(tree.FLOWS):
        for s in range(tree.SWITCHES, tree.SWITCHES + tree.SERVERS):           # Start from switches cause nodes are numerated in order -> all switches -> all servers
            cqm.add_constraint( 
                dimod.quicksum( 
                    flow_path["f{}-n{}-n{}".format(f, s, sw)] 
                    for sw in range(tree.SWITCHES) 
                    if tree.adjancy_list[s][sw] == 1
                )
                - vm_status[tree.src_dst[f][0]][s-tree.SWITCHES]
                <= 0, 
                label="C13-N{}".format(f*tree.SERVERS+s)
            )

    # (6) For each flow and server, the sum of entering flow from the server to all adj switch is <= than vms part of that flow
    for f in range(tree.FLOWS):
        for s in range(tree.SWITCHES, tree.SWITCHES + tree.SERVERS):
            cqm.add_constraint( 
                dimod.quicksum( 
                    flow_path["f{}-n{}-n{}".format(f, sw, s)] 
                    for sw in range(tree.SWITCHES) 
                    if tree.adjancy_list[sw][s] == 1
                ) 
                - vm_status[tree.src_dst[f][1]][s-tree.SWITCHES]
                <= 0, 
                label="C14-N{}".format(f*tree.SERVERS+s)
            ) 

    # (7) For each flow and server, force allocation of all flows     
    for f in range(tree.FLOWS):
        for s in range(tree.SWITCHES, tree.SWITCHES + tree.SERVERS):
            cqm.add_constraint( 
                vm_status[tree.src_dst[f][0]][s-tree.SWITCHES]
                - vm_status[tree.src_dst[f][1]][s-tree.SWITCHES]
                - ( 
                    dimod.quicksum( 
                        flow_path["f{}-n{}-n{}".format(f, s, sw)] 
                        for sw in range(tree.SWITCHES) 
                        if tree.adjancy_list[s][sw] == 1
                    ) 
                    - dimod.quicksum( 
                        flow_path["f{}-n{}-n{}".format(f, sw, s)] 
                        for sw in range(tree.SWITCHES) 
                        if tree.adjancy_list[sw][s] == 1
                    )
                ) 
                == 0, 
                label="C15-N{}".format(f*tree.SERVERS+s)
            )

    # (8) For each switch and flow, entering and exiting flow from the switch are equal
    for sw in range(tree.SWITCHES):
        for f in range(tree.FLOWS):
            cqm.add_constraint( 
                dimod.quicksum( 
                    flow_path["f{}-n{}-n{}".format(f, n, sw)]  
                    for n in range(tree.NODES) 
                    if tree.adjancy_list[n][sw] == 1
                ) 
                - dimod.quicksum( 
                    flow_path["f{}-n{}-n{}".format(f, sw, n)] 
                    for n in range(tree.NODES) 
                    if tree.adjancy_list[sw][n] == 1
                ) 
                == 0, 
                label="C16-N{}".format(sw*tree.FLOWS+f)
            )

    # (9) For each link, the data rate on it is less or equal than its capacity      
    for l in range(tree.LINKS):
        n1,n2 = get_nodes(l, tree.link_dict)
        cqm.add_constraint( 
            dimod.quicksum( 
                tree.data_rate[f] 
                * (
                    flow_path["f{}-n{}-n{}".format(f, n1, n2)] 
                    + flow_path["f{}-n{}-n{}".format(f, n2, n1)]
                ) for f in range(tree.FLOWS)
            ) 
            - tree.link_capacity[l] 
            * on["on{}-{}".format(n1, n2)] 
            <= 0, 
            label="C17-N{}".format(l)
        )

    # (10)(11) For each link, the link is ON only if both nodes are ON       
    for l in range(tree.LINKS):
        n1,n2 = get_nodes(l, tree.link_dict)

        cqm.add_constraint(
            on["on{}-{}".format(n1, n2)] 
            - switch_status[n1] 
            <= 0, 
            label="C18-N{}".format(l)
        )

        if n2 < tree.SWITCHES:     # If the second node is a switch
            cqm.add_constraint(
                on["on{}-{}".format(n1, n2)] 
                - switch_status[n2] 
                <= 0,
                label="C19-N{}".format(l)
            )
        else:                           # If it's a server
            cqm.add_constraint(
                on["on{}-{}".format(n1, n2)] 
                - server_status[n2-tree.SWITCHES] 
                <= 0,
                label="C19-N{}".format(l)
            )
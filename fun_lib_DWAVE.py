DEBUG = False

"""
################################### MODEL VARIABLES DICTIONARY ######################################################
_____________________________________________________________________________________________________________________
Variable         |  Type         |  Model        |  Description
_________________|_______________|_______________|___________________________________________________________________
SERVERS             int             M               number of servers
VMS                 int             N               number of VM
SWITCHES            int             K               number of switches
FLOWS               int             F               number of flows (server-server paths, = M/2)
LINKS               int             L               number of links (graph links)
idle_powcons        1D list         p(idle_i/k)     idle power consumption fo each node (i server, k switch)
dyn_powcons         1D list         p(dyn_i/k)      maximum dynamic power of each node (i server, k switch) 
adjancy_list        2D list         ---             node's adjancy list
link_capacity       1D list         C(l)            capacity of each link
server_capacity     1D list         C(s)            capacity of each server
src_dst             2D list         ---             list of vms communicating through a path, identifies flows
server_status       1D list         s(i)            server (i) status, 1 on, 0 off
switch_status       1D list         sw(k)           switch (k) status, 1 on, 0 off
vm_status           2D list         v(ji)           VM (j) status per server (i), 1 on, 0 off
cpu_util            1D array        u(v(ji))        CPU utilization of each VM 
data_rate           2D array        d(fl)           data rate of flow (f) on link (l)
flow_path           bin dictionary  ρ(f,(k,i))      se parte del flow (f) va da k a i (nodi), allora 1, 0 altrimenti
on                  bin dictionary  on(n1, n2)      link between node n1 and n2 is ON                
_____________________________________________________________________________________________________________________
#####################################################################################################################
"""
# D_WAVE
import dimod
import dwave.system

# OTHERS
import json

# CUSTOM
from structures import *



def print_model_structure(name: str, model: dimod.ConstrainedQuadraticModel, 
        columns = 10):
    '''
    Simple function to print cqm model structure.

    Args:
        name (str): name of the cqm model
        model (ConstrainedQuadraticModel): CQM
        columns (int, optional, default = 10): print columns for 
        dictionary
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
        sample (set): solution sample
        infoset (set): extra info set
        columns (int, optional, default = 10): print columns 
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



def detailed_cqm_solver(cqm_problem: dimod.ConstrainedQuadraticModel, problem_label: str, 
            depth: int, save_solution = False, save_info = False):
    '''
    Solves the CQM problem using a CQM Hybrid Solver and returns
    the results.

    Args:
        - cqm_problem (ConstrainedQuadraticModel): the BQM to 
        solve
        - problem_label (str): the problem label
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
        best_solution = {}
        energy = 0.0
        
    if save_info:
        new_dict = dict(filter(dict_filter, problem_info.items()))
        for k,v in new_dict.items():
            new_dict[k] = v / 10**6     # Convert timers to seconds for better readability
        new_dict["energy"] = energy
        path = f"DWAVE LOGS/depth_{depth}/{problem_label}_info.txt"
        info_writer(new_dict, path)

    # Print
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
    
    Returns:
        - null
    '''

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

    # Objective
    # 1 - SUM of server pow cons
    obj1 = dimod.quicksum(
        server_status[s] 
        * tree.idle_powcons[s+tree.SWITCHES] 
        for s in range(tree.SERVERS)
    )
    # 2 - SUM of vm dyn pow cons
    obj2 = dimod.quicksum(
        tree.dyn_powcons[s+tree.SWITCHES] 
        * dimod.quicksum(
            tree.cpu_util[vm] 
            * vm_status[s][vm] 
            for vm in range(tree.VMS)
        ) for s in range(tree.SERVERS)
    )
    # Total
    cqm.set_objective(obj1 + obj2)

    # Constraints
    # (11) For each server, the CPU utilization of each VM on that server must be less or equal than server's capacity            
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

    # (12) For each VM, it must be active on one and only one server
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
        - load (bool): boolean var for loading saved results
    
    Returns:
        - null
    '''
    
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


    # Load best solution from file
    if load:
        with open(f"DWAVE LOGS/depth_{tree.DEPTH}/vm_model_solution.txt") as fp:
            vm_solution = json.loads(fp.read())
            print("VM Solution Dictionary loaded!")
            print(vm_solution)
            print("\n\n")


    # Objective
    # 3 - SUM of switch idle pow cons
    obj3 = dimod.quicksum(
        switch_status[sw] 
        * tree.idle_powcons[sw] 
        for sw in range(tree.SWITCHES)
    )
    # 4 - SUM of flow path
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
    # Total
    cqm.set_objective(obj3 + obj4)


    # Constraints
    # (13) For each flow and server, the sum of exiting flow from the server to all adj switch is = than vms part of that flow
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

    # (14) For each flow and server, the sum of entering flow from the server to all adj switch is = than vms part of that flow
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

    # (15) For each flow and server, force allocation of all flows     
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

    # (16) For each switch and flow, entering and exiting flow from the switch are equal
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

    # (17) For each link, the data rate on it is less or equal than its capacity      
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

    # (18)(19) For each link, the link is ON only if both nodes are ON       
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


        # -------------------------------------------------
        # Based on structure formation, n1 will always be a switch
        # if structure changes, this will be the new conditions
        # structure.
        # -------------------------------------------------
        # if n1 < proxytree.SWITCHES:
        #     path_cqm.add_constraint(
        #         on["on" + str(n1) + "-" + str(n2)] 
        #         - switch_status[n1] 
        #         <= 0, label="C18-N"+str(l))
        # else:
        #     path_cqm.add_constraint(
        #         on["on" + str(n1) + "-" + str(n2)] 
        #         - cqm_best[0].get("s"+str(n1-SWITCHES)) 
        #         <= 0, label="C18-N"+str(l))
        # if n2 < proxytree.SWITCHES:
        #     path_cqm.add_constraint(
        #         on["on" + str(n1) + "-" + str(n2)] 
        #         - switch_status[n2] 
        #         <= 0, label="C19-N"+str(l))
        # else:
        #     path_cqm.add_constraint(
        #         on["on" + str(n1) + "-" + str(n2)] 
        #         - cqm_best[0].get("s"+str(n2-SWITCHES)) 
        #         == 0, label="C19-N"+str(l))



def full_model(tree: Proxytree, cqm: dimod.ConstrainedQuadraticModel):
    '''
    Creates the full optimization model as a Constrained Quadratic Model

    Args:
        - tree (Proxytree): the tree structure to generate the model
            type: Proxytree
        - cqm (ConstrainedQuadraticModel): the CQM to create
    
    Returns:
        - null
    '''
    

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


    # Objective
    # 1
    obj1 = dimod.quicksum(
        server_status[s] 
        * tree.idle_powcons[s+tree.SWITCHES] 
        for s in range(tree.SERVERS)
    )
    # 2
    obj2 = dimod.quicksum(
        tree.dyn_powcons[s+tree.SWITCHES] 
        * dimod.quicksum(
            tree.cpu_util[vm] 
            * vm_status[s][vm] 
            for vm in range(tree.VMS)
        ) for s in range(tree.SERVERS)
    )
    # 3
    obj3 = dimod.quicksum(
        switch_status[sw] 
        * tree.idle_powcons[sw] 
        for sw in range(tree.SWITCHES)
    )
    # 4
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
    # Total
    cqm.set_objective(obj1 + obj2 + obj3 + obj4)


    # Constraints
    # (11)     
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

    # (12)
    for vm in range(tree.VMS):
        cqm.add_constraint(
            dimod.quicksum(
                vm_status[s][vm] 
                for s in range(tree.SERVERS)
            ) 
            == 1, 
            label="C12-N{}".format(vm)
        )
        
    # Constraints
    # (13)
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

    # (14) 
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

    # (15)     
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

    # (16)
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

    # (17)      
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

    # (18)(19)       
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



################################################################################################
#                                 LEGACY - UNUSED CODE                                         #
################################################################################################

import hybrid


def check_bqm_feasible(bqm_solution: dict, cqm_model: dimod.ConstrainedQuadraticModel, 
            inverter: dimod.constrained.CQMToBQMInverter):
    '''
    Checks if given sampleset is feasible for the given CQM.

    Args:
        - bqm_solution: the sampleset to check 
            type: sampleset
        - cqm_model: the CQM for checking 
            type: ConstrainedQuadraticModel
        - inverter: the converter from the BQM to the CQM 
            type: CQMToBQMInverter
    
    Returns:
        - null
    '''
    inverted_sample = inverter(bqm_solution)
    
    print("\n\n## Converted Variables ##")

    last_char = ""
    for var, value in inverted_sample.items():
        if last_char != var[0]:         # Var separator
            print(end="\n")
        if value != 0.0:                # Nonzero var printer
            print(var, value, sep = ": ",end= " | ")
        last_char = var[0]          # Update last char to separate vars
    
    print("\n\nFeasible: ", cqm_model.check_feasible(inverted_sample))



def cqm_solver(cqm_problem: dimod.ConstrainedQuadraticModel, problem_label: str, 
            save = False):
    '''
    Solves the CQM problem using a CQM Hybrid Solver and returns
    the results.

    Args:
        - cqm_problem (ConstrainedQuadraticModel): the BQM to 
        solve
        - problem_label (str): the problem label
        - save (bool, optional, default=False): save option
        for the dictionary

    Returns:
        - Tuple: containing the solution's dictionary
        and its execution time
            type: tuple(dict(), int)
    '''
    
    # Create Sampler
    sampler = dwave.system.LeapHybridCQMSampler()

    # Sample results
    sampleset = sampler.sample_cqm(cqm_problem, label = problem_label)

    # Exec time
    exec_time = sampleset.info.get('run_time')
    print("CQM TIME: ", exec_time, " micros")

    # Extract feasible solution
    feasible_sampleset = sampleset.filter(lambda sample: sample.is_feasible)

    # Extract best solution and energy
    best_solution = feasible_sampleset.first[0]
    energy = feasible_sampleset.first[1]

    # Energy
    print("CQM ENERGY: ", str(energy))

    # Extract variables
    print("\n## CQM Variables ##")
    last_char = ""
    for var, value in best_solution.items():
        if last_char != var[0]:         # Var separator
            print(end="\n")
        if value != 0.0:                # Nonzero var printer
            print(var, value, sep = ": ",end= " | ")
        last_char = var[0]          # Update last char to separate vars
    print(end= "\n")
    # Save best solution
    if save:
        with open(("cqm_dict_"+problem_label+".txt"), "w") as fp:
            json.dump(best_solution, fp)
            print(problem_label+" dictionary updated!")

    return (best_solution, exec_time)



def bqm_solver(bqm_problem: dimod.BinaryQuadraticModel, problem_label: str, 
            cqm_time = 0, time_mult = 1):
    '''
    Solves the BQM problem using decomposition and returns
    the result.

    Args:
        - bqm_problem (BinaryQuadraticModel): the BQM to 
        solve
        - problem_label (str): the problem label
        - cqm_time (int, optional, default=0): cqm time
        to compute custom resolve time
        - time_mult (int, optional, default=1): custom
        time multiplier for resolve time

    Returns:
        - best_solution: the solution's dictionary
            type: dict()
    '''   
    # Roof Duality
    # rf_energy, rf_variables = dwave.preprocessing.roof_duality(vm_bqm)
    # print("Roof Duality variables: ", rf_variables)

    # Create Sampler
    sampler = dwave.system.LeapHybridSampler()

    # Sample Results
    if cqm_time:
        sampleset = sampler.sample(bqm_problem, cqm_time//10**6 *time_mult, label = problem_label)
    else:
        sampleset = sampler.sample(bqm_problem, label = problem_label)

    # Exec Time
    exec_time = sampleset.info.get('run_time')
    print("BQM TIME: ", exec_time, " micros")

    # Extract best solution & energy
    best_solution = sampleset.first[0]
    energy = sampleset.first[1]

    # Energy
    print("BQM ENERGY: ", energy)
    # print("Roof Duality Energy: ", rf_energy)

    # Extract variables
    print("\n## BQM Variables ##")
    last_char = ""
    for var, value in best_solution.items():
        if last_char != var[0]:         # Var separator
            print(end="\n")
        if value != 0.0:                # Nonzero var printer
            print(var, value, sep = ": ",end= " | ")
        last_char = var[0]          # Update last char to separate vars
    print(end= "\n")
    
    return best_solution



def merge_substates(_, substates):
    '''
    Minimal function to merge substates in a multiple
    substates per cycle environment
    '''

    a, b = substates
    return a.updated(subsamples=hybrid.hstack_samplesets(a.subsamples, b.subsamples))



def decomposed_solver(bqm_problem: dimod.BinaryQuadraticModel, problem_label: str):
    '''
    Solves the BQM problem using decomposition and returns
    the result.

    Args:
        - bqm_problem (BinaryQuadraticModel): the BQM to 
        solve
        - problem_label (str): the problem label
        - cqm_time (int, optional, default=0): cqm time
        to compute custom resolve time
        - time_mult (int, optional, default=1): custom
        time multiplier for resolve time

    Returns:
        - best_solution: the solution's dictionary
            type: dict()
    '''
    # Decomposer
    decomposer = hybrid.ComponentDecomposer()
    decomposer_random = hybrid.RandomSubproblemDecomposer(size= 10)
    # decomposer = hybrid.Unwind( 
    #                 hybrid.SublatticeDecomposer()
    #             )

    # Subsampler
    qpu = dwave.system.DWaveSampler()
    subsampler = hybrid.QPUSubproblemAutoEmbeddingSampler(
                    qpu_sampler=qpu
    )
    # subsampler = hybrid.Map(
    #                     hybrid.QPUSubproblemAutoEmbeddingSampler(
    #                         qpu_sampler= qpu,
    #                     )
    #             ) | hybrid.Reduce (
    #                     hybrid.Lambda(merge_substates)
    #             )
    
    # Composer
    composer = hybrid.SplatComposer()
    
    # Parallel solvers
    classic_branch = hybrid.InterruptableTabuSampler() 
    
    # Merger
    merger = hybrid.ArgMin()
    # merger = hybrid.GreedyPathMerge()    

    # Branch
    qpu_branch = (decomposer | subsampler | composer) | hybrid.TrackMin(output= True)   # pylint: disable=unsupported-binary-operation
    random_branch = (decomposer_random | subsampler | composer) | hybrid.TrackMin(output= True) # pylint: disable=unsupported-binary-operation
    parallel_branches = hybrid.RacingBranches(
                    classic_branch, 
                    qpu_branch,
                    random_branch,
                    ) | merger

    # Define workflow
    workflow = hybrid.LoopUntilNoImprovement(
                        parallel_branches, 
                        # convergence= 3, 
                        # max_iter= 5, 
                        max_time= 3,
                        )

    # Solve
    origin_embeddings = hybrid.make_origin_embeddings(qpu, )
    init_state = hybrid.State.from_sample(
                        hybrid.random_sample(bqm_problem), 
                        bqm_problem,
                        origin_embeddings= origin_embeddings)
    solution = workflow.run(init_state).result()

    # Print timers
    # hybrid.print_counters(workflow)

    # Extract best solution & energy
    best_solution = solution.samples.first[0]
    energy = solution.samples.first[1]

    # Energy
    print("Decomposer BQM ENERGY: ", energy)

    # Extract variables
    print("\n## Decomposer BQM Variables ##")
    last_char = ""
    for var, value in best_solution.items():
        if last_char != var[0]:         # Var separator
            print(end="\n")
        if value != 0.0:                # Nonzero var printer
            print(var, value, sep = ": ",end= " | ")
        last_char = var[0]          # Update last char to separate vars
    print(end= "\n")
    
    # Extract infos
    print("\n\n## Decomposer BQM Extra Info ##")
    print(solution.info)
    # print(solution)
    

    return best_solution
    


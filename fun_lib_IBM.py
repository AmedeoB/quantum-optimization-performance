# DOCPLEX
from docplex.cp.model import CpoModel, minimize
from docplex.cp.solution import CpoSolveResult
from docplex.cp.solver.solver_listener import AutoStopListener 
from docplex.cp.parameters import CpoParameters
# import cplex

# OTHER
import json

# CUSTOM
from structures import *


def to_dictionary(solution: CpoSolveResult):
    
    dictionary = {}
    for var in solution.get_all_var_solutions():
        dictionary[var.get_name()] = var.get_value() 
    
    sorted_dictionary = {k: v for k, v in sorted(dictionary.items(), key= lambda item: item[0])}

    return sorted_dictionary


def cplex_solver(model: CpoModel, depth: int, problem_label: str,
                 exec_time: int, save_solution = False):

    # model.add_solver_listener(AutoStopListener(
    #                             # qsc_time= min(2**depth, exec_time//10),
    #                             # qsc_time= exec_time,
    #                             # min_sols= 1,
    #                             max_sols=2,
    #                         )
    #                     )

    # c = cplex.Cplex()
    # c.parameters.parallel = -1
    # c.parameters.lpmethod = cplex.Cplex.parameters.lpmethod.values.barrier

    # c = CpoParameters()
    # c.set_attribute('parallel', -1)

    print("Solving...")
    solution = model.solve(
                    TimeLimit= exec_time,
                    SolutionLimit= 1,
                    Workers= 4,
                )

    print(
        f"\n# SOLUTION #\n"
        f"\nSolve Status: {solution.get_solve_status()}"
        f"\nEnergy: {solution.get_objective_value()}"
        f"\nSolve Time: {solution.get_solve_time()}"
    )

    print("\n# VARIABLES \n")    
    if solution.is_solution():
        sol_dictionary = to_dictionary(solution)
        for key, val in sol_dictionary.items():
            if val != 0:
                print(f"{key}: {val}")
    else:   
        sol_dictionary = {}
        save_solution = False

    # Save solution
    if save_solution:
        with open((f"IBM LOGS/depth_{depth}/{problem_label}_solution.txt"), "w") as fp:
            json.dump(sol_dictionary, fp)
            print(f"{problem_label} solution updated!")
    
    # Save values
    dictionary = {}
    dictionary["status"] = solution.get_solve_status() 
    dictionary["time"] = solution.get_solve_time()
    dictionary["energy"] = solution.get_objective_value()
    info_writer(dictionary, f"IBM LOGS/depth_{depth}/{problem_label}_info.txt")



    return sol_dictionary


def vm_cplex_model(model: CpoModel, tree: Proxytree):
    
    # Variables
    server_status = [
        model.binary_var(name= "s{}".format(s)) # pylint: disable=no-member
        for s in range(tree.SERVERS)
    ]
    vm_status = [
        [
            model.binary_var(name= "vm{}-s{}".format(vm, s)) # pylint: disable=no-member
            for vm in range(tree.VMS) 
        ] for s in range(tree.SERVERS)
    ]

    # Constraints
    # (11)
    for s in range(tree.SERVERS):
        model.add_constraint(
            sum(
                (tree.cpu_util[vm] * vm_status[s][vm])
                for vm in range(tree.VMS)
            )
            - (tree.server_capacity[s] * server_status[s])
            <= 0
        )
    # (12)
    for vm in range(tree.VMS):
        model.add_constraint(
            sum(
                vm_status[s][vm] 
                for s in range(tree.SERVERS)
            )
            == 1
        )

    # Objective
    model.add(
        minimize(
            sum(
                (server_status[s] * tree.idle_powcons[s+tree.SWITCHES])
                for s in range(tree.SERVERS)
            ) 
            + sum(
                (tree.dyn_powcons[s+tree.SWITCHES]
                * sum(
                    (vm_status[vm][s] * tree.cpu_util[vm])
                    for vm in range(tree.VMS))
                ) 
                for s in range(tree.SERVERS)
            )
        )
    )    


def path_cplex_model(model: CpoModel, tree: Proxytree, vm_solution: dict):

    # Variables
    switch_status = [
        model.binary_var(name= "sw{}".format(sw)) # pylint: disable=no-member
        for sw in range(tree.SWITCHES)
    ]

    flow_path = {}
    for f in range(tree.FLOWS):
        for n1 in range(tree.NODES):
            for n2 in range(tree.NODES):
                if tree.adjancy_list[n1][n2]:
                    flow_path["f{}-n{}-n{}".format(f, n1, n2)] = model.binary_var("f{}-n{}-n{}".format(f, n1, n2))

    on = {}
    for n1 in range(tree.NODES):
        for n2 in range(n1, tree.NODES):
            if tree.adjancy_list[n1][n2]:
                on["on{}-{}".format(n1, n2)] = model.binary_var("on{}-{}".format(n1, n2))


    # Constraints
    # (13)
    for f in range(tree.FLOWS):
        for s in range(tree.SWITCHES, tree.SWITCHES + tree.SERVERS):           # Start from switches cause nodes are numerated in order -> all switches -> all servers
            if vm_solution.get("vm{}-s{}".format(tree.src_dst[f][0], s-tree.SWITCHES)) == 0:
                model.add_constraint( 
                    sum( 
                        flow_path["f{}-n{}-n{}".format(f, s, sw)] 
                        for sw in range(tree.SWITCHES) 
                        if tree.adjancy_list[s][sw] == 1
                    )
                    == 0
                )

    # (14)
    for f in range(tree.FLOWS):
        for s in range(tree.SWITCHES, tree.SWITCHES + tree.SERVERS):           # Start from switches cause nodes are numerated in order -> all switches -> all servers
            if vm_solution.get("vm{}-s{}".format(tree.src_dst[f][1], s-tree.SWITCHES)) == 0:
                model.add_constraint( 
                    sum( 
                        flow_path["f{}-n{}-n{}".format(f, sw, s)] 
                        for sw in range(tree.SWITCHES) 
                        if tree.adjancy_list[sw][s] == 1
                    )
                    == 0
                )

    # (15)
    for f in range(tree.FLOWS):
        for s in range(tree.SWITCHES, tree.SWITCHES + tree.SERVERS):
            model.add_constraint( 
                vm_solution.get("vm{}-s{}".format(tree.src_dst[f][0], s-tree.SWITCHES)) 
                - vm_solution.get("vm{}-s{}".format(tree.src_dst[f][1], s-tree.SWITCHES))  
                - ( 
                    sum( 
                        flow_path["f{}-n{}-n{}".format(f, s, sw)] 
                        for sw in range(tree.SWITCHES) 
                        if tree.adjancy_list[s][sw] == 1
                    ) 
                    - sum( 
                        flow_path["f{}-n{}-n{}".format(f, sw, s)] 
                        for sw in range(tree.SWITCHES) 
                        if tree.adjancy_list[sw][s] == 1
                    )
                ) 
                == 0
            )

    # (16)
    for sw in range(tree.SWITCHES):
        for f in range(tree.FLOWS):
            model.add_constraint( 
                sum( 
                    flow_path["f{}-n{}-n{}".format(f, n, sw)]  
                    for n in range(tree.NODES) 
                    if tree.adjancy_list[n][sw] == 1
                ) 
                - sum( 
                    flow_path["f{}-n{}-n{}".format(f, sw, n)] 
                    for n in range(tree.NODES) 
                    if tree.adjancy_list[sw][n] == 1
                ) 
                == 0
            )
    
    # (17)
    for l in range(tree.LINKS):
        n1,n2 = get_nodes(l, tree.link_dict)
        model.add_constraint( 
            sum( 
                tree.data_rate[f] * (
                    flow_path["f{}-n{}-n{}".format(f, n1, n2)] 
                    + flow_path["f{}-n{}-n{}".format(f, n2, n1)]
                ) 
                for f in range(tree.FLOWS)
            ) 
            - (tree.link_capacity[l] * on["on{}-{}".format(n1, n2)]) 
            <= 0
        )
    
    # (18-19)
    for l in range(tree.LINKS):
        n1,n2 = get_nodes(l, tree.link_dict)

        model.add_constraint(
            on["on{}-{}".format(n1, n2)] 
            - switch_status[n1] 
            <= 0
        )

        if n2 < tree.SWITCHES:     # If the second node is a switch
            model.add_constraint(
                on["on{}-{}".format(n1, n2)] 
                - switch_status[n2] 
                <= 0
            )
        else:                           # If it's a server
            model.add_constraint(
                on["on{}-{}".format(n1, n2)] 
                - vm_solution.get("s{}".format(n2-tree.SWITCHES)) 
                == 0
            )


    # Objective
    model.add(
        minimize(
            sum(
                (switch_status[sw] * tree.idle_powcons[sw]) 
                for sw in range(tree.SWITCHES)
            )
            + sum(
                    (tree.dyn_powcons[sw] 
                    * (
                        flow_path['f' + str(f) + '-n' + str(n) + '-n' + str(sw)] 
                        + flow_path['f' + str(f) + '-n' + str(sw) + '-n' + str(n)]
                    ))
                for n in range(tree.NODES) 
                for f in range(tree.FLOWS) 
                for sw in range(tree.SWITCHES) 
                if tree.adjancy_list[n][sw] == 1
            )
        )
    )


def full_cplex_model(model: CpoModel, tree: Proxytree):
    # Variables
    server_status = [
        model.binary_var(name= "s{}".format(s)) # pylint: disable=no-member
        for s in range(tree.SERVERS)
    ]
    vm_status = [
        [
            model.binary_var(name= "vm{}-s{}".format(vm, s)) # pylint: disable=no-member
            for vm in range(tree.VMS) 
        ] for s in range(tree.SERVERS)
    ]
    switch_status = [
        model.binary_var(name= "sw{}".format(sw)) # pylint: disable=no-member
        for sw in range(tree.SWITCHES)
    ]

    flow_path = {}
    for f in range(tree.FLOWS):
        for n1 in range(tree.NODES):
            for n2 in range(tree.NODES):
                if tree.adjancy_list[n1][n2]:
                    flow_path["f{}-n{}-n{}".format(f, n1, n2)] = model.binary_var("f{}-n{}-n{}".format(f, n1, n2))

    on = {}
    for n1 in range(tree.NODES):
        for n2 in range(n1, tree.NODES):
            if tree.adjancy_list[n1][n2]:
                on["on{}-{}".format(n1, n2)] = model.binary_var("on{}-{}".format(n1, n2))

    # Constraints
    # (11)
    for s in range(tree.SERVERS):
        model.add_constraint(
            sum(
                (tree.cpu_util[vm] * vm_status[s][vm])
                for vm in range(tree.VMS)
            )
            - (tree.server_capacity[s] * server_status[s])
            <= 0
        )
    # (12)
    for vm in range(tree.VMS):
        model.add_constraint(
            sum(
                vm_status[s][vm] 
                for s in range(tree.SERVERS)
            )
            == 1
        )
    # (13)
    for f in range(tree.FLOWS):
        for s in range(tree.SWITCHES, tree.SWITCHES + tree.SERVERS):           # Start from switches cause nodes are numerated in order -> all switches -> all servers
                model.add_constraint( 
                    sum( 
                        flow_path["f{}-n{}-n{}".format(f, s, sw)] 
                        for sw in range(tree.SWITCHES) 
                        if tree.adjancy_list[s][sw] == 1
                    )
                    - vm_status[tree.src_dst[f][0]][s-tree.SWITCHES]
                    <= 0
                )

    # (14)
    for f in range(tree.FLOWS):
        for s in range(tree.SWITCHES, tree.SWITCHES + tree.SERVERS):           # Start from switches cause nodes are numerated in order -> all switches -> all servers
                model.add_constraint( 
                    sum( 
                        flow_path["f{}-n{}-n{}".format(f, sw, s)] 
                        for sw in range(tree.SWITCHES) 
                        if tree.adjancy_list[sw][s] == 1
                    )
                    - vm_status[tree.src_dst[f][1]][s-tree.SWITCHES]
                    <= 0
                )

    # (15)
    for f in range(tree.FLOWS):
        for s in range(tree.SWITCHES, tree.SWITCHES + tree.SERVERS):
            model.add_constraint( 
                vm_status[tree.src_dst[f][0]][s-tree.SWITCHES]
                - vm_status[tree.src_dst[f][1]][s-tree.SWITCHES]  
                - ( 
                    sum( 
                        flow_path["f{}-n{}-n{}".format(f, s, sw)] 
                        for sw in range(tree.SWITCHES) 
                        if tree.adjancy_list[s][sw] == 1
                    ) 
                    - sum( 
                        flow_path["f{}-n{}-n{}".format(f, sw, s)] 
                        for sw in range(tree.SWITCHES) 
                        if tree.adjancy_list[sw][s] == 1
                    )
                ) 
                == 0
            )

    # (16)
    for sw in range(tree.SWITCHES):
        for f in range(tree.FLOWS):
            model.add_constraint( 
                sum( 
                    flow_path["f{}-n{}-n{}".format(f, n, sw)]  
                    for n in range(tree.NODES) 
                    if tree.adjancy_list[n][sw] == 1
                ) 
                - sum( 
                    flow_path["f{}-n{}-n{}".format(f, sw, n)] 
                    for n in range(tree.NODES) 
                    if tree.adjancy_list[sw][n] == 1
                ) 
                == 0
            )
    
    # (17)
    for l in range(tree.LINKS):
        n1,n2 = get_nodes(l, tree.link_dict)
        model.add_constraint( 
            sum( 
                tree.data_rate[f] * (
                    flow_path["f{}-n{}-n{}".format(f, n1, n2)] 
                    + flow_path["f{}-n{}-n{}".format(f, n2, n1)]
                ) 
                for f in range(tree.FLOWS)
            ) 
            - (tree.link_capacity[l] * on["on{}-{}".format(n1, n2)]) 
            <= 0
        )
    
    # (18-19)
    for l in range(tree.LINKS):
        n1,n2 = get_nodes(l, tree.link_dict)

        model.add_constraint(
            on["on{}-{}".format(n1, n2)] 
            - switch_status[n1] 
            <= 0
        )

        if n2 < tree.SWITCHES:     # If the second node is a switch
            model.add_constraint(
                on["on{}-{}".format(n1, n2)] 
                - switch_status[n2] 
                <= 0
            )
        else:                           # If it's a server
            model.add_constraint(
                on["on{}-{}".format(n1, n2)] 
                - server_status[n2-tree.SWITCHES] 
                <= 0
            )
    

    # Objective
    model.add(
        minimize(
            sum(
                (server_status[s] * tree.idle_powcons[s+tree.SWITCHES])
                for s in range(tree.SERVERS)
            ) 
            + sum(
                (tree.dyn_powcons[s+tree.SWITCHES]
                * sum(
                    (vm_status[vm][s] * tree.cpu_util[vm])
                    for vm in range(tree.VMS))
                ) 
                for s in range(tree.SERVERS)
            )
            + sum(
                (switch_status[sw] * tree.idle_powcons[sw]) 
                for sw in range(tree.SWITCHES)
            )
            + sum(
                    (tree.dyn_powcons[sw] 
                    * (
                        flow_path["f{}-n{}-n{}".format(f, n, sw)] 
                        + flow_path["f{}-n{}-n{}".format(f, sw, n)]
                    ))
                for n in range(tree.NODES) 
                for f in range(tree.FLOWS) 
                for sw in range(tree.SWITCHES) 
                if tree.adjancy_list[n][sw] == 1
            )
        )
    )
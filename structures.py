import random
from os.path import exists



class Proxytree():
    
    '''
    A class to define the tree and manage all the constants and its structure.
    
    Args:
        - depth (int): the tree depth
        - server_c (int): the servers capacity
        - link_c (int): the links capacity * 
        - idle_pc (int): idle powcons of nodes *
        - dyn_pc (int): dynamic powcons of nodes *
        - datar_avg (int): the average datarate of flows
        - random_tree (bool, Optional, default = False): makes the tree
            structure rand

    * will be multiplied by tree levels, changes every level
    '''

    def __init__(self, depth, server_c, link_c, idle_pc, dyn_pc, datar_avg, random_tree = False):        
        self.DEPTH = depth

        self.SERVER_C = server_c                                                    # Server capacity
        self.LINK_C = link_c*self.DEPTH                                             # Link capacity
        self.LINK_C_DECREASE = 2
        self.IDLE_PC = idle_pc*self.DEPTH                                           # Idle power consumption
        self.IDLE_PC_DECREASE = 5                                                   # Idle power consumption
        self.DYN_PC = dyn_pc*self.DEPTH                                             # Dynamic power consumption
        self.DYN_PC_DECREASE = 1                                                    # Dynamic power consumption
        self.DATAR_AVG = datar_avg                                                  # Average data rate per flow

        self.SERVERS = pow(2, self.DEPTH)                                           # Server number
        self.SWITCHES = sum(pow(2,lvl) for lvl in range(self.DEPTH))                # Switch number
        self.VMS = self.SERVERS                                                     # VM number per server
        self.FLOWS = self.VMS//2 if self.VMS%2==0 else self.VMS//2+1                # Flow number
        self.NODES = self.SERVERS + self.SWITCHES                                   # Total Nodes
        self.LINKS = 0
        self.__init_links()

        self.server_capacity = [self.SERVER_C for _ in range(self.SERVERS)]         # Capacity of each server
        self.link_capacity = []
        self.idle_powcons = []                                                      # Idle power consumption of each node
        self.dyn_powcons = []                                                       # Dynamic power of each node
        self.__init_link_capacity()
        self.__init_idle_dyn_powcons()
        if random_tree:
            self.cpu_util = [
                        random.randint(self.SERVER_C//2 +1, self.SERVER_C-1) 
                        for _ in range(self.VMS)
                        ]                                                           # CPU utilization of each VM
            self.data_rate = [
                        random.randint(self.DATAR_AVG-1 , self.DATAR_AVG+1)
                        for _ in range(self.FLOWS)
                        ]                                                           # Data rate of flow f on link l
        else:
            self.cpu_util = [server_c//2+1 for _ in range(self.VMS)]                # CPU utilization of each VM
            self.data_rate = [datar_avg for _ in range(self.FLOWS)]                 # Data rate of flow f on link l 
        
        self.link_dict = {}
        self.adjancy_list = [
                        [0 for _ in range(self.NODES)] 
                        for _ in range(self.NODES)
                        ] 
        self.__init_link_dict_adj_list()

        self.src_dst = [
                    [0 for _ in range(2)] 
                    for _ in range(self.FLOWS)
                    ]
        self.__init_src_dst(random_tree)


    def __init_links(self):
        '''
        Computes links number.
        '''

        for i in range(self.DEPTH-1):
            self.LINKS += 2**i * 2**(i+1)
        self.LINKS += 2*(2**(self.DEPTH-1))
    

    def __init_link_capacity(self):
        '''
        Initialize link_capacity list
        '''

        start_link_c = self.LINK_C
        # Switch links
        for lvl in range(self.DEPTH-1):
            for _ in range(2**(2*lvl+1)):
                self.link_capacity.append(start_link_c)
            start_link_c -= self.LINK_C_DECREASE
        # Server links
        for _ in range(2**self.DEPTH):
            self.link_capacity.append(start_link_c)
        

    def __init_idle_dyn_powcons(self):
        '''
        Initialize nodes' idle and dynamic powcons lists
        '''

        start_idle_pc = self.IDLE_PC
        start_dyn_pc = self.DYN_PC
        for lvl in range(self.DEPTH+1):
            for _ in range(2**lvl):
                self.idle_powcons.append(start_idle_pc)
                self.dyn_powcons.append(start_dyn_pc)
            start_idle_pc -= self.IDLE_PC_DECREASE
            start_dyn_pc -= self.DYN_PC_DECREASE


    def __init_link_dict_adj_list(self):
        '''
        Computes the adjancy_list matrix and fills
        the link_dict dictionary with the nodes couples
        and associated link number.
        '''
        
        link_counter = 0
        # Create all sw-sw links
        for lvl in range(self.DEPTH-1):
            if lvl == 0:
                for i in range(1,3):
                    self.adjancy_list[0][i] = 1
                    self.adjancy_list[i][0] = 1
                    self.link_dict[str((0,i))] = link_counter
                    self.link_dict[str((i,0))] = link_counter
                    link_counter += 1
            else:
                first_sw = 2**(lvl) - 1
                last_sw = first_sw * 2
                for father in range(first_sw, last_sw + 1):
                    first_son = 2**(lvl+1) - 1
                    last_son = first_son * 2
                    for son in range(first_son, last_son + 1):
                        self.adjancy_list[father][son] = 1
                        self.adjancy_list[son][father] = 1
                        self.link_dict[str((father,son))] = link_counter
                        self.link_dict[str((son,father))] = link_counter
                        link_counter += 1
        
        # Last layer first and last switch
        ll_firstsw = 2**(self.DEPTH-1) - 1
        ll_lastsw = ll_firstsw * 2
        
        # Create all sw-s links
        for father in range(ll_firstsw, ll_lastsw + 1):
            for i in range(2):
                son = father * 2 + 1 + i

                self.adjancy_list[father][son] = 1
                self.adjancy_list[son][father] = 1
                self.link_dict[str((father,son))] = link_counter
                self.link_dict[str((son,father))] = link_counter
                link_counter += 1


    def __init_src_dst(self, random_tree):
        '''
        Initialize the source-destination matrix.
        '''

        index_list = [i for i in range(self.VMS)]
        if random_tree:  random.shuffle(index_list)
        for i in range(self.FLOWS):
            for j in range(2):
                self.src_dst[i][j] = index_list[i*2 + j]


    def print_tree(self):
        '''
        Prints the whole tree structure.
        '''

        print("SWITCH Indexes: ", *[k for k in range(self.SWITCHES)])
        print("SERVER Indexes: ", *[s+self.SWITCHES for s in range(self.SERVERS)])
        print("SERVER Capacity: ", *[s for s in self.server_capacity])
        print("LINK Capacity: ", *[s for s in self.link_capacity])
        print("IDLE Power Consumption: ", *[s for s in self.idle_powcons])
        print("DYNAMIC Power Consumption: ", *[s for s in self.dyn_powcons])
        print("VM's CPU Utilization: ", *[s for s in self.cpu_util])
        print("Flow Path Data Rate: ", *[s for s in self.data_rate])
        print("\n\n")

        print("### Tree Structure ###")
        for i in range(len(self.adjancy_list)):
            print("\nNodo ", i, " collegato ai nodi:", end="\t")
            for j in range(len(self.adjancy_list)):
                if self.adjancy_list[i][j] == 1:
                    print(j, " (link ", self.link_dict.get(str((i,j))) ,")", sep="", end="\t")
        print("\n\n")

        print("### VM Paths ###")
        for path in self.src_dst:
            print("Path ", self.src_dst.index(path), ": ", end="\t")
            print( *[s for s in path], sep="  -  ")
        print("\n")



class CQMmanager():
    '''
    A class to manage all main_CQM constant

    Args:
        - save_solution_vm (bool, optional, default=False): save
            vm assignment solution
        - save_info_vm (bool, optional, default=False): save 
            vm assignment info
        - load_solution (bool, optional, default=False): load
            vm assignment solution from file
        - save_solution_path (bool, optional, default=False): save 
            path planner solution
        - save_info_path (bool, optional, default=False): save 
            path planner info
        - save_solution_full (bool, optional, default=False): save 
            full problem solution
        - save_info_full (bool, optional, default=False): save 
            full problem info
    '''
    def __init__(
                self, 
                save_solution_vm = False, 
                save_info_vm = False, 
                load_solution = False, 
                save_solution_path = False, 
                save_info_path = False,
                save_solution_full = False, 
                save_info_full = False
            ):
        
        self.SAVE_VM_SOL = save_solution_vm
        self.SAVE_VM_INFO = save_info_vm
        self.LOAD_SOL = load_solution
        self.SAVE_PATH_SOL = save_solution_path
        self.SAVE_PATH_INFO = save_info_path
        self.SAVE_FULL_SOL = save_solution_full
        self.SAVE_FULL_INFO = save_info_full
    
    def print_manager(self):
        print(
            f"# CQM Manager Structure #"
            f"\nSave VM Solution:   {self.SAVE_VM_SOL}"
            f"\nSave VM Info:       {self.SAVE_VM_INFO}"
            f"\nLoad VM Solution:   {self.LOAD_SOL}"
            f"\nSave PATH Solution: {self.SAVE_PATH_SOL}"
            f"\nSave PATH Info:     {self.SAVE_PATH_INFO}"
            f"\nSave FULL Solution: {self.SAVE_FULL_SOL}"
            f"\nSave FULL Info:     {self.SAVE_FULL_INFO}"
        )
        


def get_nodes(l, dictionary):
    '''
    A function that returns a tuple (n1,n2) containing
    the nodes linked by link l and saved in a dictionary
    with structure {(n1,n2) = l}

    Args:
        - l (int): the link index
        - dictionary (dict): the dictionary containing
        the couple
    
    Returns:
        - Tuple(int, int): nodes indexes
    '''
    
    values = list(dictionary.values())
    index = values.index(l)
    nodes = list(dictionary.keys())[index]
    nodes = nodes.replace("(", "")
    nodes = nodes.replace(")", "")
    
    return tuple(map(int, nodes.split(', ')))



def print_section(section_name: str):
    '''
    A standard printing formatting for section separation. 
    Automatically converts text to uppercase.

    Args:
        - section_name (str): the name of the section
    '''
    
    print(
        f"\n####################### {section_name.upper()} ###########################"
        f"\n"
    )



def dict_filter(pair):
    '''
    Filters an info dictionary extracting only run_time.
    '''
    key, _ = pair
    return "time" in key 



def info_writer(dictionary: dict, path: str):
    '''
    Writes solution on a file.

    Args:
        - dictionary (dict): a dictionary to save
        - path (str): file path
    '''
    writeheads = False
    if not exists(path): writeheads = True
    
    with open(path,"a") as file:
        # Keys
        if writeheads:
            for k in dictionary.keys():
                file.write(f"{k}\t")
            file.write("\n")
        
        # Values
        for v in dictionary.values():
            file.write(f"{v}\t")
        file.write("\n")
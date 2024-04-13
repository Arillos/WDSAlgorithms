"""
          Name:     Algorithm 2- Algorytm wyznaczania tras przepływu wody
        Author:     Ariel Antonowicz
   Last update:     26.02.2022
"""
import wntr
import copy
import os, glob
from config import Configuration_data


class Algorithm2:

    def __init__(self):
        self.init_config = Configuration_data()
        self.inp_file =

        self.nodes_to_check = list()
        self.results = list()
        self.wn = wntr.network.WaterNetworkModel(self.inp_file)
        self.wn.options.time.duration = self.init_config.sim_duration
        self.sim = wntr.sim.EpanetSimulator(wn=self.wn)

    def __del__(self):
        for filename in glob.glob("temp*"):
            os.remove(filename)

    def run_simulation(self, wn, source):
        simulation_results = list()
        sim = wntr.sim.EpanetSimulator(wn=wn)

        wn.options.quality.parameter = 'TRACE'
        wn.options.quality.trace_node = source

        for step in range(0, self.init_config.sim_duration + 1, 1):
            wn.options.time.duration = step * 3600
            simulation_results = sim.run_sim()

        return {'quality': simulation_results.node['quality'].to_dict('index'),
                'flow': simulation_results.link['flowrate'].to_dict('index')}

    def check_neighbours(self, node_id):
        node_neighbours_list = list()

        for link in self.wn.link_name_list:
            if node_id == self.wn.get_link(link).todict()['start_node_name']:
                node_neighbours_list.append({'node_id': node_id, 'link_id': link, 'start_node_id': node_id, 'end_node_id': self.wn.get_link(link).todict()['end_node_name']})

            elif node_id == self.wn.get_link(link).todict()['end_node_name']:
                node_neighbours_list.append({'node_id': node_id, 'link_id': link, 'start_node_id': self.wn.get_link(link).todict()['start_node_name'], 'end_node_id': node_id})

        return node_neighbours_list

    def water_trace_data(self, node_id):
        # Create source list:
        source_list = list(self.wn.nodes.reservoir_names)
        source_list.extend(list(self.wn.nodes.tank_names))

        result = list()

        self.nodes_to_check.append(node_id)

        for node in self.nodes_to_check:
            node_neighbours_list = self.check_neighbours(node)          # Find node neighbours (and links ID)

            wn = wntr.network.WaterNetworkModel(self.inp_file)
            sim_result = self.run_simulation(wn, source=node)

            quality_results = copy.deepcopy(sim_result['quality'])
            flow_results = copy.deepcopy(sim_result['flow'])

            for step in quality_results:

                for neighbour in node_neighbours_list:
                    link_id = neighbour['link_id']
                    neighbour['sim_step'] = step
                    neighbour['flow'] = copy.deepcopy(flow_results[step][link_id])

                    if (neighbour['start_node_id'] == neighbour['node_id']) and (neighbour['flow'] > 0):
                        neighbour['role'] = {'node_id': neighbour['node_id'], 'neighbour_id': neighbour['end_node_id'], 'status': 'giver'}
                    elif (neighbour['start_node_id'] == neighbour['node_id']) and (neighbour['flow'] < 0):
                        neighbour['role'] = {'node_id': neighbour['node_id'], 'neighbour_id': neighbour['end_node_id'], 'status': 'receiver'}
                        if (neighbour['end_node_id'] not in source_list) and (neighbour['end_node_id'] not in self.nodes_to_check) and neighbour['end_node_id'] != node:
                            self.nodes_to_check.append(neighbour['end_node_id'])
                    elif (neighbour['end_node_id'] == neighbour['node_id']) and (neighbour['flow'] > 0):
                        neighbour['role'] = {'node_id': neighbour['node_id'], 'neighbour_id': neighbour['start_node_id'], 'status': 'receiver'}
                        if (neighbour['start_node_id'] not in source_list) and (neighbour['start_node_id'] not in self.nodes_to_check) and neighbour['start_node_id'] != node:
                            self.nodes_to_check.append(neighbour['start_node_id'])
                    else:
                        neighbour['role'] = {'node_id': neighbour['node_id'], 'neighbour_id': neighbour['start_node_id'], 'status': 'giver'}
                    result.append(copy.deepcopy(neighbour))
        return result

    def path_creator(self, node_id):
        data = self.water_trace_data(node_id)
        simple_info = list()
        node_list = list()
        givers = dict()
        path = dict()

        for case in data:
            if case['role']['status'] == 'receiver':
                if case['start_node_id'] not in node_list:
                    node_list.append(case['start_node_id'])
                if case['end_node_id'] not in node_list:
                    node_list.append(case['end_node_id'])

                simple_info.append({'step': case['sim_step'],
                                    'rec': case['node_id'],
                                    'giv': case['role']['neighbour_id'],
                                    'flow': case['flow'],
                                    'link_id': case['link_id']})

        for step in range(0, self.init_config.sim_duration * 3600, 3600):
            path[step] = list()
            for node in node_list:
                givers[node] = list()
                for item in simple_info:
                    if item['step'] == step:
                        if node == item['giv']:
                            givers[node].append([item['rec'], item['link_id']])
            path[step].append(givers)

        return path

    def critical_pipes(self, node_id):
        data = self.water_trace_data(node_id)
        pipe_id_list = list()
        result = dict()

        for case in data:
            if case['role']['status'] == 'receiver':
                if case['link_id'] not in pipe_id_list:
                    pipe_id_list.append(case['link_id'])

        for link in pipe_id_list:
            result[link] = 0

        for case in data:
            if case['link_id'] in pipe_id_list:
                result[case['link_id']] = result[case['link_id']] + abs(case['flow'])

        return result

# =============================================================================== Main
new_case = Algorithm_2()
new_case.path_creator(node_id='J14')
new_case.critical_pipes('J14')
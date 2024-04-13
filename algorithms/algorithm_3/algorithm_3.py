"""
          Name:     Algorithm 3 - Algorytm typowania zasuw do zamknięcia
        Author:     Ariel Antonowicz
   Last update:     28.02.2022
"""
import wntr
import wntr.network.controls as controls
import pandas as pd
import itertools
import json
import os, glob
import time
import copy
import matplotlib.pyplot as plt
from config import Configuration_data


class Algorithm_3:

    def __init__(self):

        self.init_config = Configuration_data()
        self.inp_file = self.init_config.networks_path + self.init_config.inp_file_name + '.inp'

        self.wn = wntr.network.WaterNetworkModel(self.inp_file)
        self.wn.options.time.duration = self.init_config.sim_duration
        self.sim = wntr.sim.EpanetSimulator(wn=self.wn)

        self.valve_info = self.init_config.valve_info_path + self.init_config.valve_info + '.json'
        self.segments = self.init_config.segments_info_path + self.init_config.segments + '.json'
        self.matrix_a = self.init_config.matrix_path + self.init_config.matrix_a + '.csv'
        self.matrix_b = self.init_config.matrix_path + self.init_config.matrix_b + '.csv'
        self.matrix_c = self.init_config.matrix_path + self.init_config.matrix_c + '.csv'

        with open(self.valve_info, "r") as jsonFile:
            self.valves = json.load(jsonFile)

    def __del__(self):
        for filename in glob.glob("temp*"):
            os.remove(filename)

    def valve_to_pipe_references(self, pipe_id):

        segment = self.find_segment(pipe_id)
        valve_to_pipe_reference = dict()

        for valve in segment['segment_valves']:
            valve_to_pipe_reference[valve] = list()
            for data in self.valves[self.init_config.valve_set]:
                if valve == data['valve_id']:
                    if data['data']['link_id'] in segment['segment_links']:
                        start_node = self.wn.get_link(data['data']['link_id']).todict()['start_node']
                        end_node = self.wn.get_link(data['data']['link_id']).todict()['end_node']

                        if str(start_node) in segment['near_node_list']:
                            for link in self.wn.link_name_list:
                                if str(link) not in segment['segment_links']:
                                    if str(start_node) == str(self.wn.get_link(link).todict()['start_node']) or str(start_node) == str(self.wn.get_link(link).todict()['end_node']):
                                        valve_to_pipe_reference[valve].append(link)

                        if str(end_node) in segment['near_node_list']:
                            for link in self.wn.link_name_list:
                                if str(link) not in segment['segment_links']:
                                    if str(end_node) == str(self.wn.get_link(link).todict()['start_node']) or str(end_node) == str(self.wn.get_link(link).todict()['end_node']):
                                        valve_to_pipe_reference[valve].append(link)

                    else:
                        valve_to_pipe_reference[valve].append(data['data']['link_id'])
        return [valve_to_pipe_reference, segment['segment_valves']]

    def create_use_case(self, pipe_id):
        valve_to_pipe_ref, valves = self.valve_to_pipe_references(pipe_id)
        use_case_list = list()

        for valve in valves:
            temp = copy.deepcopy(valves)
            temp.remove(valve)
            use_case_list.append(temp)

        return [use_case_list, valve_to_pipe_ref]

    def min_number_of_valves(self, pipe_id):
        use_cases, ref = self.create_use_case(pipe_id)

        # Reference simulation:
        simulation_results = list()
        flow_result = list()
        pipe_to_close = list()
        ref_sum_open = 0
        ref_sum_close = 0
        use_cases_result= list()

        for pipe in ref.values():
            pipe_to_close.extend(pipe)

        self.wn = wntr.network.WaterNetworkModel(self.inp_file)
        self.sim = wntr.sim.EpanetSimulator(wn=self.wn)

        for step in range(0, self.init_config.sim_duration, 1):
            self.wn.options.time.duration = step * 3600
            simulation_results = self.sim.run_sim()
        flow_result.append(simulation_results.link['flowrate'].to_dict('index'))

        for x in range(0, len(flow_result), 1):
            ref_sum_open = ref_sum_open + flow_result[x][x * 3600][pipe_id]

        self.wn = wntr.network.WaterNetworkModel(self.inp_file)
        self.sim = wntr.sim.EpanetSimulator(wn=self.wn)
        flow_result.clear()

        for pipe in pipe_to_close:
            act = controls.ControlAction(self.wn.get_link(pipe), 'status', 0)
            cond = controls.SimTimeCondition(self.wn, controls.Comparison.ge, '00:00:00')

            ctr1 = controls.Control(cond, act)
            self.wn.add_control('control' + str(pipe), ctr1)

        for step in range(0, self.init_config.sim_duration, 1):
            self.wn.options.time.duration = step * 3600
            simulation_results = self.sim.run_sim()
        flow_result.append(simulation_results.link['flowrate'].to_dict('index'))

        for x in range(0, len(flow_result), 1):
            ref_sum_close = ref_sum_close + flow_result[x][x * 3600][pipe_id]

        # Use cases sim:
        for case in use_cases:
            link_to_close = list()
            for valve in case:
                for val in ref:
                    if valve == val:
                        link_to_close.extend(ref[val])

            self.wn = wntr.network.WaterNetworkModel(self.inp_file)
            self.sim = wntr.sim.EpanetSimulator(wn=self.wn)
            flow_result.clear()

            for pipe in link_to_close:
                act = controls.ControlAction(self.wn.get_link(pipe), 'status', 0)
                cond = controls.SimTimeCondition(self.wn, controls.Comparison.ge, '00:00:00')

                ctr1 = controls.Control(cond, act)
                self.wn.add_control('control' + str(pipe), ctr1)

            for step in range(0, self.init_config.sim_duration, 1):
                self.wn.options.time.duration = step * 3600
                simulation_results = self.sim.run_sim()
            flow_result.append(simulation_results.link['flowrate'].to_dict('index'))

            flow = 0
            for x in range(0, len(flow_result), 1):
                flow = flow + flow_result[x][x * 3600][pipe_id]
            case.append(flow)

            if case[-1] <= 0:
                use_cases_result.append(case)

        if len(use_cases_result) == 0:
            return ref.keys()
        else:
            return use_cases_result[0][0:-1]

    def matrix_a_creator(self):
        matrix_a = pd.DataFrame([], self.wn.node_name_list, self.wn.link_name_list)

        for link in self.wn.link_name_list:
            for node in self.wn.node_name_list:
                if self.wn.links[self.wn.get_link(link)].todict()['start_node_name'] == str(node):
                    matrix_a.loc[node, link] = 1
                if self.wn.links[self.wn.get_link(link)].todict()['end_node_name'] == str(node):
                    matrix_a.loc[node, link] = 1
        matrix_a.to_csv(self.matrix_a)
        return matrix_a

    def matrix_b_creator(self):
        matrix_b = pd.DataFrame([], self.wn.node_name_list, self.wn.link_name_list)

        for link in self.wn.link_name_list:
            for node in self.wn.node_name_list:
                for valve in self.valves[self.init_config.valve_set]:
                    if (valve['data']['node_id'] == node) and (valve['data']['link_id'] == link):
                        matrix_b.loc[node, link] = 1

        matrix_b.to_csv(self.matrix_b)
        return matrix_b

    def matrix_c_creator(self):
        matrix_a = self.matrix_a_creator()
        matrix_b = self.matrix_b_creator()
        matrix_c = pd.DataFrame([], self.wn.node_name_list, self.wn.link_name_list)

        for link in self.wn.link_name_list:
            for node in self.wn.node_name_list:
                if matrix_a.loc[node, link] == 1 and matrix_b.loc[node, link] == 1:
                    pass
                elif matrix_a.loc[node, link] == 1 or matrix_b.loc[node, link] == 1:
                    matrix_c.loc[node, link] = 1

        matrix_c.to_csv(self.matrix_c)
        return matrix_c

    def search_in_row(self, node_id, matrix):
        results = list()
        for link in self.wn.link_name_list:
            if matrix.loc[node_id, link] == 1:
                results.append(link)
        return results

    def search_in_column(self, link_id, matrix):
        results = list()
        for node in self.wn.node_name_list:
            if matrix.loc[node, link_id] == 1:
                results.append(node)
        return results

    def find_segment(self, pipe_id):
        pipe_list = list()
        node_list = list()
        near_node_list = list()

        matrix_a = self.matrix_a_creator()
        matrix_b = self.matrix_b_creator()
        matrix_c = self.matrix_c_creator()

        pipe_list.append(pipe_id)

        # Find nodes and links ID belongs to segment
        for pipe in pipe_list:
            for res in self.search_in_column(pipe, matrix_c):
                if res not in node_list:
                    node_list.append(res)
            for node in node_list:
                for res in self.search_in_row(node, matrix_c):
                    if res not in pipe_list:
                        pipe_list.append(res)

        # Find segment near nodes
        for pipe in pipe_list:
            for res in self.search_in_column(pipe, matrix_a):
                if res not in node_list:
                    near_node_list.append(res)

        # Find valves needed to close analyzed segment
        valve_list = list()

        for node in node_list:
            for valve in self.valves[self.init_config.valve_set]:
                if valve['data']['node_id'] == node:
                    valve_list.append(valve['valve_id'])

        for node in near_node_list:
            for valve in self.valves[self.init_config.valve_set]:
                if (valve['data']['node_id'] == node) and (valve['data']['link_id'] in pipe_list):
                    valve_list.append(valve['valve_id'])

        return {'link_id': pipe_id, 'segment_links': pipe_list, 'segment_nodes': node_list, 'near_node_list': near_node_list, 'segment_valves': valve_list}

    def find_all_segments(self):
        link_list = self.wn.links.pipe_names
        segments_list = list()

        segment_id = 1

        for link in link_list:
            result = self.find_segment(link)

            count = 0
            for seg in segments_list:
                if result['link_id'] in seg['segment_links']:
                    count = count + 1
            del result['link_id']
            if count == 0:
                result['segment_id'] = 'S' + str(segment_id)
                segments_list.append(result)
                segment_id = segment_id + 1
        # segments_list.append({'valve_set_id': self.init_config.valve_set})
        return {'valve_set_id': self.init_config.valve_set, 'data': segments_list}

    def save_segments(self):
        data = self.find_all_segments()

        with open(self.segments, "w") as jsonFile:
            json.dump(data, jsonFile)


# =============================================================================== Main
# new_case = Algorithm_3()
# new_case.matrix_a_creator()
# new_case.matrix_b_creator()
# new_case.matrix_c_creator()
#
# new_case.find_all_segments()
# new_case.save_segments()
# new_case.min_number_of_valves('P38')

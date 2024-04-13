"""
          Name:     Algorithm 7 - Szeregowanie zadań ekip naprawczych
        Author:     Ariel Antonowicz
   Last update:     29.03.2022
"""
from algorithms.algorithm_6.algorithm_6 import *
from config import Configuration_data


class Algorithm_7:
    def __init__(self):
        self.init_config = Configuration_data()
        self.inp_file = self.init_config.networks_path + self.init_config.inp_file_name + '.inp'

        self.aggregation_result = self.init_config.results_path + self.init_config.aggregation_result + '.json'
        self.failures_info = self.init_config.failures_path + self.init_config.failures_info + '.json'
        self.segment_info = self.init_config.segments_info_path + self.init_config.segments + '.json'
        self.valve_info = self.init_config.valve_info_path + self.init_config.valve_info + '.json'

        self.wn = wntr.network.WaterNetworkModel(self.inp_file)
        self.wn.options.time.duration = self.init_config.sim_duration
        self.sim = wntr.sim.EpanetSimulator(wn=self.wn)

        self.failures = None
        self.additional_info = None
        self.classification_and_prioritization = Algorithm_5()
        self.aggregation = Algorithm_6()

        self.scenario_info = self.init_config.scenarios_path + self.init_config.scenario_file + '.json'
        with open(self.scenario_info, "r") as jsonFile:
            self.scenario_info = json.load(jsonFile)

        with open(self.failures_info, "r") as jsonFile:
            self.failures = json.load(jsonFile)

        with open(self.valve_info, "r") as jsonFile:
            self.valves = json.load(jsonFile)

        with open(self.segment_info, "r") as jsonFile:
            self.segments = json.load(jsonFile)

        self.additional_info = self.init_config.additional_data_path + self.init_config.additional_info + '.json'
        with open(self.additional_info, "r") as jsonFile:
            self.additional_info = json.load(jsonFile)

    def __del__(self):
        for filename in glob.glob("temp*"):
            os.remove(filename)

    def update_data(self):
        self.classification_and_prioritization.update_data()

        with open(self.failures_info, "r") as jsonFile:
            self.failures = json.load(jsonFile)

        self.aggregation.save_proposition_of_aggregation()
        self.additional_info = self.init_config.additional_data_path + self.init_config.additional_info + '.json'
        with open(self.additional_info, "r") as jsonFile:
            self.additional_info = json.load(jsonFile)

        return self.failures

    def create_levels(self, aggregation=True):

        levels = {'L1': list(), 'L2': list(), 'L3': list(), 'L4': list()}
        remove_list = list()
        failures = copy.deepcopy(self.failures[self.init_config.failures_set]['data'])

        if aggregation:
            aggregated_pipes = list()

            with open(self.aggregation_result, "r") as jsonFile:
                self.aggregation_result = json.load(jsonFile)

            for fail in self.aggregation_result[0]['aggregation_first_degree']:
                if fail['failures'][0][5:] and fail['failures'][1][5:] not in aggregated_pipes:
                    aggregated_pipes.append(fail['failures'][0][5:])
                    aggregated_pipes.append(fail['failures'][1][5:])

                    new_fail = dict()
                    repair_time = list()
                    classification = list()

                    new_fail['failure_id'] = 'AG_' + fail['failures'][0] + fail['failures'][1][4:]
                    new_fail['pipe_id'] = [fail['failures'][0][5:], fail['failures'][1][5:]]
                    new_fail['failure_type'] = list()
                    new_fail['pipe_diameter'] = list()
                    new_fail['historical_data'] = list()
                    new_fail['failure_start'] = list()
                    new_fail['type_of_substrate'] = list()
                    new_fail['place_of_occurrence'] = list()
                    new_fail['segment'] = dict()
                    new_fail['element_criticality'] = list()
                    new_fail['damage_intensity_factor'] = list()
                    new_fail['day_flow'] = list()
                    new_fail['pipe_resilience_factor'] = list()
                    new_fail['failure_time_repair'] = None
                    new_fail['failure_class'] = None
                    new_fail['prioritization_factor'] = 0
                    duplicate_valves = list()
                    time_to_reduce = 0

                    for f in failures:
                        if f['pipe_id'] in new_fail['pipe_id']:
                            new_fail['failure_type'].append(f['failure_type'])
                            new_fail['pipe_diameter'].append(f['pipe_diameter'])
                            new_fail['historical_data'].append(f['historical_data'])
                            new_fail['failure_start'].append(f['failure_start'])
                            new_fail['type_of_substrate'].append(f['type_of_substrate'])
                            new_fail['place_of_occurrence'].append(f['place_of_occurrence'])
                            new_fail['segment'] = f['segment']
                            duplicate_valves = f['segment']['segment_valves']
                            new_fail['element_criticality'].append(f['element_criticality'])
                            new_fail['damage_intensity_factor'].append(f['damage_intensity_factor'])
                            new_fail['day_flow'].append(f['day_flow'])
                            new_fail['pipe_resilience_factor'].append(f['pipe_resilience_factor'])
                            repair_time.append(copy.deepcopy(f['failure_time_repair']))
                            classification.append(copy.deepcopy(f['failure_class']))

                            if f not in remove_list:
                                remove_list.append(f)

                    if 'C2' in classification:
                        new_fail['failure_class'] = 'C2'
                    else:
                        new_fail['failure_class'] = 'C3'

                    for valve in duplicate_valves:
                        for val in self.valves[self.init_config.valve_set]:
                            if valve == val['valve_id']:
                                # Diameter:
                                diameter = self.wn.get_link(val['data']['link_id']).todict()['diameter']
                                if diameter <= self.init_config.map_pipe_diameter['D3'][1]:
                                    diam_type = 'D3'
                                elif self.init_config.map_pipe_diameter['D2'][0] < diameter <= self.init_config.map_pipe_diameter['D2'][1]:
                                    diam_type = 'D2'
                                else:
                                    diam_type = 'D1'

                                time_to_reduce = time_to_reduce + random.randint(self.init_config.repair_times[diam_type]['open_valve'][0],
                                                                                 self.init_config.repair_times[diam_type]['open_valve'][1])
                                time_to_reduce = time_to_reduce + random.randint(self.init_config.repair_times[diam_type]['close_valve'][0],
                                                                                 self.init_config.repair_times[diam_type]['close_valve'][1])

                    total_repair_time = repair_time[0][1] + repair_time[1][1] - time_to_reduce
                    hours = total_repair_time // 60
                    minutes = total_repair_time % 60
                    time_string = "{} godz. {} min".format(int(hours), int(minutes))

                    new_fail['failure_time_repair'] = [time_string, total_repair_time]
                    failures.append(new_fail)

            for fail in self.aggregation_result[1]['aggregation_second_degree']:
                if fail['failures'][0][5:] and fail['failures'][1][5:] not in aggregated_pipes:
                    aggregated_pipes.append(fail['failures'][0][5:])
                    aggregated_pipes.append(fail['failures'][1][5:])
                    new_fail = dict()
                    repair_time = list()
                    classification = list()
                    segment_info = list()

                    new_fail['failure_id'] = 'AG_' + fail['failures'][0] + fail['failures'][1][4:]
                    new_fail['pipe_id'] = [fail['failures'][0][5:], fail['failures'][1][5:]]
                    new_fail['failure_type'] = list()
                    new_fail['pipe_diameter'] = list()
                    new_fail['historical_data'] = list()
                    new_fail['failure_start'] = list()
                    new_fail['type_of_substrate'] = list()
                    new_fail['place_of_occurrence'] = list()
                    new_fail['segment'] = dict()
                    new_fail['segment']['link_id'] = list()
                    new_fail['segment']['segment_links'] = list()
                    new_fail['segment']['segment_nodes'] = list()
                    new_fail['segment']['near_node_list'] = list()
                    new_fail['segment']['segment_valves'] = list()
                    new_fail['element_criticality'] = list()
                    new_fail['damage_intensity_factor'] = list()
                    new_fail['day_flow'] = list()
                    new_fail['pipe_resilience_factor'] = list()
                    new_fail['failure_time_repair'] = None
                    new_fail['failure_class'] = None
                    new_fail['prioritization_factor'] = 0

                    for f in failures:
                        if f['pipe_id'] in new_fail['pipe_id']:
                            new_fail['failure_type'].append(f['failure_type'])
                            new_fail['pipe_diameter'].append(f['pipe_diameter'])
                            new_fail['historical_data'].append(f['historical_data'])
                            new_fail['failure_start'].append(f['failure_start'])
                            new_fail['type_of_substrate'].append(f['type_of_substrate'])
                            new_fail['place_of_occurrence'].append(f['place_of_occurrence'])
                            new_fail['element_criticality'].append(f['element_criticality'])
                            new_fail['damage_intensity_factor'].append(f['damage_intensity_factor'])
                            new_fail['day_flow'].append(f['day_flow'])
                            new_fail['pipe_resilience_factor'].append(f['pipe_resilience_factor'])
                            repair_time.append(copy.deepcopy(f['failure_time_repair']))
                            classification.append(copy.deepcopy(f['failure_class']))
                            segment_info.append(copy.deepcopy(f['segment']))

                            if f not in remove_list:
                                remove_list.append(f)

                    duplicate_valves = list()
                    for seg in segment_info:
                        new_fail['segment']['link_id'].append(seg['link_id'])
                        for item in seg['segment_links']:
                            if item not in new_fail['segment']['segment_links']:
                                new_fail['segment']['segment_links'].append(item)
                        for item in seg['segment_nodes']:
                            if item not in new_fail['segment']['segment_nodes']:
                                new_fail['segment']['segment_nodes'].append(item)
                        for item in seg['near_node_list']:
                            if item not in new_fail['segment']['near_node_list']:
                                new_fail['segment']['near_node_list'].append(item)
                        for item in seg['segment_valves']:
                            if item not in new_fail['segment']['segment_valves']:
                                new_fail['segment']['segment_valves'].append(item)
                            else:
                                duplicate_valves.append(item)

                    if 'C2' in classification:
                        new_fail['failure_class'] = 'C2'
                    else:
                        new_fail['failure_class'] = 'C3'

                    time_to_reduce = 0

                    for valve in duplicate_valves:
                        for val in self.valves[self.init_config.valve_set]:
                            if valve == val['valve_id']:
                                # Diameter:
                                diameter = self.wn.get_link(val['data']['link_id']).todict()['diameter']
                                if diameter <= self.init_config.map_pipe_diameter['D3'][1]:
                                    diam_type = 'D3'
                                elif self.init_config.map_pipe_diameter['D2'][0] < diameter <= self.init_config.map_pipe_diameter['D2'][1]:
                                    diam_type = 'D2'
                                else:
                                    diam_type = 'D1'

                                time_to_reduce = time_to_reduce + random.randint(self.init_config.repair_times[diam_type]['open_valve'][0],
                                                                                 self.init_config.repair_times[diam_type]['open_valve'][1])
                                time_to_reduce = time_to_reduce + random.randint(self.init_config.repair_times[diam_type]['close_valve'][0],
                                                                                 self.init_config.repair_times[diam_type]['close_valve'][1])

                    total_repair_time = repair_time[0][1] + repair_time[1][1] - time_to_reduce
                    hours = total_repair_time // 60
                    minutes = total_repair_time % 60
                    time_string = "{} godz. {} min".format(int(hours), int(minutes))

                    new_fail['failure_time_repair'] = [time_string, total_repair_time]
                    failures.append(new_fail)

        for item in remove_list:
            failures.remove(item)

        for fail in failures:
            if fail['failure_id'][:3] == 'AG_':
                start_node_id = {'id': str(self.wn.get_node(self.wn.get_link(fail['pipe_id'][0]).todict()['start_node_name'])),
                                 'coordinates': [
                                     self.wn.get_node(self.wn.get_link(fail['pipe_id'][0]).todict()['start_node_name']).todict()['coordinates'][0],
                                     self.wn.get_node(self.wn.get_link(fail['pipe_id'][0]).todict()['start_node_name']).todict()['coordinates'][1]]}
            else:
                start_node_id = {'id': str(self.wn.get_node(self.wn.get_link(fail['pipe_id']).todict()['start_node_name'])),
                                 'coordinates': [
                                     self.wn.get_node(self.wn.get_link(fail['pipe_id']).todict()['start_node_name']).todict()['coordinates'][0],
                                     self.wn.get_node(self.wn.get_link(fail['pipe_id']).todict()['start_node_name']).todict()['coordinates'][1]]}

            if fail['failure_type'] == 'F1':
                valves_id = None
            else:
                valves_id = dict()
                for segment in self.segments['data']:
                    if fail['pipe_id'] in segment['segment_links']:
                        temp = list()
                        for valve in segment['segment_valves']:

                            for data in self.valves[self.init_config.valve_set]:
                                if valve == data['valve_id']:
                                    temp.append({'valve_id': valve, 'node_id': data['data']['node_id'], 'coordinates': data['data']['coordinates']})

                        valves_id['segment_id'] = {'segment_id': segment['segment_id'], 'valves': temp}

            if fail['prioritization_factor'] == 1:
                levels['L1'].append({'failure_id': fail['failure_id'],
                                     'failure_category': fail['failure_class'],
                                     'pipe_id': fail['pipe_id'],
                                     'start_node': start_node_id,
                                     'failure_type': fail['failure_type'],
                                     'valves_id': valves_id})

            elif fail['failure_class'] == 'C1':
                levels['L2'].append({'failure_id': fail['failure_id'],
                                     'failure_category': fail['failure_class'],
                                     'pipe_id': fail['pipe_id'],
                                     'start_node': start_node_id,
                                     'failure_type': fail['failure_type'],
                                     'valves_id': valves_id})

            elif fail['failure_class'] == 'C2':
                levels['L3'].append({'failure_id': fail['failure_id'],
                                     'failure_category': fail['failure_class'],
                                     'pipe_id': fail['pipe_id'],
                                     'start_node': start_node_id,
                                     'failure_type': fail['failure_type'],
                                     'valves_id': valves_id})
            else:
                levels['L4'].append({'failure_id': fail['failure_id'],
                                     'failure_category': fail['failure_class'],
                                     'pipe_id': fail['pipe_id'],
                                     'start_node': start_node_id,
                                     'failure_type': fail['failure_type'],
                                     'valves_id': valves_id})
        return levels

    def failure_repair_cost(self):
        levels = self.create_levels()
        total_cost = {'clamps': 0, 'pipes': 0, 'other_stuff': 0}

        for lev in levels:
            for fail in levels[lev]:
                if isinstance(fail['failure_type'], list):
                    clamps = 0
                    pipe = 0
                    other_stuff = 0
                    for kind in fail['failure_type']:
                        if kind == 'F1':
                            total_cost['clamps'] = total_cost['clamps'] + self.init_config.repair_cost['F1']['clamps']
                            total_cost['pipes'] = total_cost['pipes'] + self.init_config.repair_cost['F1']['pipes']
                            total_cost['other_stuff'] = total_cost['other_stuff'] + self.init_config.repair_cost['F1']['other_stuff']
                            clamps = clamps + self.init_config.repair_cost['F1']['clamps']
                            pipe = pipe + self.init_config.repair_cost['F1']['pipes']
                            other_stuff = other_stuff + self.init_config.repair_cost['F1']['other_stuff']
                            fail['repair_costs'] = {'clamps': clamps, 'pipes': pipe, 'other_stuff': other_stuff}
                        elif kind == 'F2':
                            total_cost['clamps'] = total_cost['clamps'] + self.init_config.repair_cost['F2']['clamps']
                            total_cost['pipes'] = total_cost['pipes'] + self.init_config.repair_cost['F2']['pipes']
                            total_cost['other_stuff'] = total_cost['other_stuff'] + self.init_config.repair_cost['F2']['other_stuff']
                            clamps = clamps + self.init_config.repair_cost['F2']['clamps']
                            pipe = pipe + self.init_config.repair_cost['F2']['pipes']
                            other_stuff = other_stuff + self.init_config.repair_cost['F2']['other_stuff']
                            fail['repair_costs'] = {'clamps': clamps, 'pipes': pipe, 'other_stuff': other_stuff}
                        else:
                            total_cost['clamps'] = total_cost['clamps'] + self.init_config.repair_cost['F3']['clamps']
                            total_cost['pipes'] = total_cost['pipes'] + self.init_config.repair_cost['F3']['pipes']
                            total_cost['other_stuff'] = total_cost['other_stuff'] + self.init_config.repair_cost['F3']['other_stuff']
                            clamps = clamps + self.init_config.repair_cost['F3']['clamps']
                            pipe = pipe + self.init_config.repair_cost['F3']['pipes']
                            other_stuff = other_stuff + self.init_config.repair_cost['F3']['other_stuff']
                            fail['repair_costs'] = {'clamps': clamps, 'pipes': pipe, 'other_stuff': other_stuff}
                else:
                    if fail['failure_type'] == 'F1':
                        total_cost['clamps'] = total_cost['clamps'] + self.init_config.repair_cost['F1']['clamps']
                        total_cost['pipes'] = total_cost['pipes'] + self.init_config.repair_cost['F1']['pipes']
                        total_cost['other_stuff'] = total_cost['other_stuff'] + self.init_config.repair_cost['F1']['other_stuff']
                        fail['repair_costs'] = {'clamps': self.init_config.repair_cost['F1']['clamps'], 'pipes': self.init_config.repair_cost['F1']['pipes'], 'other_stuff': self.init_config.repair_cost['F1']['other_stuff']}
                    elif fail['failure_type'] == 'F2':
                        total_cost['clamps'] = total_cost['clamps'] + self.init_config.repair_cost['F2']['clamps']
                        total_cost['pipes'] = total_cost['pipes'] + self.init_config.repair_cost['F2']['pipes']
                        total_cost['other_stuff'] = total_cost['other_stuff'] + self.init_config.repair_cost['F2']['other_stuff']
                        fail['repair_costs'] = {'clamps': self.init_config.repair_cost['F2']['clamps'], 'pipes': self.init_config.repair_cost['F2']['pipes'], 'other_stuff': self.init_config.repair_cost['F2']['other_stuff']}
                    else:
                        total_cost['clamps'] = total_cost['clamps'] + self.init_config.repair_cost['F3']['clamps']
                        total_cost['pipes'] = total_cost['pipes'] + self.init_config.repair_cost['F3']['pipes']
                        total_cost['other_stuff'] = total_cost['other_stuff'] + self.init_config.repair_cost['F3']['other_stuff']
                        fail['repair_costs'] = {'clamps': self.init_config.repair_cost['F3']['clamps'], 'pipes': self.init_config.repair_cost['F3']['pipes'], 'other_stuff': self.init_config.repair_cost['F3']['other_stuff']}

        return levels, total_cost

    def create_scenario(self):
        levels, total_cost = self.failure_repair_cost()

        critical_infrastructure = self.additional_info[self.init_config.additional_set]['critical_infrastructure_nodes']
        delivery_time = self.additional_info[self.init_config.additional_set]['delivery_time']
        suspended_time = self.additional_info[self.init_config.additional_set]['suspended_time']

        # for info in self.additional_info[self.init_config.additional_set]:
        #     if info == 'critical_infrastructure_nodes':
        #         critical_infrastructure.extend(self.additional_info[self.init_config.additional_set][info])
        #     if
        #
        #     print(self.additional_info[self.init_config.additional_set][info])


            print(info)



        # print(self.scenario_info)

        # print(self.additional_info)





    #
    # def task_scheduling_ver_a(self):
    #     levels = self.create_levels()
    #     for le in levels:
    #         print(le)
    #         for fail in levels[le]:
    #             print(fail['failure_id'], fail['repair_costs'])


# =============================================================================== Main
new_case = Algorithm_7()
# new_case.update_data()
# new_case.create_levels()
# new_case.failure_repair_cost()
new_case.create_scenario()

# new_case.task_scheduling_ver_a()

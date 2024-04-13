"""
          Name:     Algorithm 4 - Algorytm klasyfikacji awarii
        Author:     Ariel Antonowicz
   Last update:     23.03.2022
"""
import numpy as np
import random
from algorithms.algorithm_1.algorithm_1 import *
from algorithms.algorithm_3.algorithm_3 import *


class Algorithm_4:
    def __init__(self):
        self.init_config = Configuration_data()
        self.inp_file = self.init_config.networks_path + self.init_config.inp_file_name + '.inp'

        self.wn = wntr.network.WaterNetworkModel(self.inp_file)
        self.wn.options.time.duration = self.init_config.sim_duration
        self.sim = wntr.sim.EpanetSimulator(wn=self.wn)

        self.classification_results = list()

        self.failures_times = self.init_config.repair_times
        self.failures_types = self.init_config.failure_type
        self.failures_info = self.init_config.failures_path + self.init_config.failures_info + '.json'
        with open(self.failures_info, "r") as jsonFile:
            self.failures = json.load(jsonFile)

    def __del__(self):
        for filename in glob.glob("temp*"):
            os.remove(filename)

    def update_data(self):

        if self.failures[self.init_config.failures_set]['status'] == 'NoUpdated':
            # Element critical factor:
            links_result = Algorithm_1().network_resilience_algorithm()

            for fail in self.failures[self.init_config.failures_set]['data']:
                # Diameter:
                diameter = self.wn.get_link(fail['pipe_id']).todict()['diameter']
                if diameter <= self.init_config.map_pipe_diameter['D3'][1]:
                    diam_type = 'D3'
                elif self.init_config.map_pipe_diameter['D2'][0] < diameter <= self.init_config.map_pipe_diameter['D2'][1]:
                    diam_type = 'D2'
                else:
                    diam_type = 'D1'
                fail['pipe_diameter'] = {'diameter_m': diameter,'diameter_in': round(diameter * 39.37), 'type': diam_type}

                # Type of substrate:
                if not fail['type_of_substrate']:
                    fail['type_of_substrate'] = ['paving_slabs', 'asphalt']

                # Historical data:
                if not fail['historical_data']:
                    fail['historical_data'] = {'number_of_failure': random.randint(self.init_config.historical_data_random[0], self.init_config.historical_data_random[1]),
                                               'years': random.randint(self.init_config.historical_data_random[0], self.init_config.historical_data_random[1])}
                # Place occurrence:
                if not fail['place_of_occurrence']:
                    fail['place_of_occurrence'] = 'public'

                # Segment:
                fail['segment'] = Algorithm_3().find_segment(fail['pipe_id'])

                # Element critical factor:
                for link in links_result['links']:
                    for case in links_result['links'][link]:
                        if case['remove_element_id'] == fail['pipe_id']:
                            fail['element_criticality'] = [case['percent'], case['category']]
                            break
            # Update info:
            self.failures[self.init_config.failures_set]['status'] = 'Updated'

            with open(self.failures_info, "w") as jsonFile:
                json.dump(self.failures, jsonFile)

    def damage_intensity_factor(self, fail):                                           # Wskaźnik intesywności uszkodzeń (lambda)
        self.wn = wntr.network.WaterNetworkModel(self.inp_file)
        self.wn.options.time.duration = self.init_config.sim_duration
        self.sim = wntr.sim.EpanetSimulator(wn=self.wn)
        total_length = 0
        pipe_length = 0

        for pipe in self.wn.link_name_list:
            if self.wn.links[pipe].todict()['link_type'] == 'Pipe':
                total_length = total_length + self.wn.links[pipe].todict()['length']
            if self.wn.links[pipe].todict()['name'] == fail['pipe_id']:
                pipe_length = self.wn.links[pipe].todict()['length']

        fail['damage_intensity_factor'] = round(fail['historical_data']['number_of_failure'] / (pipe_length * fail['historical_data']['years']), 4)
        return fail

    def day_flow(self, fail, sim_time=24):
        sum_of_flow = 0
        pipe_flow = 0
        flow_result = list()

        self.wn = wntr.network.WaterNetworkModel(self.inp_file)
        self.wn.options.time.duration = self.init_config.sim_duration
        self.sim = wntr.sim.EpanetSimulator(wn=self.wn)

        for step in range(0, sim_time + 1, 1):
            self.wn.options.time.duration = step * 3600
            simulation_results = self.sim.run_sim()
            flow_result.append(simulation_results.link['flowrate'].to_dict('index'))

        for step in range(0, len(flow_result), 1):

            for key in flow_result[step][step*3600]:
                flow_result[step][step * 3600][key] = round(flow_result[step][step*3600][key] * 15.85, 2)
                sum_of_flow = sum_of_flow + flow_result[step][step * 3600][key]

                if key == fail['pipe_id']:
                    pipe_flow = pipe_flow + flow_result[step][step * 3600][key]

        fail['day_flow'] = round((round(pipe_flow, 2) * 100) / round(sum_of_flow, 2), 4)
        return fail

    def pipe_resilience_factor(self, fail, sim_time=24):
        self.wn = wntr.network.WaterNetworkModel(self.inp_file)
        self.wn.options.time.duration = self.init_config.sim_duration
        self.sim = wntr.sim.EpanetSimulator(wn=self.wn)

        benchmark_pressure = list()
        benchmark_flow = list()
        benchmark_demand = list()
        benchmark_nodes_without_demand = list()
        benchmark_node_pressure_bellow_5 = list()
        bench_sum_of_flow = 0

        sim_pressure = list()
        sim_flow = list()
        sim_demand = list()
        sim_nodes_without_demand = list()
        sim_node_pressure_bellow_5 = list()
        sim_sum_of_flow = 0

        demand_result = list()
        pressure_result = list()

        for step in range(0, sim_time + 1, 1):
            self.wn.options.time.duration = step * 3600
            simulation_results = self.sim.run_sim()

            benchmark_flow.append(simulation_results.link['flowrate'].to_dict('index'))
            benchmark_demand.append(simulation_results.node['demand'].to_dict('index'))
            benchmark_pressure.append(simulation_results.node['pressure'].to_dict('index'))

            dem = 0
            pre = 0

            for node in self.wn.node_name_list:
                # print(benchmark_demand[-1][step*3600][node])
                # print(benchmark_pressure[-1][step * 3600][node])
                if benchmark_demand[-1][step*3600][node] <= 0.0:
                    dem = dem + 1
                if benchmark_pressure[-1][step*3600][node] <= 5.0:
                    pre = pre + 1
            benchmark_nodes_without_demand.append(dem)
            benchmark_node_pressure_bellow_5.append(pre)

        for step in range(0, len(benchmark_flow), 1):

            for key in benchmark_flow[step][step*3600]:
                benchmark_flow[step][step * 3600][key] = round(benchmark_flow[step][step*3600][key] * 15.85, 2)
                bench_sum_of_flow = bench_sum_of_flow + benchmark_flow[step][step * 3600][key]

        self.wn = wntr.network.WaterNetworkModel(self.inp_file)
        self.wn.options.time.duration = self.init_config.sim_duration
        self.sim = wntr.sim.EpanetSimulator(wn=self.wn)

        act = controls.ControlAction(self.wn.get_link(fail['pipe_id']), 'status', 0)
        cond = controls.SimTimeCondition(self.wn, controls.Comparison.ge, '00:00:00')
        ctr1 = controls.Control(cond, act)
        self.wn.add_control('control' + str(fail['pipe_id']), ctr1)

        for step in range(0, sim_time + 1, 1):
            self.wn.options.time.duration = step * 3600
            simulation_results = self.sim.run_sim()

            sim_flow.append(simulation_results.link['flowrate'].to_dict('index'))
            sim_demand.append(simulation_results.node['demand'].to_dict('index'))
            sim_pressure.append(simulation_results.node['pressure'].to_dict('index'))

            dem = 0
            pre = 0

            for node in self.wn.node_name_list:
                if sim_demand[-1][step*3600][node] <= 0.0:
                    dem = dem + 1
                if sim_pressure[-1][step*3600][node] <= 5.0:
                    pre = pre + 1
            sim_nodes_without_demand.append(dem)
            sim_node_pressure_bellow_5.append(pre)

        for x in range(0, len(benchmark_nodes_without_demand), 1):
            demand_result.append(benchmark_nodes_without_demand[x] - sim_nodes_without_demand[x])
            pressure_result.append(benchmark_node_pressure_bellow_5[x] - sim_node_pressure_bellow_5[x])

        for step in range(0, len(sim_flow), 1):

            for key in sim_flow[step][step*3600]:
                sim_flow[step][step * 3600][key] = round(sim_flow[step][step*3600][key] * 15.85, 2)
                sim_sum_of_flow = sim_sum_of_flow + sim_flow[step][step * 3600][key]

        # print(f'Benchmark demand: {benchmark_nodes_without_demand}')
        # print(f'Sim demand      : {sim_nodes_without_demand}')
        # print(f'Result          : {demand_result}')
        # print(f'==========================================')
        # print(f'Benchmark pressure: {benchmark_node_pressure_bellow_5}')
        # print(f'Sim pressure      : {sim_node_pressure_bellow_5}')
        # print(f'Result            : {pressure_result}')
        # print(f'==========================================')
        # print(f'Benchmark flow    : {round(bench_sum_of_flow, 2)}')
        # print(f'Sim flow          : {round(sim_sum_of_flow, 2)}')
        # print(f'Result            : {round(bench_sum_of_flow - sim_sum_of_flow, 2)}')

        diameter = round(self.wn.links[self.wn.get_link(fail['pipe_id'])].todict()['diameter'] * 39.73, 2)      # m to in
        flow_drop = round(bench_sum_of_flow - sim_sum_of_flow, 2)

        c_j = round((diameter + (sum(demand_result)/24 * -0.5) + (sum(pressure_result)/24 * -0.25) + flow_drop) / len(self.wn.pipe_name_list), 3)
        fail['pipe_resilience_factor'] = c_j
        return fail

    def todini_resilience_index(self):
        wn = wntr.network.WaterNetworkModel(self.inp_file)
        wn.options.hydraulic.demand_model = 'PDD'
        sim = wntr.sim.WNTRSimulator(wn=self.wn)
        results = sim.run_sim()

        pressure = results.node['pressure']
        threshold = 21.09  # 30 psi
        pressure_above_threshold = wntr.metrics.query(pressure, np.greater, threshold)
        expected_demand = wntr.metrics.expected_demand(wn)
        demand = results.node['demand']
        wsa = wntr.metrics.water_service_availability(expected_demand, demand)
        head = results.node['head']
        pump_flowrate = results.link['flowrate'].loc[:, wn.pump_name_list]
        todini = wntr.metrics.todini_index(head, pressure, demand, pump_flowrate, wn, threshold)
        return todini

    def failure_time_repair(self, fail):
        t_factor = 0

        if fail['place_of_occurrence'] == 'private':
            t_factor = t_factor + 60

        for element in self.failures_types[fail['failure_type']]:
            needed_time = 0

            if element == 'open_valve' or element == 'close_valve':
                needed_time = len(fail['segment']['segment_valves']) * random.randint(self.failures_times[fail['pipe_diameter']['type']][element][0],
                                                                                      self.failures_times[fail['pipe_diameter']['type']][element][1])
                t_factor = t_factor + needed_time

            elif (element == 'asphalt_extraction') and ('asphalt' not in fail['type_of_substrate']):
                pass
            elif (element == 'paving_slabs') and ('paving_slabs' not in fail['type_of_substrate']):
                pass
            else:
                needed_time = random.randint(self.failures_times[fail['pipe_diameter']['type']][element][0],
                                             self.failures_times[fail['pipe_diameter']['type']][element][1])
                t_factor = t_factor + needed_time

        hours = t_factor // 60
        minutes = t_factor % 60
        time_string = "{} godz. {} min".format(int(hours), int(minutes))

        fail['failure_time_repair'] = [time_string, t_factor]
        return fail

    def get_classify(self):
        # self.todini_resilience_index()
        with open(self.failures_info, "r") as jsonFile:
            self.failures = json.load(jsonFile)

        for fail in self.failures[self.init_config.failures_set]['data']:
            self.failure_time_repair(fail)
            self.damage_intensity_factor(fail)
            self.day_flow(fail)
            self.pipe_resilience_factor(fail)

            class_c1_sum = 0
            class_c2_sum = 0

            if fail['element_criticality'][1] == 'CAT-3' or fail['element_criticality'][1] == 'CAT-4':
                class_c1_sum = class_c1_sum + 1
            if fail['element_criticality'][0] >= 15.0:
                class_c1_sum = class_c1_sum + 1
            if fail['pipe_resilience_factor'] >= 1.0:
                class_c1_sum = class_c1_sum + 1
            if fail['failure_time_repair'][1] >= 15*60:
                class_c1_sum = class_c1_sum + 1
            if fail['element_criticality'][1] == 'CAT-3' or fail['element_criticality'][1] == 'CAT-4' or fail['element_criticality'][1] == 'CAT-2':
                class_c2_sum = class_c2_sum + 1
            if fail['element_criticality'][0] >= 10.0:
                class_c2_sum = class_c2_sum + 1
            if fail['pipe_resilience_factor'] >= 0.7:
                class_c2_sum = class_c2_sum + 1
            if fail['failure_time_repair'][1] >= 8.5*60:
                class_c2_sum = class_c2_sum + 1

            if class_c1_sum >= 2:
                fail['failure_class'] = 'C1'
            elif class_c2_sum >= 2:
                fail['failure_class'] = 'C2'
            else:
                fail['failure_class'] = 'C3'

        with open(self.failures_info, "w") as jsonFile:
            json.dump(self.failures, jsonFile)
        return True


# =============================================================================== Main
# new_case = Algorithm_4()
# new_case.update_data()
# new_case.get_classify()

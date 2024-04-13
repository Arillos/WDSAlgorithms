"""
          Name:     Algorithm 1 - Klasyfikacja elementów sieci wodociągowej
        Author:     Ariel Antonowicz
   Last update:     24.02.2022
"""
import wntr
import copy
import pandas as pd
import os, glob
from config import Configuration_data


class Algorithm_1:

    def __init__(self):

        self.init_config = Configuration_data()

        self.inp_file = self.init_config.networks_path + self.init_config.inp_file_name + '.inp'
        self.nodes_csv_file = self.init_config.results_path + self.init_config.nodes_csv_file + '.csv'
        self.links_csv_file = self.init_config.results_path + self.init_config.links_csv_file + '.csv'

        self.link_file = open(file=self.links_csv_file, newline='', mode='a')
        self.node_file = open(file=self.nodes_csv_file, newline='', mode='a')

        self.sum_of_flow = 0
        self.sum_of_pressure = 0
        self.sum_of_demand = 0
        self.sum_of_head = 0
        self.links_results = {'flow': list()}
        self.nodes_results = {'head': list(), 'demand': list(), 'pressure': list()}
        self.isolated_nodes_list = list()

        self.wn = wntr.network.WaterNetworkModel(self.inp_file)
        self.wn.options.time.duration = self.init_config.sim_duration
        self.sim = wntr.sim.EpanetSimulator(wn=self.wn)

    def __del__(self):
        for filename in glob.glob("temp*"):
            os.remove(filename)

    def run_simulation(self, wn):
        simulation_results = list()

        sim = wntr.sim.EpanetSimulator(wn=wn)
        for step in range(0, self.init_config.sim_duration + 1, 1):
            wn.options.time.duration = step * 3600
            simulation_results = sim.run_sim()

        return {'flow': simulation_results.link['flowrate'].to_dict('index'),
                'head': simulation_results.node['head'].to_dict('index'),
                'demand': simulation_results.node['demand'].to_dict('index'),
                'pressure': simulation_results.node['pressure'].to_dict('index')}

    def create_new_topology(self, element_type, element_id):
        wn = wntr.network.WaterNetworkModel(self.inp_file)

        if element_type == 'node':
            # Search Pipe ID where element is start or end node.
            for link in wn.link_name_list:
                if element_id == str(wn.get_link(link).todict()['start_node']):
                    # Copy info about NODE and LINK
                    node_temp_info = copy.deepcopy(wn.get_node(element_id).todict())  # Save info about node
                    link_temp_info = copy.deepcopy(wn.get_link(link).todict())  # Save info about link
                    wn.remove_link(wn.get_link(link).todict()['name'])  # Remove link
                    wn.remove_node(element_id)  # Remove analyzed element

                    # Create new node and link base on temp_info
                    wn.add_junction(name=element_id,
                                    base_demand=0,
                                    elevation=wn.get_node(link_temp_info['end_node']).todict()['elevation'],
                                    coordinates=node_temp_info['coordinates'])

                    wn.add_pipe(name=link_temp_info['name'],  # Create new pipe
                                start_node_name=element_id,
                                end_node_name=link_temp_info['end_node_name'])
                    break

                elif element_id == str(wn.get_link(link).todict()['end_node']):
                    # Copy info about NODE and LINK
                    node_temp_info = copy.deepcopy(wn.get_node(element_id).todict())  # Save info about node
                    link_temp_info = copy.deepcopy(wn.get_link(link).todict())  # Save info about link
                    wn.remove_link(wn.get_link(link).todict()['name'])  # Remove link
                    wn.remove_node(element_id)  # Remove analyzed element

                    # Create new temporary junction
                    wn.add_junction(name=element_id,
                                    base_demand=0,
                                    elevation=wn.get_node(link_temp_info['start_node']).todict()['elevation'],
                                    coordinates=node_temp_info['coordinates'])

                    wn.add_pipe(name=link_temp_info['name'],  # Create new pipe
                                start_node_name=link_temp_info['start_node_name'],
                                end_node_name=element_id)
                    break
        elif element_type == 'link':
            pump_temp_info = copy.deepcopy(wn.get_link(element_id).todict())
            wn.remove_link(element_id)
            wn.add_pipe(name=pump_temp_info['name'],  # Create temporary pipe base on Pump/Valve info
                        start_node_name=pump_temp_info['start_node_name'],
                        end_node_name=pump_temp_info['end_node_name'])

        elif element_type == 'pipe':
            not_isolated_node_list = list()

            # Check that remove pipe creates isolated junction
            wn.remove_link(element_id)  # Remove analyzed element

            for link in wn.link_name_list:
                not_isolated_node_list.append(wn.get_link(link).todict()['start_node_name']) if wn.get_link(link).todict()['start_node_name'] not in not_isolated_node_list else not_isolated_node_list
                not_isolated_node_list.append(wn.get_link(link).todict()['end_node_name']) if wn.get_link(link).todict()['end_node_name'] not in not_isolated_node_list else not_isolated_node_list

            self.isolated_nodes_list = list(set(not_isolated_node_list).symmetric_difference(set(wn.node_name_list)))       # Create unique list (isolated nodes)

            # Remove isolated nodes
            for x in self.isolated_nodes_list:
                wn.remove_node(x)

        return wn

    def reference_simulation(self):
        # Create reference result list
        # print(f'Start reference simulation for: {self.inp_file}')
        wn = wntr.network.WaterNetworkModel(self.inp_file)
        sim_result = self.run_simulation(wn)

        reference_simulation_result = {
            'ID': 'Reference sim',
            'isolated_nodes_id': [],
            'flow': sim_result['flow'],
            'head': sim_result['head'],
            'demand': sim_result['demand'],
            'pressure': sim_result['pressure']}

        return reference_simulation_result

    def reservoir_resilience_simulation(self, list_to_test=None):
        if not list_to_test:
            list_to_check = list(self.wn.nodes.reservoir_names)
        else:
            list_to_check = list_to_test

        reservoir_resilience_simulation_result = list()
        for element in list_to_check:
            wn = self.create_new_topology('node', element)
            sim_result = self.run_simulation(wn)

            use_case = {
                'ID': element,
                'type': 'reservoir',
                'flow': sim_result['flow'],
                'head': sim_result['head'],
                'demand': sim_result['demand'],
                'pressure': sim_result['pressure'],
                'isolated_nodes_id': []
            }
            reservoir_resilience_simulation_result.append(use_case)
        return reservoir_resilience_simulation_result

    def tank_resilience_simulation(self, list_to_test=None):
        if not list_to_test:
            list_to_check = list(self.wn.nodes.tank_names)
        else:
            list_to_check = list_to_test

        tank_resilience_simulation_result = list()
        for element in list_to_check:
            wn = self.create_new_topology('node', element)
            sim_result = self.run_simulation(wn)

            use_case = {
                'ID': element,
                'type': 'tank',
                'flow': sim_result['flow'],
                'head': sim_result['head'],
                'demand': sim_result['demand'],
                'pressure': sim_result['pressure'],
                'isolated_nodes_id': []
            }
            tank_resilience_simulation_result.append(use_case)
        return tank_resilience_simulation_result

    def pump_resilience_simulation(self, list_to_test=None):
        if not list_to_test:
            list_to_check = list(self.wn.links.pump_names)
        else:
            list_to_check = list_to_test

        pump_resilience_simulation_result = list()
        for element in list_to_check:
            wn = self.create_new_topology('link', element)
            sim_result = self.run_simulation(wn)

            use_case = {
                'ID': element,
                'type': 'pump',
                'flow': sim_result['flow'],
                'head': sim_result['head'],
                'demand': sim_result['demand'],
                'pressure': sim_result['pressure'],
                'isolated_nodes_id': []
            }
            pump_resilience_simulation_result.append(use_case)
        return pump_resilience_simulation_result

    def valve_resilience_simulation(self, list_to_test=None):
        if not list_to_test:
            list_to_check = list(self.wn.links.valve_names)
        else:
            list_to_check = list_to_test

        valve_resilience_simulation_result = list()
        for element in list_to_check:
            wn = self.create_new_topology('link', element)
            sim_result = self.run_simulation(wn)

            use_case = {
                'ID': element,
                'type': 'valve',
                'flow': sim_result['flow'],
                'head': sim_result['head'],
                'demand': sim_result['demand'],
                'pressure': sim_result['pressure'],
                'isolated_nodes_id': []
            }
            valve_resilience_simulation_result.append(use_case)
        return valve_resilience_simulation_result

    def pipe_resilience_simulation(self, list_to_test=None):
        if not list_to_test:
            list_to_check = list(self.wn.links.pipe_names)
        else:
            list_to_check = list_to_test
        pipe_resilience_simulation_result = list()
        for element in list_to_check:
            wn = self.create_new_topology('pipe', element)
            sim_result = self.run_simulation(wn)

            use_case = {
                'ID': element,
                'type': 'pipe',
                'flow': sim_result['flow'],
                'head': sim_result['head'],
                'demand': sim_result['demand'],
                'pressure': sim_result['pressure'],
                'isolated_nodes_id': self.isolated_nodes_list
            }
            pipe_resilience_simulation_result.append(use_case)
        return pipe_resilience_simulation_result

    def create_data_frame_for_links(self, data_type, data):
        flow_data = dict()

        self.wn = wntr.network.WaterNetworkModel(self.inp_file)

        for link_id in self.wn.link_name_list:
            flow_data[link_id] = 0

        if data_type == 'reference_simulation':
            for sim_step in data['flow']:
                for link_id in data['flow'][sim_step]:
                    flow_data[link_id] = flow_data[link_id] + data['flow'][sim_step][link_id]

            for element in flow_data.values():
                self.sum_of_flow = self.sum_of_flow + element
            flow_data['sum'] = self.sum_of_flow
            flow_data['percent'] = 100
            flow_data['category'] = 'CAT-1'
            flow_df = pd.DataFrame(flow_data, index=['Flow (ref_sim)'])
            flow_df.to_csv(self.link_file, index=True, header=True)

        elif data_type == 'resilience_simulation':
            index = list()
            temp_list = list()
            for case in data:

                flow_data.clear()
                for link_id in self.wn.link_name_list:
                    flow_data[link_id] = 0
                index.append('Flow (' + str(case['ID']) + ')')
                for sim_step in case['flow']:
                    for link_id in case['flow'][sim_step]:
                        flow_data[link_id] = flow_data[link_id] + case['flow'][sim_step][link_id]
                total_sum = 0
                for element in flow_data.values():
                    total_sum = total_sum + element
                flow_data['sum'] = total_sum
                flow_data['percent'] = round((total_sum * 100)/self.sum_of_flow , 2)

                flow_data['remove_element_id'] = case['ID']
                flow_data['element_type'] = case['type']

                for category in self.init_config.flow_category:
                    if self.init_config.flow_category[category][0] <= flow_data['percent'] <= self.init_config.flow_category[category][1]:
                        flow_data['category'] = category
                        break
                temp_list.append(copy.deepcopy(flow_data))

                self.links_results['flow'].append(copy.deepcopy(flow_data))

            flow_df = pd.DataFrame(temp_list, index=index)
            flow_df.to_csv(self.link_file, index=True, header=False)

        return self.links_results

    def create_data_frame_for_nodes(self, data_type, data):
        head_data = dict()
        demand_data = dict()
        pressure_data = dict()

        self.wn = wntr.network.WaterNetworkModel(self.inp_file)

        for node_id in self.wn.node_name_list:
            head_data[node_id] = 0
            demand_data[node_id] = 0
            pressure_data[node_id] = 0

        if data_type == 'reference_simulation':
            for sim_step in data['head']:
                for node_id in data['head'][sim_step]:
                    head_data[node_id] = head_data[node_id] + data['head'][sim_step][node_id]
            for sim_step in data['demand']:
                for node_id in data['demand'][sim_step]:
                    demand_data[node_id] = demand_data[node_id] + data['demand'][sim_step][node_id]
            for sim_step in data['pressure']:
                for node_id in data['pressure'][sim_step]:
                    pressure_data[node_id] = pressure_data[node_id] + data['pressure'][sim_step][node_id]

            for element in head_data.values():
                self.sum_of_head = self.sum_of_head + element
            head_data['sum'] = self.sum_of_head
            head_data['percent'] = 100
            head_data['category'] = 'CAT-1'

            for element in demand_data.values():
                self.sum_of_demand = self.sum_of_demand + element
            demand_data['sum'] = self.sum_of_demand
            demand_data['percent'] = 100
            demand_data['category'] = 'CAT-1'

            for element in pressure_data.values():
                self.sum_of_pressure = self.sum_of_pressure + element
            pressure_data['sum'] = self.sum_of_pressure
            pressure_data['percent'] = 100
            pressure_data['category'] = 'CAT-1'

            head_df = pd.DataFrame(head_data, index=['Head (ref_sim)'])
            demand_df = pd.DataFrame(demand_data, index=['Demand (ref_sim)'])
            pressure_df = pd.DataFrame(pressure_data, index=['Pressure (ref_sim)'])
            head_df.to_csv(self.node_file, index=True, header=True)
            demand_df.to_csv(self.node_file, index=True, header=False)
            pressure_df.to_csv(self.node_file, index=True, header=False)

        elif data_type == 'resilience_simulation':
            head_index = list()
            demand_index = list()
            pressure_index = list()
            head_temp_list = list()
            demand_temp_list = list()
            pressure_temp_list = list()

            for case in data:
                head_data.clear()
                demand_data.clear()
                pressure_data.clear()
                head_index.append('Head (' + str(case['ID']) + ')')
                demand_index.append('Demand (' + str(case['ID']) + ')')
                pressure_index.append('Pressure (' + str(case['ID']) + ')')

                for node_id in self.wn.node_name_list:
                    head_data[node_id] = 0
                    demand_data[node_id] = 0
                    pressure_data[node_id] = 0

                for sim_step in case['head']:
                    for node_id in case['head'][sim_step]:
                        head_data[node_id] = head_data[node_id] + case['head'][sim_step][node_id]
                total_sum = 0
                for element in head_data.values():

                    total_sum = total_sum + element
                head_data['sum'] = total_sum
                head_data['percent'] = round((total_sum * 100) / self.sum_of_head, 2)

                for category in self.init_config.head_category:
                    if self.init_config.head_category[category][0] <= head_data['percent'] <= self.init_config.head_category[category][1]:
                        head_data['category'] = category
                        break
                head_temp_list.append(copy.deepcopy(head_data))
                head_data['remove_element_id'] = case['ID']
                head_data['element_type'] = case['type']
                self.nodes_results['head'].append(copy.deepcopy(head_data))

                for sim_step in case['demand']:
                    for node_id in case['demand'][sim_step]:
                        demand_data[node_id] = demand_data[node_id] + case['demand'][sim_step][node_id]
                total_sum = 0
                for element in demand_data.values():
                    total_sum = total_sum + element
                demand_data['sum'] = total_sum
                demand_data['percent'] = round((total_sum * 100) / self.sum_of_demand, 2)

                for category in self.init_config.demand_category:
                    if self.init_config.demand_category[category][0] <= demand_data['percent'] <= self.init_config.demand_category[category][1]:
                        demand_data['category'] = category
                        break
                demand_temp_list.append(copy.deepcopy(demand_data))
                demand_data['remove_element_id'] = case['ID']
                demand_data['element_type'] = case['type']
                self.nodes_results['demand'].append(copy.deepcopy(demand_data))

                for sim_step in case['pressure']:
                    for node_id in case['pressure'][sim_step]:
                        pressure_data[node_id] = pressure_data[node_id] + case['pressure'][sim_step][node_id]

                total_sum = 0
                for element in pressure_data.values():
                    total_sum = total_sum + element
                pressure_data['sum'] = total_sum
                pressure_data['percent'] = round((total_sum * 100) / self.sum_of_pressure, 2)

                for category in self.init_config.pressure_category:
                    if self.init_config.pressure_category[category][0] <= pressure_data['percent'] <= self.init_config.pressure_category[category][1]:
                        pressure_data['category'] = category
                        break
                pressure_temp_list.append(copy.deepcopy(pressure_data))
                pressure_data['remove_element_id'] = case['ID']
                pressure_data['element_type'] = case['type']
                self.nodes_results['pressure'].append(copy.deepcopy(pressure_data))

            head_df = pd.DataFrame(head_temp_list, index=head_index)
            demand_df = pd.DataFrame(demand_temp_list, index=demand_index)
            pressure_df = pd.DataFrame(pressure_temp_list, index=pressure_index)
            head_df.to_csv(self.node_file, index=True, header=False)
            demand_df.to_csv(self.node_file, index=True, header=False)
            pressure_df.to_csv(self.node_file, index=True, header=False)

        return self.nodes_results

    def network_resilience_algorithm(self):
        ref_sim = self.reference_simulation()
        res_sim = self.reservoir_resilience_simulation()
        tan_sim = self.tank_resilience_simulation()
        pum_sim = self.pump_resilience_simulation()
        val_sim = self.valve_resilience_simulation()
        pip_sim = self.pipe_resilience_simulation()

        self.create_data_frame_for_links('reference_simulation', ref_sim)
        self.create_data_frame_for_nodes('reference_simulation', ref_sim)
        self.create_data_frame_for_links('resilience_simulation', res_sim)
        self.create_data_frame_for_nodes('resilience_simulation', res_sim)
        self.create_data_frame_for_links('resilience_simulation', tan_sim)
        self.create_data_frame_for_nodes('resilience_simulation', tan_sim)
        self.create_data_frame_for_links('resilience_simulation', pum_sim)
        self.create_data_frame_for_nodes('resilience_simulation', pum_sim)
        self.create_data_frame_for_links('resilience_simulation', val_sim)
        self.create_data_frame_for_nodes('resilience_simulation', val_sim)
        self.create_data_frame_for_links('resilience_simulation', pip_sim)
        self.create_data_frame_for_nodes('resilience_simulation', pip_sim)

        return {'links': self.links_results, 'nodes': self.nodes_results}


# =============================================================================== Main
# new_case = Algorithm_1()
# x = new_case.network_resilience_algorithm()

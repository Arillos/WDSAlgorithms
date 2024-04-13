"""
          Name:     Algorithm 5 - Algorytm priorytetyzacji
        Author:     Ariel Antonowicz
   Last update:     24.03.2022
"""
from algorithms.algorithm_2.algorithm_2 import *
from algorithms.algorithm_4.algorithm_4 import *


class Algorithm_5:
    def __init__(self):
        self.init_config = Configuration_data()
        self.inp_file = self.init_config.networks_path + self.init_config.inp_file_name + '.inp'

        self.wn = wntr.network.WaterNetworkModel(self.inp_file)
        self.wn.options.time.duration = self.init_config.sim_duration
        self.sim = wntr.sim.EpanetSimulator(wn=self.wn)

        self.failures_info = self.init_config.failures_path + self.init_config.failures_info + '.json'
        self.additional_info = self.init_config.additional_data_path + self.init_config.additional_info + '.json'
        with open(self.additional_info, "r") as jsonFile:
            self.additional_info = json.load(jsonFile)

        self.failures = None
        self.trace = Algorithm_2()
        self.classification = Algorithm_4()

    def __del__(self):
        for filename in glob.glob("temp*"):
            os.remove(filename)

    def update_data(self):
        self.classification.update_data()
        self.classification.get_classify()

        with open(self.failures_info, "r") as jsonFile:
            self.failures = json.load(jsonFile)

        for fail in self.failures[self.init_config.failures_set]['data']:
            if fail['failure_type'] == 'F1':
                fail['prioritization_factor'] = 0

        return copy.deepcopy(self.failures)

    def get_failures_id_to_check(self):
        failure_to_check = list()

        for link in self.additional_info[self.init_config.additional_set]['critical_infrastructure_nodes']:
            links = self.trace.critical_pipes(link)
            for pipe in links:
                for fail in self.failures[self.init_config.failures_set]['data']:
                    if pipe == fail['pipe_id'] and fail['failure_type'] != 'F1':
                        failure_to_check.append({'critical_node_id': link, 'failure_id':fail['failure_id'], 'pipe_id': fail['pipe_id']})

        return copy.deepcopy(failure_to_check)

    def prioritization(self):
        reference_demand = dict()
        resilience_demand = dict()
        resilience_result = list()
        failures = list()
        failure_use_cases = list()

        temp = self.get_failures_id_to_check()
        temp2 = list()
        for item in temp:
            if item['pipe_id'] not in failures:
                failures.append(item['pipe_id'])

        for n in range(1, len(failures) + 1):
            temp2.append(list(set(list(itertools.combinations(failures, n)))))

        for i in range(0, len(temp2)):
            for j in range(0, len(temp2[i])):
                temp2[i][j] = list(temp2[i][j])
            failure_use_cases.extend(temp2[i])

        # Reference simulation:
        for node in self.additional_info[self.init_config.additional_set]['critical_infrastructure_nodes']:
            reference_demand[node] = 0

            self.wn = wntr.network.WaterNetworkModel(self.inp_file)
            self.wn.options.time.duration = self.init_config.sim_duration
            self.sim = wntr.sim.EpanetSimulator(wn=self.wn)

            for step in range(0, self.init_config.sim_duration + 1, 1):
                self.wn.options.time.duration = step * 3600
                simulation_results = self.sim.run_sim()
                reference_demand[node] = reference_demand[node] + simulation_results.node['demand'].to_dict('index')[step*3600][node]

        # Resilience simulation
        for fail in failure_use_cases:

            for node in self.additional_info[self.init_config.additional_set]['critical_infrastructure_nodes']:
                resilience_demand[node] = {'failure_case': fail, 'total_demand': 0}

            self.wn = wntr.network.WaterNetworkModel(self.inp_file)
            self.wn.options.time.duration = self.init_config.sim_duration
            self.sim = wntr.sim.EpanetSimulator(wn=self.wn)

            for item in fail:
                act = controls.ControlAction(self.wn.get_link(item), 'status', 0)
                cond = controls.SimTimeCondition(self.wn, controls.Comparison.ge, '00:00:00')
                ctr1 = controls.Control(cond, act)
                self.wn.add_control('control' + str(item), ctr1)

            for step in range(0, self.init_config.sim_duration + 1, 1):
                self.wn.options.time.duration = step * 3600
                simulation_results = self.sim.run_sim()
                for node in self.additional_info[self.init_config.additional_set]['critical_infrastructure_nodes']:
                    resilience_demand[node]['total_demand'] = resilience_demand[node]['total_demand'] + simulation_results.node['demand'].to_dict('index')[step * 3600][node]

            resilience_result.append(copy.deepcopy(resilience_demand))

        for fail in self.failures[self.init_config.failures_set]['data']:
            if fail['failure_class'] == 'C1' and fail['pipe_id'] in failures:
                fail['prioritization_factor'] = 1

        with open(self.failures_info, "w") as jsonFile:
            json.dump(self.failures, jsonFile)
        return True


# =============================================================================== Main
# new_case = Algorithm_5()
# new_case.update_data()
# new_case.get_failures_id_to_check()
# new_case.prioritization()

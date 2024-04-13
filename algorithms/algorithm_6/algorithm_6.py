"""
          Name:     Algorithm 6 - Algorytm agregacji awarii
        Author:     Ariel Antonowicz
   Last update:     26.03.2022
"""
from algorithms.algorithm_5.algorithm_5 import *


class Algorithm_6:
    def __init__(self):
        self.init_config = Configuration_data()
        self.inp_file = self.init_config.networks_path + self.init_config.inp_file_name + '.inp'

        self.wn = wntr.network.WaterNetworkModel(self.inp_file)
        self.wn.options.time.duration = self.init_config.sim_duration
        self.sim = wntr.sim.EpanetSimulator(wn=self.wn)

        self.failures = None
        self.failures_info = self.init_config.failures_path + self.init_config.failures_info + '.json'
        self.segment_info = self.init_config.segments_info_path + self.init_config.segments + '.json'
        self.aggregation_result = self.init_config.results_path + self.init_config.aggregation_result + '.json'

        self.classification_and_prioritization = Algorithm_5()

        with open(self.segment_info, "r") as jsonFile:
            self.segments = json.load(jsonFile)

        with open(self.failures_info, "r") as jsonFile:
            self.failures = json.load(jsonFile)

    def __del__(self):
        for filename in glob.glob("temp*"):
            os.remove(filename)

    def update_data(self):
        self.classification_and_prioritization.update_data()
        self.classification_and_prioritization.prioritization()

        with open(self.failures_info, "r") as jsonFile:
            self.failures = json.load(jsonFile)

        return self.failures

    def aggregation_first_degree(self):
        aggregation_first_degree = list()

        for segment in self.segments['data']:
            temp = list()

            for fail in self.failures[self.init_config.failures_set]['data']:
                if fail['failure_type'] in ['F2', 'F3'] and fail['pipe_id'] in segment['segment_links']:
                    temp.append(fail['failure_id'])
            if len(temp) >= 2:
                aggregation_first_degree.append({'segment_id': segment['segment_id'], 'failures': temp})

        return {'aggregation_first_degree': aggregation_first_degree}

    def aggregation_second_degree(self):
        aggregation_second_degree = list()

        for fail_1 in self.failures[self.init_config.failures_set]['data']:
            for fail_2 in self.failures[self.init_config.failures_set]['data']:
                seg = list()
                if fail_1['failure_id'] != fail_2['failure_id']:
                    if fail_1['failure_type'] in ['F2', 'F3'] and fail_2['failure_type'] in ['F2', 'F3']:
                        if fail_1['failure_class'] != 'C1' and fail_2['failure_class'] != 'C1':
                            if any(item in fail_1['segment']['segment_valves'] for item in fail_2['segment']['segment_valves']):
                                seg.clear()
                                for segment in self.segments['data']:
                                    if sorted(fail_1['segment']['segment_valves']) == sorted(segment['segment_valves']):
                                        seg.append(segment['segment_id'])
                                    if sorted(fail_2['segment']['segment_valves']) == sorted(segment['segment_valves']):
                                        seg.append(segment['segment_id'])
                                    if len(seg) >= 2 and seg[0] != seg[1]:
                                        aggregation_second_degree.append({'segment_id': seg, 'failures': [fail_1['failure_id'], fail_2['failure_id']]})
                                        break
        result = list()
        for el in aggregation_second_degree:
            result.append({x: sorted(el[x]) for x in el.keys()})

        aggregation_second_degree.clear()

        for el in result:
            if el not in aggregation_second_degree:
                aggregation_second_degree.append(el)

        return {'aggregation_second_degree': aggregation_second_degree}

    def save_proposition_of_aggregation(self):

        first = self.aggregation_first_degree()
        second = self.aggregation_second_degree()
        aggregation = [first, second]

        with open(self.aggregation_result, "w") as jsonFile:
            json.dump(aggregation, jsonFile)

        return aggregation


# =============================================================================== Main
# new_case = Algorithm_6()
# new_case.update_data()
# new_case.aggregation_first_degree()
# new_case.aggregation_second_degree()
# new_case.save_proposition_of_aggregation()

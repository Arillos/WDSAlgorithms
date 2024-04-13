from algorithms.algorithm_6.algorithm_6 import *


class Case():
    def __init___(self):
        pass

    def __del__(self):
        for filename in glob.glob("temp*"):
            os.remove(filename)

    @staticmethod
    def algorithm_1():
        print('Algorithm 1: Resilience of network elements algorithm')
        new_case = Algorithm_1()
        new_case.network_resilience_algorithm()

    @staticmethod
    def algorithm_2():
        print('Algorithm 2: Trace of water algorithm')
        new_case = Algorithm_2()
        new_case.path_creator(node_id='J14')
        new_case.critical_pipes('J14')

    @staticmethod
    def algorithm_3():
        print('Algorithm 3: Typing valve to close algorithm')
        new_case = Algorithm_3()
        new_case.matrix_a_creator()
        new_case.matrix_b_creator()
        new_case.matrix_c_creator()

        new_case.find_all_segments()
        new_case.save_segments()
        new_case.min_number_of_valves('P38')

    @staticmethod
    def algorithm_4():
        print('Algorithm 4: Failures classification algorithm')
        new_case = Algorithm_4()
        new_case.update_data()
        new_case.get_classify()

    @staticmethod
    def algorithm_5():
        print('Algorithm 5: Prioritization failure algorithm')
        new_case = Algorithm_5()
        new_case.update_data()
        # new_case.get_failures_id_to_check()
        new_case.prioritization()

    @staticmethod
    def algorithm_6():
        print('Algorithm 6: Aggregation failure algorithm')
        new_case = Algorithm_6()
        new_case.update_data()
        # new_case.aggregation_first_degree()
        # new_case.aggregation_second_degree()
        new_case.save_proposition_of_aggregation()


case = Case()
case.algorithm_1()
case.algorithm_2()
case.algorithm_3()
case.algorithm_4()
case.algorithm_5()
case.algorithm_6()

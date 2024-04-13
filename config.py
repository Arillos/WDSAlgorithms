class Configuration_data:
    def __init__(self):

        # ======================================================== MODEL AND SIMULATION

        self.inp_file_name = 'ariel_phd'
        self.sim_duration = 24

        # ======================================================== PATHS

        self.networks_path = 'C:\\Users\\ariel\\PycharmProjects\\doctorate\\networks\\'
        self.additional_data_path = 'C:\\Users\\ariel\\PycharmProjects\\doctorate\\networks\\additional_data\\'
        self.results_path = 'C:\\Users\\ariel\\PycharmProjects\\doctorate\\results\\'
        self.valve_info_path = 'C:\\Users\\ariel\\PycharmProjects\\doctorate\\valves\\'
        self.segments_info_path = 'C:\\Users\\ariel\\PycharmProjects\\doctorate\\segments\\'
        self.matrix_path = 'C:\\Users\\ariel\\PycharmProjects\\doctorate\\matrix\\'
        self.scenarios_path = 'C:\\Users\\ariel\\PycharmProjects\\doctorate\\scenarios\\'
        self.failures_path = 'C:\\Users\\ariel\\PycharmProjects\\doctorate\\failures\\'

        # ======================================================== ALGORITHM 1

        self.nodes_csv_file = self.inp_file_name + '_nodes'
        self.links_csv_file = self.inp_file_name + '_links'

        self.flow_category = {'CAT-1': [90.0, float('inf')],
                              'CAT-2': [75.0, 89.9],
                              'CAT-3': [50.0, 74.9],
                              'CAT-4': [float('-inf'), 49.9]}

        self.head_category = {'CAT-1': [90.0, float('inf')],
                              'CAT-2': [75.0, 89.9],
                              'CAT-3': [50.0, 74.9],
                              'CAT-4': [float('-inf'), 49.9]}

        self.demand_category = {'CAT-1': [90.0, float('inf')],
                                'CAT-2': [75.0, 89.9],
                                'CAT-3': [50.0, 74.9],
                                'CAT-4': [float('-inf'), 49.9]}

        self.pressure_category = {'CAT-1': [90.0, float('inf')],
                                  'CAT-2': [75.0, 89.9],
                                  'CAT-3': [50.0, 74.9],
                                  'CAT-4': [float('-inf'), 49.9]}

        # ======================================================== ALGORITHM 2

        # ======================================================== ALGORITHM 3
        self.valve_info = self.inp_file_name + '_valve_info'
        self.valve_set = 'set_1'
        self.segments = self.inp_file_name + '_segments'

        self.matrix_a = self.inp_file_name + '_matrixA'
        self.matrix_b = self.inp_file_name + '_matrixB'
        self.matrix_c = self.inp_file_name + '_matrixC'

        # ======================================================== ALGORITHM 4
        self.failures_info = self.inp_file_name + '_failures_info'
        self.failures_set = 'set_2'

        self.historical_data_random = [3, 10]

        multiplier = 0.0254 # in to m
        self.map_pipe_diameter ={'D3': [0, 14*multiplier],
                                 'D2': [14*multiplier, 18*multiplier],
                                 'D1': [18*multiplier, 24*multiplier]}

        self.repair_times = {
            'D3': {
                'open_valve': [10, 15],
                'close_valve': [10, 15],
                'failure_localisation': [20, 25],
                'asphalt_extraction': [70, 120],
                'removal_of_paving_slabs': [30, 35],
                'excavation_for_the_pipeline': [80, 100],
                'pumping_out_the_excavation': [30, 60],
                'cleaning_the_pipe': [30, 35],
                'mount_the_bound': [25, 30],
                'assembly_of_the_seal': [40, 45],
                'pipe_remove': [30, 40],
                'add_new_pipe': [50, 60],
                'disinfection': [20, 25],
                'backfilling_the_conduit': [40, 50],
                'finishing_and_cleaning_activities': [60, 80]
            },
            'D2': {
                'open_valve': [15, 20],
                'close_valve': [15, 20],
                'failure_localisation': [55, 60],
                'asphalt_extraction': [120, 160],
                'removal_of_paving_slabs': [45, 50],
                'excavation_for_the_pipeline': [100, 140],
                'pumping_out_the_excavation': [80, 120],
                'cleaning_the_pipe': [40, 45],
                'mount_the_bound': [40, 50],
                'assembly_of_the_seal': [50, 55],
                'pipe_remove': [50, 60],
                'add_new_pipe': [60, 70],
                'disinfection': [30, 35],
                'backfilling_the_conduit': [55, 65],
                'finishing_and_cleaning_activities': [75, 100]
            },
            'D1': {
                'open_valve': [20, 30],
                'close_valve': [20, 30],
                'failure_localisation': [50, 60],
                'asphalt_extraction': [160, 240],
                'removal_of_paving_slabs': [60, 65],
                'excavation_for_the_pipeline': [150, 240],
                'pumping_out_the_excavation': [120, 180],
                'cleaning_the_pipe': [50, 60],
                'mount_the_bound': [60, 90],
                'assembly_of_the_seal': [60, 90],
                'pipe_remove': [90, 140],
                'add_new_pipe': [180, 240],
                'disinfection': [50, 60],
                'backfilling_the_conduit': [70, 80],
                'finishing_and_cleaning_activities': [100, 160]
            }}

        self.failure_type = {
            'F1': ['failure_localisation', 'asphalt_extraction', 'removal_of_paving_slabs', 'excavation_for_the_pipeline', 'pumping_out_the_excavation',
                   'mount_the_bound', 'assembly_of_the_seal', 'backfilling_the_conduit', 'finishing_and_cleaning_activities'],
            'F2': ['open_valve', 'close_valve', 'failure_localisation', 'asphalt_extraction', 'removal_of_paving_slabs', 'excavation_for_the_pipeline', 'pumping_out_the_excavation',
                   'cleaning_the_pipe', 'assembly_of_the_seal', 'mount_the_bound', 'disinfection', 'backfilling_the_conduit', 'finishing_and_cleaning_activities'],
            'F3': ['open_valve', 'close_valve', 'failure_localisation', 'asphalt_extraction', 'removal_of_paving_slabs', 'excavation_for_the_pipeline', 'pumping_out_the_excavation',
                   'cleaning_the_pipe', 'assembly_of_the_seal', 'pipe_remove', 'add_new_pipe', 'disinfection', 'backfilling_the_conduit', 'finishing_and_cleaning_activities']
        }

        # ======================================================== ALGORITHM 5
        self.additional_info = self.inp_file_name + '_additional_info'
        self.additional_set = 'set_1'

        # ======================================================== ALGORITHM 6
        self.aggregation_result = self.inp_file_name + '_aggregation'


        # ======================================================== ALGORITHM 7
        self.scenario_file = self.inp_file_name + '_scenario'

        self.repair_cost = {'F1': {'clamps': 2, 'pipes': 0, 'other_stuff': 10},
                            'F2': {'clamps': 4, 'pipes': 0, 'other_stuff': 15},
                            'F3': {'clamps': 0, 'pipes': 2, 'other_stuff': 20}}

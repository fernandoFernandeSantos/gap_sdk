import os

# GAP SDK root dir
GAP_SDK_ROOT_DIR = "/home/fernando/git_research/gap_sdk"
GVSOC_ROOT_DIR = f"{GAP_SDK_ROOT_DIR}/gvsoc"

APP_PARAMETERS = {
    # ################################################
    # "MatrixAdd": {
    #     # Path to the benchmark inside GAP SDK
    #     "app_root_dir": f"{GAP_SDK_ROOT_DIR}/examples/autotiler/MatrixAdd",
    #     # Run script to execute the simulator
    #     "run_script": "test_apps/MatrixAdd/run.sh",
    #     # how much time the app is expected to run in seconds
    #     "expected_run_time": 1,
    # },
    # ################################################
    # "MatMult": {
    #     # Path to the benchmark inside GAP SDK
    #     "app_root_dir": f"{GAP_SDK_ROOT_DIR}/examples/autotiler/MatMult",
    #     # Run script to execute the simulator
    #     "run_script": "test_apps/MatMult/run.sh",
    #     # how much time the app is expected to run in seconds
    #     "expected_run_time": 2,
    # },
    ################################################
    "Mnist": {
        # Path to the benchmark inside GAP SDK
        "app_root_dir": f"{GAP_SDK_ROOT_DIR}/examples/gap8/nn/autotiler/Mnist",
        # Run script to execute the simulator
        "run_script": "test_apps/Mnist/run.sh",
        # how much time the app is expected to run in seconds
        "expected_run_time": 2,
    },
    # ################################################
    # "Fir": {
    #     # Path to the benchmark inside GAP SDK
    #     "app_root_dir": f"{GAP_SDK_ROOT_DIR}/examples/autotiler/Fir",
    #     # Run script to execute the simulator
    #     "run_script": "test_apps/Fir/run.sh",
    #     # how much time the app is expected to run in seconds
    #     "expected_run_time": 2,
    # },
    # ################################################
    # "BilinearResize": {
    #     # Path to the benchmark inside GAP SDK
    #     "app_root_dir": f"{GAP_SDK_ROOT_DIR}/examples/autotiler/BilinearResize",
    #     # Run script to execute the simulator
    #     "run_script": "test_apps/BilinearResize/run.sh",
    #     # how much time the app is expected to run in seconds
    #     "expected_run_time": 1,
    # },
    # ################################################
    # "memradtest": {
    #     # Path to the benchmark inside GAP SDK
    #     "app_root_dir": f"{GAP_SDK_ROOT_DIR}/examples/pmsis/memradtest",
    #     # Run script to execute the simulator
    #     "run_script": "test_apps/BilinearResize/run.sh",
    #     # how much time the app is expected to run in seconds
    #     "expected_run_time": 1,
    # }
    # ################################################
    # **{
    #     i: {
    #         # Path to the benchmark inside GAP SDK
    #         "app_root_dir": f"{GAP_SDK_ROOT_DIR}/benchmarks/gap8/{i}",
    #         # Run script to execute the simulator
    #         "run_script": f"test_apps/{i}/run.sh",
    #         # how much time the app is expected to run in seconds
    #         "expected_run_time": 1,
    #     } for i in ["convparallel", "convsequential", "linearparallel",
    #                 "linearsequential", "maxpoolparallel", "maxpoolsequential"]
    # }
}

# Num of injections simulations that will execute
NUM_INJECTIONS = 10000

VERBOSE = False

# Timeout threshold to verify if the app get stuck (it will multiply by expected_run_time
# the timeout will be calculated by expected_run_time * TIMEOUT_THRESHOLD
TIMEOUT_THRESHOLD = 3

# TODO: check if this is better to set manually outside of the script

# Base root dir
GVSOCFI_ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

# logs dir, just like nvbitfi
GVSOCFI_LOGS_DIR = f"{GVSOCFI_ROOT_DIR}/logs"

# Set the GAPUINO version here
GAPUINO_SOURCE_SCRIPT = f"{GAP_SDK_ROOT_DIR}/configs/gapuino_v3.sh"

# Default profiler file
PROFILER_FILE = "gvsocfi-profiler-info-{injection_site}.txt"

# Profiler list order
PROFILER_FIELDS_INST_INJECTION = [
    "iteration_counter_gvsocfi",
    # "address", "opcode", "resource_id",
    "label", "size",
    "cpu_config_mhartid",
    "nb_out_reg", "out_reg0", "out_reg1", "out_reg2",
    # "nb_in_reg", "in_reg0", "in_reg1", "in_reg2"
]

PROFILER_FIELDS_MEM_INJECTION = [
    "mem_iteration_counter_gvsocfi", "mem_data0", "mem_data1", "offset", "operation_size", "total_memory_size"
]

GVSOCFI_INJECTION_IN_FILE = "gvsocfi-injection-in.txt"
GVSOCFI_INJECTION_OUT_FILE = "gvsocfi-injection-out.txt"
FINAL_INJECTION_DATA = "gvsocfi-injection-data-results-{fault_num}_{fault_site}.csv"
# APP_INJECTION_FOLDER_BASE = "injection-logs"

# Default stdout and stderr files
DEFAULT_GOLDEN_STDOUT_FILE = "golden_stdout.txt"
DEFAULT_GOLDEN_STDERR_FILE = "golden_stderr.txt"
DEFAULT_STDOUT_FILE = "stdout.txt"
DEFAULT_STDERR_FILE = "stderr.txt"

GVSOCFI_PROFILER_OUTPUT = "/tmp/gvsocfi_prof_output.txt"


# Data from beam experiments
l1_double_cell_hist_norm = [0.06153846153846154, 0.015384615384615385, 0.5692307692307692, 0.03076923076923077,
                            0.015384615384615385, 0.015384615384615385, 0.015384615384615385, 0.03076923076923077,
                            0.15384615384615385, 0.015384615384615385, 0.015384615384615385, 0.015384615384615385,
                            0.015384615384615385, 0.03076923076923077]
l1_double_cell_bins = [16, 112, 128, 144, 240, 256, 265, 880, 1024, 1040, 1280, 1983, 3418, 5590, 6101]

l2_double_cell_hist_norm = [0.08287292817679558, 0.016574585635359115, 0.34806629834254144, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.011049723756906077, 0.13812154696132597,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384, 0.0055248618784530384,
                            0.011049723756906077]

l2_double_cell_bins = [8, 56, 64, 72, 368, 448, 504, 512, 576, 1016, 1080, 1406, 1452, 2826, 4625, 4673, 5486, 5688,
                       5759, 6129,
                       6693, 6848, 7240, 8047, 8140, 8150, 10690, 15279, 15343, 18142, 19418, 19531, 20868, 21219,
                       22641, 22918,
                       24639, 28344, 30466, 31011, 32109, 32691, 34597, 36356, 37451, 38486, 38641, 38987, 39419, 41213,
                       45810,
                       48079, 49403, 49767, 52757, 53151, 54909, 56408, 61880, 62599, 63234, 63415, 64078, 66426, 69930,
                       70252,
                       75347, 76144, 78929, 78944, 78956, 82375, 90113, 93294, 95391, 101573, 101714, 105553]

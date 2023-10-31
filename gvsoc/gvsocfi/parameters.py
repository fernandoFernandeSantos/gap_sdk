import os
from common import FaultModel

APP_PARAMETERS = {
    # ################################################
    # "MatrixAdd": {
    #     # Path to the benchmark inside GAP SDK
    #     "app_root_dir": "/home/carol/gap_sdk/examples/autotiler/MatrixAdd",
    #     # Run script to execute the simulator
    #     "run_script": "test_apps/MatrixAdd/run.sh",
    #     # how much time the app is expected to run in seconds
    #     "expected_run_time": 1,
    # },
    # ################################################
    # "MatMult": {
    #     # Path to the benchmark inside GAP SDK
    #     "app_root_dir": "/home/carol/gap_sdk/examples/autotiler/MatMult",
    #     # Run script to execute the simulator
    #     "run_script": "test_apps/MatMult/run.sh",
    #     # how much time the app is expected to run in seconds
    #     "expected_run_time": 2,
    # },
    ################################################
    "Mnist": {
        # Path to the benchmark inside GAP SDK
        "app_root_dir": "/home/carol/gap_sdk/examples/gap8/nn/autotiler/Mnist",
        # Run script to execute the simulator
        "run_script": "test_apps/Mnist/run.sh",
        # how much time the app is expected to run in seconds
        "expected_run_time": 2,
    },
    # ################################################
    # "Fir": {
    #     # Path to the benchmark inside GAP SDK
    #     "app_root_dir": "/home/carol/gap_sdk/examples/autotiler/Fir",
    #     # Run script to execute the simulator
    #     "run_script": "test_apps/Fir/run.sh",
    #     # how much time the app is expected to run in seconds
    #     "expected_run_time": 2,
    # },
    # ################################################
    # "BilinearResize": {
    #     # Path to the benchmark inside GAP SDK
    #     "app_root_dir": "/home/carol/gap_sdk/examples/autotiler/BilinearResize",
    #     # Run script to execute the simulator
    #     "run_script": "test_apps/BilinearResize/run.sh",
    #     # how much time the app is expected to run in seconds
    #     "expected_run_time": 1,
    # },
    # ################################################
    # "memradtest": {
    #     # Path to the benchmark inside GAP SDK
    #     "app_root_dir": "/home/carol/gap_sdk/examples/pmsis/memradtest",
    #     # Run script to execute the simulator
    #     "run_script": "test_apps/BilinearResize/run.sh",
    #     # how much time the app is expected to run in seconds
    #     "expected_run_time": 1,
    # }
}

# Num of injections simulations that will execute
NUM_INJECTIONS = 5
# fault model for the campaigns
FAULT_MODEL = FaultModel.SINGLE_BIT_FLIP

VERBOSE = False

# Timeout threshold to verify if the app get stuck (it will multiply by expected_run_time
# the timeout will be calculated by expected_run_time * TIMEOUT_THRESHOLD
TIMEOUT_THRESHOLD = 3

# TODO: check if this is better to set manually outside of the script

# Base root dir
GVSOCFI_ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

# logs dir, just like nvbitfi
GVSOCFI_LOGS_DIR = f"{GVSOCFI_ROOT_DIR}/logs"

# GAP SDK root dir
GAP_SDK_ROOT_DIR = "/home/carol/gap_sdk"
GVSOC_ROOT_DIR = f"{GAP_SDK_ROOT_DIR}/gvsoc"

# Set the GAPUINO version here
GAPUINO_SOURCE_SCRIPT = f"{GAP_SDK_ROOT_DIR}/configs/gapuino_v3.sh"

# Default profiler file
PROFILER_FILE = "gvsocfi-profiler-info.txt"

# Profiler list order
PROFILER_FIELDS = [
    "iteration_counter_gvsocfi",
    # "address", "opcode", "resource_id",
    "label", "size",
    "cpu_config_mhartid",
    "nb_out_reg", "out_reg0", "out_reg1", "out_reg2",
    # "nb_in_reg", "in_reg0", "in_reg1", "in_reg2"
]

GVSOCFI_INJECTION_IN_FILE = "gvsocfi-injection-in.txt"
GVSOCFI_INJECTION_OUT_FILE = "gvsocfi-injection-out.txt"
FINAL_INJECTION_DATA = "gvsocfi-injection-data-results-{fault_num}-{fault_model}.csv"
APP_INJECTION_FOLDER_BASE = "injection-logs"

# Default stdout and stderr files
DEFAULT_GOLDEN_STDOUT_FILE = "golden_stdout.txt"
DEFAULT_GOLDEN_STDERR_FILE = "golden_stderr.txt"
DEFAULT_STDOUT_FILE = "stdout.txt"
DEFAULT_STDERR_FILE = "stderr.txt"

GVSOCFI_PROFILER_OUTPUT = "/tmp/gvsocfi_prof_output.txt"

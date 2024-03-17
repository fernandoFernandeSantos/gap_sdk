#!/usr/bin/python3
import os
import re
import sys
import numpy as np

sys.path.insert(0, '../')

import common
import parameters
import pandas as pd

MASKED, SINGLE, LINE, SQUARE, RANDOM = "MASKED", "SINGLE", "LINE", "SQUARE", "RANDOM"
CNN_MATRIX_SIZE = {
    "convparallel": (100, 100), "convsequential": (100, 100),
    "linearparallel": (16,), "linearsequential": (16,),
    "maxpoolparallel": (int(112 / 2), int(112 / 2)), "maxpoolsequential": (int(112 / 2), int(112 / 2))
}

RUNNER_HAS_FAILED = "Runner has failed"
ILLEGAL_INSTRUCTION = "Reached illegal instruction"
MEMORY_ALLOCATION_FAILED = "Memory allocation failed"
CLUSTER_OPEN_FAILED = "Cluster open failed"
INVALID_ACCESS = "Invalid access"
INVALID_FETCH_REQUEST = "Invalid fetch request"
UNABLE_TO_INIT_TIME_DRIVER = "Unable to initialize time driver"
TIMEOUT_ERROR = "TIMEOUT_ERROR"
UNICODE_ERROR = "UNICODE_ERROR"
RUNTIME_ERROR = "RUNTIME_ERROR"
ALL_STD_ERRORS = [TIMEOUT_ERROR, UNICODE_ERROR, RUNTIME_ERROR, INVALID_FETCH_REQUEST,
                  RUNNER_HAS_FAILED, ILLEGAL_INSTRUCTION,
                  MEMORY_ALLOCATION_FAILED, CLUSTER_OPEN_FAILED, INVALID_ACCESS, UNABLE_TO_INIT_TIME_DRIVER]


def check_gvsocfi_error_messages(stderr_lines: list):
    gvsoc_fi_error = False
    gvsoc_crash = False
    for line in stderr_lines:
        if any([i in line for i in ["Segmentation fault", "Aborted", "Bus error"]]):
            gvsoc_crash = True
        if "GVSOCFI_ERROR:::" in line:
            gvsoc_fi_error = True

    return gvsoc_fi_error, gvsoc_crash


def get_default_due_cases(full_output_lines: list):
    due = 0
    due_type = "NO_DUE"
    crash_str = ""
    for line in full_output_lines:
        for stderr_type in ALL_STD_ERRORS:
            if stderr_type in line:
                due_type = stderr_type
                due = 1
                crash_str = line
    return due, due_type, crash_str


def get_next_element(input_list: list):
    # Find the index of "FAULT_INJECTED_HERE" in the list
    try:
        idx = input_list.index("FAULT_INJECTED_HERE")
    except ValueError:
        return None  # "FAULT_INJECTED_HERE" not found in the list

    # Check if "FAULT_INJECTED_HERE" is the last element
    if idx == len(input_list) - 1:
        return None  # "FAULT_INJECTED_HERE" is the last element

    # Return the next element after "FAULT_INJECTED_HERE"
    return input_list[idx + 1]


def read_outputs(injection_log_path: str):
    stdout_path = os.path.join(injection_log_path, "stdout.txt")
    with open(stdout_path, errors='ignore') as stdout_fp:
        stdout_lines = stdout_fp.readlines()
    stderr_path = os.path.join(injection_log_path, "stderr.txt")
    with open(stderr_path) as stderr_fp:
        stderr_lines = stderr_fp.readlines()
    return stderr_lines, stdout_lines


def parse_mnist(injection_log_path: str, fi_data: dict):
    stderr_lines, stdout_lines = read_outputs(injection_log_path=injection_log_path)

    # Search for the layer injection
    stdout_save_path = os.path.join(injection_log_path, "stdout_save.txt")
    layer_inj_possible_strings = ["1C0", "1M0", "1C1", "1M1", "2C0", "2M0", "3L0", "3R0", "FAULT_INJECTED_HERE"]
    layer_injections = list()
    if os.path.isfile(stdout_save_path):
        with open(stdout_save_path, errors='ignore') as stdout_save_fp:
            for line in stdout_save_fp.readlines():
                if any([j in line for j in layer_inj_possible_strings]):
                    layer_injections.append(line.strip())

    injected_layer = get_next_element(input_list=layer_injections)

    crash_between_layers = False
    if injected_layer is None:
        # First remove the FAULT_INJECTED_HERE
        if "FAULT_INJECTED_HERE" in layer_injections:
            layer_injections.remove("FAULT_INJECTED_HERE")

        layer_inj_length = len(layer_injections)
        if 0 < layer_inj_length < 8:  # Crashed before
            crash_between_layers = True
            injected_layer = layer_injections[-1]
        elif layer_inj_length == 0:  # Empty case
            injected_layer = "1C0"
        elif layer_inj_length == 8:
            injected_layer = "3R0"

    if injected_layer is None:
        # Strange case
        print(layer_inj_length)
        print(fi_data)
        print(injection_log_path)
        raise ValueError(f"Incorrect parsed")

    gvsoc_fi_error, gvsoc_crash = check_gvsocfi_error_messages(stderr_lines=stderr_lines)

    gvsocfi_output_log_file = os.path.join(injection_log_path, "gvsocfi-injection-out.txt")
    was_fault_injected = False
    if gvsoc_fi_error is False and gvsoc_crash is False and os.path.isfile(gvsocfi_output_log_file):
        was_fault_injected = True

    due, due_type, crash_str = get_default_due_cases(full_output_lines=stdout_lines + stderr_lines)

    if fi_data["error_code"] != "NO_DUE":
        due = 1
        due_type = fi_data["error_code"]

    critical_sdc, sdc = 0, 0
    lines = 0
    incorrect_attribute_error = False
    # 6: Confidence: 30228
    for line in stdout_lines:
        # dealing with cases
        line_parsed = line.replace("Confience", "Confidence")
        m = re.match(r"([+-]?\d*).*: Confidence: *(-?\d+)", line_parsed)
        if m:
            lines += 1
            num, confidence = m.groups()
            if (num != '6' and confidence != '-32768') or (num == '6' and confidence != '30228'):
                sdc = 1
        elif ': 30228' in line_parsed and lines == 6:
            lines += 1  # No sdc

        critical = re.match(r"Recognized number : *([+-]?\d+)", line)
        # try:
        if "Recognized number" in line and int(critical.group(1)) != 6:
            sdc = 1
            critical_sdc = 1
        # except AttributeError:
        #     print("".join(stdout_lines))
        #     incorrect_attribute_error = True
    # If this is the case, nothing happened
    test_success = any(["Test success with 0 error" in line for line in stdout_lines])
    if test_success:
        if (due != 0 or critical_sdc != 0) and fi_data['error_code'] != 'POSSIBLE_GVSOC_CRASH':
            print(fi_data)
            # print("".join(stdout_lines + stderr_lines))
            raise ValueError("PAU")
        assert critical_sdc == 0

    error_dict = {
        **fi_data,
        "SDC": sdc, "Critical_SDC": critical_sdc, "DUE": due, "DUE_type": due_type, "crash_str": crash_str,
        "was_fault_injected": was_fault_injected, "injected_layer": injected_layer
    }

    if lines != 10 and due == 0 and incorrect_attribute_error is False:
        if test_success is False and sdc == 0:
            print(injection_log_path)
            print(fi_data)
            raise ValueError("PAU")

    if due == 0 and crash_between_layers and all([i not in injection_log_path for i in ["inj-1459"]]):
        print(error_dict)
        print(injection_log_path)
        raise ValueError("".join(stdout_lines + stderr_lines))

    return error_dict


def geometry_comparison(diff):
    def has_grouped_ones(arr: np.ndarray) -> bool:
        for i in range(1, len(arr) - 1):
            if arr[i] == 1 and (arr[i - 1] == 1 or arr[i + 1] == 1):
                return True
        return False

    error_format = MASKED
    count_non_zero_diff = np.count_nonzero(diff)
    num_dimensions = diff.ndim

    if count_non_zero_diff == 1:
        error_format = SINGLE
    elif count_non_zero_diff > 1:
        if num_dimensions == 1:
            if has_grouped_ones(arr=diff):
                error_format = LINE
            else:
                error_format = RANDOM
        else:
            # Use label function to labeling the matrix
            where_is_corrupted = np.argwhere(diff != 0)
            # Get all positions of X and Y
            all_x_positions = where_is_corrupted[:, 0]
            all_y_positions = where_is_corrupted[:, 1]
            # Count how many times each value is in the list
            unique_elements, counter_x_positions = np.unique(all_x_positions, return_counts=True)
            unique_elements, counter_y_positions = np.unique(all_y_positions, return_counts=True)

            # Check if any value is in the list more than one time
            row_error = np.any(counter_x_positions > 1)
            col_error = np.any(counter_y_positions > 1)

            if row_error and col_error:  # square error
                error_format = SQUARE
            elif row_error or col_error:  # row/col error
                error_format = LINE
            else:  # random error
                error_format = RANDOM
    return error_format


def parse_errors_cnn(injection_log_path: str, cnn_op: str, fi_data: pd.Series):
    stderr_lines, stdout_lines = read_outputs(injection_log_path=injection_log_path)

    cnn_op_size = CNN_MATRIX_SIZE[cnn_op]
    diff_matrix = np.zeros(cnn_op_size)

    log_lines = stdout_lines + stderr_lines
    gvsoc_fi_error, gvsoc_crash = check_gvsocfi_error_messages(stderr_lines=stderr_lines)

    gvsocfi_output_log_file = os.path.join(injection_log_path, "gvsocfi-injection-out.txt")
    was_fault_injected = False
    if gvsoc_fi_error is False and gvsoc_crash is False and os.path.isfile(gvsocfi_output_log_file):
        was_fault_injected = True

    due, due_type, crash_str = get_default_due_cases(full_output_lines=stdout_lines + stderr_lines)
    if fi_data["error_code"] != "NO_DUE":
        due = 1
        due_type = fi_data["error_code"]

    # The case where the runner died for real
    if any(["Error: no device found" in err_list_it for err_list_it in log_lines]):
        raise ValueError(f"RUN DIED FOR REAL, INVESTIGATE\n{log_lines}")
    # stdout_diff, stderr_diff, due, due_type = find_standard_errors(log_lines=err_list)
    sdc = 0
    for line in log_lines:
        # Search for SDC
        error_match = re.match(r"Error:\[(\d+)(?:,(\d+))?]=(-?\d+) != (-?\d+)", line.strip())
        if error_match:
            # Gold can be equal too, then not actually an error
            i, j = int(error_match.group(1)), (int(error_match.group(2)) if error_match.group(2) else None)
            found, gold = int(error_match.group(3)), int(error_match.group(4))

            if found != gold:
                sdc = 1
                if cnn_op in ["linearparallel", "linearsequential"]:
                    try:
                        diff_matrix[i] = 1
                    except IndexError:
                        pass
                        # print(f"Output index corrupted:{i}")
                        # return dict(), np.zeros(diff_matrix.shape)
                elif cnn_op in ["convparallel", "convsequential", "maxpoolparallel", "maxpoolsequential"]:
                    diff_matrix[i, j] = 1
                else:
                    raise ValueError(f"Not valid size or operation:{line} {cnn_op_size} {i} {j}")
            due = 0

    # After processing the entire diff_matrix we search for the error format
    error_format = geometry_comparison(diff=diff_matrix)

    error_dict = {
        **fi_data,
        "SDC": sdc, "DUE": due, "DUE_type": due_type, "crash_str": crash_str, "error_format": error_format,
        "was_fault_injected": was_fault_injected,
    }

    return error_dict


def parse_injected_fault(df: pd.DataFrame, app_name: str, app_logs_path: str, fault_model: common.FaultModel,
                         fault_site: str):
    series_list = list()
    for inj_it, row in df.iterrows():
        injection_log_path = os.path.join(app_logs_path, f"{fault_model}_{fault_site}", f"inj-{inj_it}")
        fi_data = row.to_dict()
        if app_name == "Mnist":
            new_row = parse_mnist(injection_log_path=injection_log_path, fi_data=fi_data)
        elif app_name in CNN_MATRIX_SIZE:
            new_row = parse_errors_cnn(injection_log_path=injection_log_path, cnn_op=app_name, fi_data=fi_data)
        else:
            raise ValueError(f"Invalid app name:{app_name}")

        series_list.append(new_row)

    return pd.DataFrame(series_list)


def main():
    clock = common.Timer()
    clock.tic()
    final_csv = list()
    tested_fault_sites = common.POSSIBLE_FAULT_SITES

    for fault_site in tested_fault_sites:
        fault_models = [common.FaultModel.INSTRUCTION_OUTPUT_95PCT_SINGLE]
        if fault_site == common.MEMORY:
            fault_models = [common.FaultModel.MEMORY_CELL_BASED_ON_BEAM]
        # Profiling all the apps on parameters.apps_parameters
        for app_name in parameters.APP_PARAMETERS.keys():
            # Create the logdir specific for the app
            app_logs_path = f"{parameters.GVSOCFI_LOGS_DIR}/{app_name}"
            injection_data_path = (
                f"{app_logs_path}/"
                f"{parameters.FINAL_INJECTION_DATA.format(fault_num=parameters.NUM_INJECTIONS, fault_site=fault_site)}"
            )
            fault_injection_df = pd.read_csv(injection_data_path, sep=";", index_col=False)
            fault_injection_df["fault_site"] = fault_site
            fault_injection_df["benchmark"] = app_name

            for fault_model in fault_models:
                print("Parsing code:", app_name, "Fault model:", fault_model, "Fault site:", fault_site)
                fault_model_df = fault_injection_df[fault_injection_df["fault_model"] == fault_model].reset_index(
                    drop=True)
                # Parse injected faults
                fault_model_df = parse_injected_fault(df=fault_model_df, app_name=app_name, app_logs_path=app_logs_path,
                                                      fault_model=fault_model, fault_site=fault_site)
                final_csv.append(fault_model_df)
    clock.toc()
    # Save the results
    final_injection_data_path = f"data/gvsocfi_parsed_fi_database_{parameters.NUM_INJECTIONS}_mnist.csv"
    print("Time to parse results:", clock, " - Saving final results on:", final_injection_data_path)
    # It is necessary to save both levels of index
    final_csv = (
        pd.concat(final_csv)
        .reset_index()
        .rename(columns={"level_1": "injection_it", "level_0": "app"})
        .drop(columns="index")
    )
    print(final_csv)
    final_csv.to_csv(final_injection_data_path, sep=";", index=False)


if __name__ == '__main__':
    main()

# def check_stdout_error_messages(app_logs_path: str, inj_it: str,
#                                 fault_model: common.FaultModel, fault_site: str) -> Tuple[list, list]:
#     injection_log_path = f"{app_logs_path}/{fault_model}_{fault_site}/inj-{inj_it}/stdout.txt"
#     # pattern = r'\d+:.*\[.*][ ]+(.*)[ ]+[/|\(].*'
#     pattern = r'\d+:[ ]+\d+:[ ]+\[.*][ ]+(.*)'
#     new_list = list()
#     stdout_lines = list()
#     with open(injection_log_path, "r", errors='ignore') as fp:
#         for line in fp:
#             if '[[[[[[[[[[[[[[' in line:
#                 continue
#             m = re.match(pattern, line)
#             if m and m.group(1) not in new_list:
#                 new_list.append(m.group(1))
#             else:
#                 stdout_lines.append(line)
#
#     return new_list, stdout_lines

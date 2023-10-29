#!/usr/bin/python3
import filecmp
import os
from typing import Tuple
import re

import common
import parameters
import pandas as pd


# RAD parsing functions
def default_error_cases(log_lines: list) -> dict:
    error_parsed = dict()
    error_parsed["test_success_found"] = False
    error_parsed["SDC"] = 0
    for line in log_lines:
        if "Test failed" in line or "failed with" in line:
            error_parsed["SDC"] = 1
        if "Test success" in line or "success with 0" in line or "with 0 error" in line:
            error_parsed["test_success_found"] = True
            error_parsed["SDC"] = 0
        if "Reached illegal instruction" in line:
            error_parsed["CRASH_ILLEGAL_INST"] = 1
        if "Runner has failed" in line:
            error_parsed["CRASH_RUNNER"] = 1
        if "Memory allocation failed" in line:
            error_parsed["CRASH_MEM"] = 1
        if "Cluster open failed" in line:
            error_parsed["CRASH_CLUSTER"] = 1
        new_pattern = r".*\[.*] (\S+):(.*)"
        m = re.match(new_pattern, line)
        if m:
            error_parsed["CRASH_STR"] = m.groups()

    return error_parsed


def parse_mat_mul(log_lines: list, error_dict: dict) -> dict:
    for line in log_lines:
        if "Error, result of different methods does not correspond!" in line or "Error: Out" in line:
            error_dict["SDC"] = 1
    return error_dict


def parse_bilinear_resize(log_lines: list, error_dict: dict) -> dict:
    size_ok = False
    for line in log_lines:
        if "Failed to load image" in line:
            error_dict["SDC"] = 1
        if "Gray, Size: 77924 bytes" in line:
            size_ok = True

    if size_ok is False and error_dict["test_success_found"] is False:
        error_dict["SDC"] = 1

    return error_dict


def parse_mat_add(log_lines: list, error_dict: dict) -> dict:
    for line in log_lines:
        if "Error: MatOut" in line:
            error_dict["SDC"] = 1

    if error_dict["test_success_found"]:
        error_dict["SDC"] = 0
    return error_dict


def parse_mnist(log_lines: list, error_dict: dict) -> dict:
    error_dict["CRITICAL_SDC"] = 1

    mnist_gold_stdout = [f"{i}: Confidence: -32768" for i in range(10)]
    mnist_gold_stdout[6] = "6: Confidence: 30228"
    mnist_dict = {i: False for i in mnist_gold_stdout}

    for line in log_lines:
        # If there is something on STDOUT there is an SDC
        m = re.match(r".*Recognized number *: *(\d+)", line)
        if m and int(m.group(1)) == 6:
            error_dict["CRITICAL_SDC"] = 0
        # Check the SDC
        for line_gold in mnist_dict:
            if line_gold in line:
                mnist_dict[line_gold] = True
                break

    if all(mnist_dict.values()):
        error_dict["SDC"] = 0
    else:
        error_dict["SDC"] = 1
    return error_dict


def compute_error(log_lines: list, benchmark: str):
    error_dict = default_error_cases(log_lines=log_lines)
    if benchmark == "Fir":
        error_dict = error_dict
    elif benchmark == "MatMult":
        error_dict = parse_mat_mul(log_lines=log_lines, error_dict=error_dict)
    elif benchmark == "MatrixAdd":
        error_dict = parse_mat_add(log_lines=log_lines, error_dict=error_dict)
    elif benchmark == "Mnist" or benchmark == "MnistGraph":
        error_dict = parse_mnist(log_lines=log_lines, error_dict=error_dict)
    elif benchmark == "BilinearResize":
        error_dict = parse_bilinear_resize(log_lines=log_lines, error_dict=error_dict)
    else:
        raise ValueError(f"Incorrect benchmark value {benchmark}")
    error_dict["benchmark"] = benchmark
    # if all([not i for i in error_dict.values()]):
    #     print(f"INCORRECT PARSING {log_lines}")
    return error_dict


def check_stdout_error_messages(app_logs_path: str, inj_it: str) -> Tuple[list, list]:
    injection_log_path = f"{app_logs_path}/{parameters.APP_INJECTION_FOLDER_BASE}/inj-{inj_it}/stdout.txt"
    # pattern = r'\d+:.*\[.*][ ]+(.*)[ ]+[/|\(].*'
    pattern = r'\d+:[ ]+\d+:[ ]+\[.*][ ]+(.*)'
    new_list = list()
    stdout_lines = list()
    with open(injection_log_path, "r", errors='ignore') as fp:
        for line in fp:
            if '[[[[[[[[[[[[[[' in line:
                continue
            m = re.match(pattern, line)
            if m and m.group(1) not in new_list:
                new_list.append(m.group(1))
            else:
                stdout_lines.append(line)

    return new_list, stdout_lines


def check_stderr_error_messages(app_logs_path: str, inj_it: str):
    injection_log_path = f"{app_logs_path}/{parameters.APP_INJECTION_FOLDER_BASE}/inj-{inj_it}/stderr.txt"
    # is_file_empty = True
    was_fault_injected = True
    gvsoc_crash = False
    stderr_lines = list()
    with open(injection_log_path, "r", errors='ignore') as fp:
        for line in fp:
            if any([i in line for i in ["Segmentation fault", "Aborted", "Bus error"]]):
                gvsoc_crash = True
            if "GVSOCFI_ERROR:::" in line:
                was_fault_injected = False
            # if len(line) > 1:
            #     is_file_empty = False
            stderr_lines.append(line)
    return was_fault_injected, gvsoc_crash, stderr_lines


def parse_injected_fault(row: pd.Series, app_name: str):
    # Categorize by DUEType and SDC
    app_logs_path = f"{parameters.GVSOCFI_LOGS_DIR}/{app_name}"
    inj_it = str(row.name)

    stdout_err_msg, stdout_data = check_stdout_error_messages(app_logs_path=app_logs_path, inj_it=inj_it)
    was_fault_injected, gvsoc_crash, stderr_data = check_stderr_error_messages(app_logs_path=app_logs_path,
                                                                               inj_it=inj_it)

    old_sdc, old_due = row["SDC"], row["DUE"]
    error_dict = compute_error(log_lines=stdout_data + stderr_data, benchmark=app_name)
    if error_dict["test_success_found"] is False and int(old_sdc) != error_dict[
        "SDC"] and not stdout_err_msg and not gvsoc_crash and row[
        "error_code"] != common.DUEType.TIMEOUT_ERROR and "CRASH_STR" not in error_dict:
        os.system(f"cat {app_logs_path}/{parameters.APP_INJECTION_FOLDER_BASE}/inj-{inj_it}/stdout.txt")
        print(row)
        print(error_dict)
        # print(error_dict["test_success_found"])

    for key, value in error_dict.items():
        row[key] = value

    row["was_fault_injected"] = was_fault_injected
    # row["DUE"] = int(is_file_empty is False)
    row["GVSOC_error_state"] = stdout_err_msg

    # the DUE has precedence
    if was_fault_injected is False:
        row["SDC"] = row["DUE"] = False

    return row


def main():
    clock = common.Timer()
    clock.tic()
    final_csv = dict()
    # Profiling all the apps on parameters.apps_parameters
    for app_name, app_parameters in parameters.APP_PARAMETERS.items():
        # Create the logdir specific for the app
        app_logs_path = f"{parameters.GVSOCFI_LOGS_DIR}/{app_name}"
        injection_data_path = f"{app_logs_path}"
        injection_data_path += f"/{parameters.FINAL_INJECTION_DATA.format(parameters.NUM_INJECTIONS)}"
        fault_injection_df = pd.read_csv(injection_data_path, sep=";", index_col=False)
        # Convert to enum
        fault_injection_df["error_code"] = fault_injection_df["error_code"].apply(lambda x: common.DUEType[x])
        # Select only the faults that were injected
        fault_injection_df = fault_injection_df[fault_injection_df["was_fault_injected"]]
        # Parse injected faults
        fault_injection_df = fault_injection_df.apply(parse_injected_fault, args=(app_name,), axis="columns")
        # it is necessary to filter twice
        fault_injection_df = fault_injection_df[fault_injection_df["was_fault_injected"]]
        final_csv[app_name] = fault_injection_df
    clock.toc()
    # Save the results
    final_injection_data_path = "/home/carol/gvsocfi/data/gvsocfi_database.csv"
    print("Time to parse results:", clock, " - Saving final results on:", final_injection_data_path)
    # It is necessary to save both levels of index
    final_csv = pd.concat(final_csv).reset_index().rename(columns={"level_1": "injection_it", "level_0": "app"})
    print(final_csv)
    final_csv.to_csv(final_injection_data_path, sep=";", index=False)


if __name__ == '__main__':
    main()

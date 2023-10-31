#!/usr/bin/python3
import filecmp
import os.path
from typing import Union

import parameters
import pandas as pd
import numpy as np

import common


def create_injection_mask(output_register_val: int, output_register_byte_size: int) -> int:
    # size * byte size
    bit_size = output_register_byte_size * 8
    base_string = ['0'] * bit_size
    if parameters.FAULT_MODEL == common.FaultModel.SINGLE_BIT_FLIP:
        random_bit = np.random.randint(0, bit_size)
        base_string[random_bit] = '1'
    elif parameters.FAULT_MODEL == common.FaultModel.DOUBLE_BIT_FLIP:
        random_bit = np.random.randint(1, bit_size)
        base_string[random_bit] = '1'
        base_string[random_bit - 1] = '1'
    elif parameters.FAULT_MODEL == common.FaultModel.RANDOM_VALUE:
        base_string = list(map(str, np.random.randint(0, 2, bit_size).tolist()))
    elif parameters.FAULT_MODEL == common.FaultModel.ZERO_VALUE:
        base_string = f'{output_register_val:0{bit_size}b}'

    # Just put the mask to inject the faults
    return int("".join(base_string), 2)


def kill_simulator_after_injection():
    kill_program_list = ["gapy", "gvsoc_launcher_debug"]
    # The force killing is necessary here
    for cmd in kill_program_list:
        os.system(f"pkill -9 -f {cmd} && killall -9 {cmd}")


def verify_output(app_logs_path: str, error_code: common.DUEType,
                  injection_log_file: str, injection_logs_path: str,
                  stderr_file: str, stdout_file: str,
                  exec_stdout: Union[str, None], exec_stderr: Union[str, None]):
    # Store any message coming from execution function
    if exec_stdout:
        with open(stdout_file, "a") as stdout_fp:
            stdout_fp.write(f"\n{exec_stdout}\n")
    if exec_stderr:
        with open(stderr_file, "a") as stderr_fp:
            stderr_fp.write(f"\n{exec_stderr}\n")

    if len(open(stdout_file, "rb").read()) == 0 and error_code != common.DUEType.TIMEOUT_ERROR and len(
            open(stderr_file, "rb").read()) == 0:
        print("Check in case of error", open(stdout_file).readlines(), open(stderr_file).readlines())
        exit(1)
    golden_stdout_file = f"{app_logs_path}/{parameters.DEFAULT_GOLDEN_STDOUT_FILE}"
    golden_stderr_file = f"{app_logs_path}/{parameters.DEFAULT_GOLDEN_STDERR_FILE}"

    # Verify correctness
    sdc = not filecmp.cmp(golden_stdout_file, stdout_file, shallow=False)
    due = not filecmp.cmp(golden_stderr_file, stderr_file, shallow=False)
    outcome = "Masked"
    if sdc:
        outcome = "SDC"
    if due or error_code == common.DUEType.TIMEOUT_ERROR:
        due = True
        with open(stderr_file, errors='ignore') as stderr_fp:
            data_from_stderr = stderr_fp.read()
            if "GVSOCFI_ERROR:::" in data_from_stderr:
                print(data_from_stderr)
                # Not a due
                due = False
        if due:
            error_code = common.DUEType.GENERAL_DUE if error_code == common.DUEType.NO_DUE else error_code
            outcome = outcome + ", but DUE also recorded." if outcome == "SDC" else "DUE"
            outcome += f" DUEType:{error_code}"
    was_fault_injected = True
    if outcome == "Masked" and os.path.isfile(injection_log_file) is False:
        outcome = "Fault not injected"
        was_fault_injected = False
    return sdc, due, outcome, was_fault_injected


def inject_sample_faults(row: pd.Series, app_name: str, app_parameters: dict) -> pd.Series:
    inj_clock = common.Timer()
    inj_clock.tic()
    injection_it = row.name
    app_logs_path = f"{parameters.GVSOCFI_LOGS_DIR}/{app_name}"
    injection_logs_path = f"{app_logs_path}/{parameters.APP_INJECTION_FOLDER_BASE}/inj-{injection_it}"
    # Create/Clean the output path
    common.execute_command(command=f"mkdir -p {injection_logs_path}")
    common.execute_command(command=f"rm {injection_logs_path}/*")

    # Inject the fault
    run_cmd = app_parameters["run_script"]
    injection_info_file = f"{injection_logs_path}/{parameters.GVSOCFI_INJECTION_IN_FILE}"
    injection_log_file = f"{injection_logs_path}/{parameters.GVSOCFI_INJECTION_OUT_FILE}"
    stdout_file = f"{injection_logs_path}/{parameters.DEFAULT_STDOUT_FILE}"
    stderr_file = f"{injection_logs_path}/{parameters.DEFAULT_STDERR_FILE}"

    set_environment_vars = [("GVSOCFI_RUN_TYPE", str(common.RunMode.INST_INJECTOR)),
                            ("GVSOCFI_INJECTION_IN_FILE", injection_info_file),
                            ("GVSOCFI_INJECTION_OUT_FILE", injection_log_file),
                            ("STDOUT_FILE", stdout_file),
                            ("STDERR_FILE", stderr_file)]

    # Put the contents in the info file
    row["gvsoc_fi_mask"] = create_injection_mask(output_register_val=row["out_reg0"],
                                                 output_register_byte_size=row["size"])
    with open(injection_info_file, "w") as inj_fp:
        lines_to_write = [row["iteration_counter_gvsocfi"], row["gvsoc_fi_mask"], row["out_reg0"],
                          # row["address"], row["opcode"], row["size"],
                          row["cpu_config_mhartid"], row["label"]]
        inj_fp.writelines("\n".join(map(str, lines_to_write)))

    timeout = app_parameters["expected_run_time"] * parameters.TIMEOUT_THRESHOLD
    # default files
    exec_stdout, exec_stderr, error_code = common.execute_gvsoc(command=run_cmd,
                                                                gapuino_source_script=parameters.GAPUINO_SOURCE_SCRIPT,
                                                                gvsoc_fi_env=set_environment_vars, timeout=timeout)
    sdc, due, outcome, was_fault_injected = verify_output(app_logs_path=app_logs_path, error_code=error_code,
                                                          injection_log_file=injection_log_file,
                                                          injection_logs_path=injection_logs_path,
                                                          stdout_file=stdout_file, stderr_file=stderr_file,
                                                          exec_stdout=exec_stdout, exec_stderr=exec_stderr)

    row["SDC"], row["DUE"] = sdc, due
    row["was_fault_injected"] = was_fault_injected
    row["error_code"] = str(error_code)
    # clean the system before continue
    kill_simulator_after_injection()
    inj_clock.toc()
    print("Injecting fault num:", injection_it, "App:", app_name, "Outcome:", outcome, "exec time:", inj_clock)
    return row


def main():
    clock = common.Timer()
    # Profiling all the apps on parameters.apps_parameters
    for app_name, app_parameters in parameters.APP_PARAMETERS.items():
        # Create the logdir specific for the app
        app_logs_path = f"{parameters.GVSOCFI_LOGS_DIR}/{app_name}"
        profile_app_file = f"{app_logs_path}/{parameters.PROFILER_FILE}"
        profile_df = pd.read_csv(profile_app_file, sep=";", names=parameters.PROFILER_FIELDS,
                                 index_col=False)
        # Create the path if it was not created yet
        injection_logs_path = f"{app_logs_path}/{parameters.APP_INJECTION_FOLDER_BASE}"
        common.execute_command(command=f"mkdir -p {injection_logs_path}/")

        # Remove the instructions that do not have output
        # Select instructions that have only one output register
        # TODO: Add fault injection for more than one output register
        profile_df = profile_df[profile_df["nb_out_reg"] == 1]
        # print(profile_df[(profile_df["address"] == 469766476) & (profile_df["opcode"] == 552826243) &
        #                  (profile_df["cpu_config_mhartid"] == 2) & (profile_df["label"] == "p.lw")])
        # print(len(profile_df["cpu_config_mhartid"].unique()))
        # print(profile_df["cpu_config_mhartid"].value_counts())
        # TODO: which bit generator is better here?
        random_generator = np.random.MT19937()
        # Set the number of injections, if the NUM_INJECTIONS < profile rows then allow repetitions of inj sites
        app_num_injections = parameters.NUM_INJECTIONS if parameters.NUM_INJECTIONS else profile_df.shape[0]
        allow_inj_site_repetition = app_num_injections > profile_df.shape[0]
        profile_df = profile_df.sample(n=app_num_injections, random_state=random_generator,
                                       replace=allow_inj_site_repetition, ignore_index=True)

        # Get the golden values, save them for future analysis
        common.execute_gvsoc(command=app_parameters["run_script"],
                             gapuino_source_script=parameters.GAPUINO_SOURCE_SCRIPT,
                             gvsoc_fi_env=[("STDOUT_FILE", f"{app_logs_path}/{parameters.DEFAULT_GOLDEN_STDOUT_FILE}"),
                                           ("STDERR_FILE", f"{app_logs_path}/{parameters.DEFAULT_GOLDEN_STDERR_FILE}")])

        # Inject sampled faults
        clock.tic()
        profile_df = profile_df.apply(inject_sample_faults, args=(app_name, app_parameters), axis="columns")
        clock.toc()

        # Save the results
        final_injection_data_path = parameters.FINAL_INJECTION_DATA.format(app_num_injections, parameters.FAULT_MODEL)
        final_injection_data_path = f"{app_logs_path}/{final_injection_data_path}"
        print("Fault injection finished, total spent time:", clock, " - Saving final results on:",
              final_injection_data_path)
        profile_df.to_csv(final_injection_data_path, sep=";", index=False)


if __name__ == '__main__':
    main()

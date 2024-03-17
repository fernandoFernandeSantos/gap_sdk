#!/usr/bin/python3
import filecmp
import os.path
import shutil
from typing import Union

import parameters
import pandas as pd
import numpy as np

import common

PROBLEMS_LOGGING_FILE = "injection.log"


def generate_next_offset_to_inject_memory(memory_level: str) -> int:
    bins, hist_norm = parameters.l1_double_cell_bins, parameters.l1_double_cell_hist_norm
    if memory_level == "L2":
        bins, hist_norm = parameters.l2_double_cell_bins, parameters.l2_double_cell_hist_norm

    return np.random.choice(bins[:-1], size=1, p=hist_norm)[0]


def get_random_value(percent: float, index: int, values: list):
    # Calculate the number of values to select from the list
    num_values = len(values)
    # Generate random index based on the specified percentage
    if np.random.rand() < percent:
        # Select index with 95% probability
        return values[index]
    else:
        # Select random index different from the given index with 5% probability
        random_index = np.random.randint(num_values)
        while random_index == index:
            random_index = np.random.randint(num_values)
        return values[random_index]


def create_injection_mask(output_register_val: int, output_register_byte_size: int,
                          fault_model: common.FaultModel,
                          memory_offset: int = None, memory_size: int = None) -> [int, int]:
    # size * byte size
    bit_size = output_register_byte_size * 8
    half_bit_size = bit_size // 2
    next_offset_double_cell = 0
    base_string = ['0'] * bit_size
    # Double bit flip is only valid for memory
    if fault_model in [common.FaultModel.SINGLE_BIT_FLIP, common.FaultModel.DOUBLE_CELL_FLIP]:
        random_bit = np.random.randint(0, bit_size)
        base_string[random_bit] = '1'
    elif fault_model == common.FaultModel.RANDOM_VALUE:
        base_string = list(map(str, np.random.randint(0, 2, bit_size).tolist()))
    elif fault_model == common.FaultModel.ZERO_VALUE:
        base_string = f'{output_register_val:0{bit_size}b}'
    elif fault_model == common.FaultModel.HALF_LOWER_BITS:
        half_base_string = list(map(str, np.random.randint(0, 2, half_bit_size).tolist()))
        base_string[:half_bit_size] = half_base_string
    elif fault_model == common.FaultModel.HALF_HIGHER_BITS:
        half_base_string = list(map(str, np.random.randint(0, 2, half_bit_size).tolist()))
        base_string[half_bit_size:] = half_base_string
    elif fault_model == common.FaultModel.MEMORY_CELL_BASED_ON_BEAM:
        # first select if it is one or two bit flips
        single_or_double_list = [1, 2]
        if memory_size <= (64 * 1024):
            single_or_double = get_random_value(percent=0.858, index=0, values=single_or_double_list)
            memory_level = "L1"
        else:
            single_or_double = get_random_value(percent=0.753, index=0, values=single_or_double_list)
            memory_level = "L2"

        random_bit = np.random.randint(0, bit_size)
        base_string[random_bit] = '1'
        if single_or_double == 2:
            for _ in range(3):  # try 3 times
                next_offset_double_cell = generate_next_offset_to_inject_memory(memory_level=memory_level)
                if next_offset_double_cell + memory_offset <= memory_size:
                    break
            else:
                with open(PROBLEMS_LOGGING_FILE, "a") as fp:
                    fp.write(f"Not possible to find a suitable offset: {memory_offset} | "
                             f"{memory_size} | {next_offset_double_cell}")
    elif fault_model == common.FaultModel.INSTRUCTION_OUTPUT_95PCT_SINGLE:
        single_or_random_list = [1, 2]
        single_or_random = get_random_value(percent=0.95, index=0, values=single_or_random_list)
        # Single bit flip
        if single_or_random == 1:
            random_bit = np.random.randint(0, bit_size)
            base_string[random_bit] = '1'
        else:
            base_string = list(map(str, np.random.randint(0, 2, bit_size).tolist()))

    # Just put the mask to inject the faults
    return int("".join(base_string), 2), next_offset_double_cell


def kill_simulator_after_injection():
    kill_program_list = ["gapy", "gvsoc_launcher_debug"]
    # The force killing is necessary here
    for cmd in kill_program_list:
        os.system(f"pkill -9 -f {cmd} && killall -9 {cmd}")


def verify_output(app_logs_path: str, error_code: common.DUEType,
                  injection_log_file: str, stderr_file: str, stdout_file: str,
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
        return False, False, "GVSOC_CRASHED_BEFORE_OUTPUT_READY", False

    golden_stdout_file = f"{app_logs_path}/{parameters.DEFAULT_GOLDEN_STDOUT_FILE}"
    golden_stderr_file = f"{app_logs_path}/{parameters.DEFAULT_GOLDEN_STDERR_FILE}"

    stdout_copy_file = f"{os.path.dirname(stdout_file)}/stdout_save.txt"
    shutil.copyfile(stdout_file, stdout_copy_file)
    with open(stdout_file, errors='ignore') as fp:
        lines_stdout = fp.readlines()
    with open(stdout_file, "w") as out_fp:
        for line in lines_stdout:
            if "FAULT_INJECTED_HERE" not in line:
                out_fp.write(line)

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


def inject_sample_faults_iter_rows(df: pd.DataFrame, app_name: str, app_parameters: dict,
                                   num_injections_per_run: int, fault_model: common.FaultModel,
                                   fault_injection_site: str) -> list:
    default_app_path = f"{parameters.GVSOCFI_LOGS_DIR}/{app_name}"
    app_logs_path_fault_model_and_site = f"{default_app_path}/{fault_model}_{fault_injection_site}"

    injection_data = list()
    for injection_it, (index, row) in enumerate(df.iterrows()):
        inj_clock = common.Timer()
        inj_clock.tic()
        injection_logs_path = f"{app_logs_path_fault_model_and_site}/inj-{injection_it}"
        # Create/Clean the output path
        common.execute_command(command=f"mkdir -p {injection_logs_path}")
        common.execute_command(command=f"rm {injection_logs_path}/*")

        # Inject the fault
        run_cmd = app_parameters["run_script"]
        injection_info_file = f"{injection_logs_path}/{parameters.GVSOCFI_INJECTION_IN_FILE}"
        injection_log_file = f"{injection_logs_path}/{parameters.GVSOCFI_INJECTION_OUT_FILE}"
        stdout_file = f"{injection_logs_path}/{parameters.DEFAULT_STDOUT_FILE}"
        stderr_file = f"{injection_logs_path}/{parameters.DEFAULT_STDERR_FILE}"

        # Profile the application
        set_environment_vars = [(fault_injection_site, str(common.RunMode.INST_INJECTOR)),
                                ("GVSOCFI_INJECTION_IN_FILE", injection_info_file),
                                ("GVSOCFI_INJECTION_OUT_FILE", injection_log_file),
                                ("STDOUT_FILE", stdout_file),
                                ("STDERR_FILE", stderr_file)]

        row_dict = write_fault_injection_information_file(fault_model=fault_model,
                                                          injection_info_file=injection_info_file,
                                                          num_injections_per_run=num_injections_per_run, row=row,
                                                          fault_injection_site=fault_injection_site)

        timeout = app_parameters["expected_run_time"] * parameters.TIMEOUT_THRESHOLD
        # default files
        exec_stdout, exec_stderr, error_code = common.execute_gvsoc(
            command=run_cmd,
            gapuino_source_script=parameters.GAPUINO_SOURCE_SCRIPT,
            gvsoc_fi_env=set_environment_vars, timeout=timeout
        )
        sdc, due, outcome, was_fault_injected = verify_output(
            app_logs_path=default_app_path,
            error_code=error_code,
            injection_log_file=injection_log_file,
            stdout_file=stdout_file, stderr_file=stderr_file,
            exec_stdout=exec_stdout, exec_stderr=exec_stderr
        )

        row_dict["SDC"], row_dict["DUE"] = sdc, due
        row_dict["was_fault_injected"] = was_fault_injected
        row_dict["error_code"] = str(error_code)

        row_dict["inst_label"] = row["label"] if fault_injection_site == common.INSTRUCTION_OUTPUT else "mem"
        injection_data.append(row_dict)
        # clean the system before continue
        kill_simulator_after_injection()
        inj_clock.toc()
        print("Fault num:", injection_it, "Fault Model:", fault_model, "Fault site:", fault_injection_site,
              "App:", app_name, "Outcome:", outcome, "exec time:", inj_clock)
    return injection_data


def write_fault_injection_information_file(fault_model: common.FaultModel, injection_info_file: str,
                                           num_injections_per_run: int, row: pd.Series, fault_injection_site: str):
    # Put the contents in the info file
    row_dict = dict(fault_model=fault_model)
    with open(injection_info_file, "w") as inj_fp:
        if fault_injection_site in common.INSTRUCTION_OUTPUT:
            row_dict["gvsoc_fi_mask"], _ = create_injection_mask(output_register_val=row["out_reg0"],
                                                                 output_register_byte_size=row["size"],
                                                                 fault_model=fault_model)
            lines_to_write = [num_injections_per_run, row["iteration_counter_gvsocfi"], row_dict["gvsoc_fi_mask"],
                              row["out_reg0"], row["cpu_config_mhartid"], row["label"]]
        elif fault_injection_site == common.MEMORY:
            row_dict["gvsoc_fi_mask"], row_dict["next_offset_double_cell"] = create_injection_mask(
                output_register_val=row["mem_data0"],
                output_register_byte_size=1, fault_model=fault_model, memory_offset=row["offset"],
                memory_size=row["total_memory_size"]
            )
            # row_dict["second_gvsoc_fi_mask"], row_dict["next_offset_double_cell"] = create_injection_mask(
            #     output_register_val=row["mem_data1"],
            #     output_register_byte_size=1,
            #     fault_model=fault_model
            # )
            is_double_cell_upset = 0
            if (fault_model == common.FaultModel.DOUBLE_CELL_FLIP or (
                    fault_model == common.FaultModel.MEMORY_CELL_BASED_ON_BEAM
                    and row_dict["next_offset_double_cell"] != 0)):
                is_double_cell_upset = 1

            lines_to_write = [
                row["mem_iteration_counter_gvsocfi"], row_dict["gvsoc_fi_mask"], row["mem_data0"],
                row["offset"], row["operation_size"], row["total_memory_size"], is_double_cell_upset,
                row_dict["next_offset_double_cell"]
            ]

        inj_fp.writelines("\n".join(map(str, lines_to_write)))
    return row_dict


def main():
    args = common.parse_args()
    fault_injection_site = args.fault_site
    fault_models = [common.FaultModel.INSTRUCTION_OUTPUT_95PCT_SINGLE]
    if fault_injection_site == common.MEMORY:
        fault_models = [common.FaultModel.MEMORY_CELL_BASED_ON_BEAM]

    clock = common.Timer()
    clock.tic()
    # Profiling all the apps on parameters.apps_parameters
    for app_name, app_parameters in parameters.APP_PARAMETERS.items():
        # Create the logdir specific for the app
        app_logs_path = f"{parameters.GVSOCFI_LOGS_DIR}/{app_name}"
        profile_app_file = app_logs_path
        profile_app_file += "/" + parameters.PROFILER_FILE.format(injection_site=fault_injection_site)
        profiler_fields = parameters.PROFILER_FIELDS_MEM_INJECTION
        if fault_injection_site == common.INSTRUCTION_OUTPUT:
            profiler_fields = parameters.PROFILER_FIELDS_INST_INJECTION
        profile_df = pd.read_csv(profile_app_file, sep=";", names=profiler_fields, index_col=False)

        # Create the path if it was not created yet
        # injection_logs_path = f"{app_logs_path}/{parameters.APP_INJECTION_FOLDER_BASE}"
        common.execute_command(command=f"mkdir -p {app_logs_path}/")

        # Remove the instructions that do not have output
        # Select instructions that have only one output register
        if fault_injection_site == common.INSTRUCTION_OUTPUT:
            # TODO: Add fault injection for more than one output register
            profile_df = profile_df[profile_df["nb_out_reg"] == 1]

        random_generator = np.random.MT19937()
        # Set the number of injections, if the NUM_INJECTIONS < profile rows then allow repetitions of inj sites
        assert parameters.NUM_INJECTIONS <= profile_df.shape[0], (f"NUM_INJECTIONS must be lower or equal"
                                                                  f" profiled instructions:"
                                                                  f" {parameters.NUM_INJECTIONS} > "
                                                                  f"{profile_df.shape[0]}")

        # Get the golden values, save them for future analysis
        common.execute_gvsoc(command=app_parameters["run_script"],
                             gapuino_source_script=parameters.GAPUINO_SOURCE_SCRIPT,
                             gvsoc_fi_env=[("STDOUT_FILE", f"{app_logs_path}/{parameters.DEFAULT_GOLDEN_STDOUT_FILE}"),
                                           ("STDERR_FILE", f"{app_logs_path}/{parameters.DEFAULT_GOLDEN_STDERR_FILE}")])
        # Inject sampled faults for each fault model
        final_data_list = list()
        for fault_model in fault_models:
            sampled_faults_df = profile_df.sample(n=parameters.NUM_INJECTIONS, random_state=random_generator,
                                                  replace=False, ignore_index=True)

            # profile_df = profile_df.apply(inject_sample_faults, args=(app_name, app_parameters), axis="columns")
            num_injections_per_run = 1  # 2 if common.FaultModel.DOUBLE_BIT_FLIP_2REG else 1
            fi_data_list = inject_sample_faults_iter_rows(df=sampled_faults_df, app_name=app_name,
                                                          app_parameters=app_parameters,
                                                          num_injections_per_run=num_injections_per_run,
                                                          fault_model=fault_model,
                                                          fault_injection_site=fault_injection_site)
            final_data_list.extend(fi_data_list)

        # Save the results
        final_injection_data_path = parameters.FINAL_INJECTION_DATA.format(fault_num=parameters.NUM_INJECTIONS,
                                                                           fault_site=fault_injection_site)
        final_injection_data_path = f"{app_logs_path}/{final_injection_data_path}"
        fi_df = pd.DataFrame(final_data_list)
        fi_df.to_csv(final_injection_data_path, sep=";", index=False)
    clock.toc()
    print("Fault injection finished, total spent time:", clock)


if __name__ == '__main__':
    main()

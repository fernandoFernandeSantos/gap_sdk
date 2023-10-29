#!/usr/bin/python3
import parameters
import common


def main():
    # Check if output logs path exists
    common.execute_command(command=f"mkdir -p {parameters.GVSOCFI_LOGS_DIR}")

    # Profiling all the apps on parameters.apps_parameters
    for app_name, app_parameters in parameters.APP_PARAMETERS.items():
        # Create the logdir specific for the app
        app_logs_path = f"{parameters.GVSOCFI_LOGS_DIR}/{app_name}"
        profile_app_file = f"{app_logs_path}/{parameters.PROFILER_FILE}"
        # The profile file is only opened on append mode, so remove it before continues
        common.execute_command(command=f"rm {profile_app_file}")
        # First check if the log paths exists
        common.execute_command(command=f"mkdir -p {app_logs_path}")
        print("Profiling:", app_name, "Profile data will be saved at:", profile_app_file)
        # Profile the application
        set_environment_vars = [("GVSOCFI_RUN_TYPE", str(common.RunMode.PROFILER)),
                                ("GVSOCFI_PROFILER_FILE", profile_app_file),
                                ("STDOUT_FILE", parameters.GVSOCFI_PROFILER_OUTPUT),
                                ("STDERR_FILE", parameters.GVSOCFI_PROFILER_OUTPUT)]

        common.execute_gvsoc(command=app_parameters["run_script"],
                             gapuino_source_script=parameters.GAPUINO_SOURCE_SCRIPT, gvsoc_fi_env=set_environment_vars)
        print("Profile finished.")


if __name__ == '__main__':
    main()

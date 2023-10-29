import os
import shlex
import signal
import subprocess
from enum import Enum
from typing import Tuple, Optional, Union
import time


class FaultModel(Enum):
    SINGLE_BIT_FLIP = 0
    DOUBLE_BIT_FLIP = 1
    ZERO_VALUE = 2
    RANDOM_VALUE = 3

    def __str__(self) -> str:
        """Override the str method
        :return: the name of the enum as string
        """
        return self.name


class RunMode(Enum):
    PROFILER = 0
    INST_INJECTOR = 1

    def __str__(self) -> str:
        """Override the str method
        :return: the name of the enum as string
        """
        return str(self.value)


class DUEType(Enum):
    # I create an ENUM just in case other types
    NO_DUE = 0
    GENERAL_DUE = 1
    TIMEOUT_ERROR = 2
    POSSIBLE_GVSOC_CRASH = 3

    def __str__(self) -> str:
        """Override the str method
        :return: the name of the enum as string
        """
        return str(self.name)


class Timer:
    time_measure = 0

    def tic(self):
        self.time_measure = time.time()

    def toc(self):
        self.time_measure = time.time() - self.time_measure

    @property
    def diff_time(self):
        return self.time_measure

    def __str__(self):
        return f"{self.time_measure:.2f}s"

    def __repr__(self):
        return str(self)


def execute_command(command: str, verbose: bool = False) -> Tuple[str, str]:
    """ this is only used for common commands not suitable for gvsoc    """
    command = shlex.split(command)
    p = subprocess.Popen(command, env=os.environ, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         universal_newlines=True)
    out, err = p.communicate()
    if verbose:
        print("STDOUT:", out)
        print("STDERR:", err)
    p.terminate()  # send sigterm, or ...
    p.kill()  # send sigkill
    return out, err


def is_timeout(pr: subprocess.Popen, timeout: float):
    # check if the process is active every 'factor' sec for timeout threshold
    factor = 0.5
    return_code = None
    to_th = timeout / factor
    while to_th > 0:
        return_code = pr.poll()
        if return_code is not None:
            break
        to_th -= 1
        time.sleep(factor)

    if to_th == 0:
        os.killpg(pr.pid, signal.SIGINT)  # pr.kill()
        return True, pr.poll()
    else:
        return False, return_code


def execute_gvsoc(command: str, gapuino_source_script: str, gvsoc_fi_env: Optional[Union[dict, list]] = None,
                  timeout: float = 60) -> Tuple[Union[None, str], Union[None, str], DUEType]:
    env_vars_str, _ = execute_command(command=f"env -i bash -c 'source {gapuino_source_script} && env'", )
    current_env_vars = os.environ.copy()
    for line in env_vars_str.split("\n"):
        (key, _, value) = line.strip().partition("=")
        current_env_vars[key] = value
    if gvsoc_fi_env:
        current_env_vars.update(gvsoc_fi_env)

    command = shlex.split(command)

    process = subprocess.Popen(command, env=current_env_vars, shell=True, executable='/bin/bash', preexec_fn=os.setsid,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    timeout_flag, return_code = is_timeout(pr=process, timeout=timeout)
    out, err = process.communicate()
    process.wait()
    process.terminate()  # send sigterm
    process.kill()  # send sigkill

    due_type = DUEType.NO_DUE
    if timeout_flag:
        due_type = DUEType.TIMEOUT_ERROR
    elif err:
        due_type = DUEType.POSSIBLE_GVSOC_CRASH

    return out, err, due_type

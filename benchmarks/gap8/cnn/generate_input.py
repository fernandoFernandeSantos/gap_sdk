#!/usr/bin/python3

import numpy as np


def generate_conv_input():
    wic = 100
    hic = 100
    high = 3
    low = -high
    filter_array = np.random.randint(low=low, high=high, size=(5, 5))
    in_array = np.random.randint(low=low, high=high, size=(wic, hic))
    with open("inputs_maxpool.h", "w") as inputs_fp:
        inputs_fp.write("#ifndef __INPUTS_H__\n#define __INPUTS_H__\n")
        for (array, var_name) in [(filter_array, "filter_array"),
                                  (in_array, "input_array")]:
            inputs_fp.write(
                f"signed char {var_name}[] = " + "{\n"
            )

            for line in array:
                inputs_fp.write("\t" + ", ".join(map(str, line)) + ",")
                inputs_fp.write("\n")
            inputs_fp.write("};\n\n")
        inputs_fp.write("#endif\n")


def generate_linear_input():
    wil = 1024
    hil = 16
    high = 3
    low = -high

    filter_array = np.random.randint(low=low, high=high, size=wil * hil)
    in_array = np.random.randint(low=low, high=high, size=wil)
    with open("inputs_maxpool.h", "w") as inputs_fp:
        inputs_fp.write("#ifndef __INPUTS_H__\n#define __INPUTS_H__\n")
        for (array, var_name) in [(filter_array, "filter_array"),
                                  (in_array, "input_array")]:
            inputs_fp.write(
                f"signed char {var_name}[] = " + "{\n"
            )

            for line in array:
                inputs_fp.write(f"{line},")
                # inputs_fp.write("\n")
            inputs_fp.write("};\n\n")
        inputs_fp.write("#endif\n")


def generate_maxpool_input():
    wi = 112
    hi = 112
    high = 127
    low = 1

    in_array = np.random.randint(low=low, high=high, size=wi * hi)
    with open("inputs_maxpool.h", "w") as inputs_fp:
        inputs_fp.write("#ifndef __INPUTS_H__\n#define __INPUTS_H__\n")
        inputs_fp.write(
            f"signed char input_array[] = " + "{\n"
        )

        for line in in_array:
            inputs_fp.write(f"{line},")
            # inputs_fp.write("\n")
        inputs_fp.write("};\n\n")
        inputs_fp.write("#endif\n")

# generate_conv_input()
# generate_linear_input()
generate_maxpool_input()
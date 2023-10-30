#!/usr/bin/python3
import pandas as pd
import sys

sys.path.insert(0, '../')
import parameters

APPS = {
    "Mnist"
}


def main():
    for app in APPS:
        csv_path = f"../logs/{app}/{parameters.PROFILER_FILE}"
        df = pd.read_csv(csv_path, sep=";", names=parameters.PROFILER_FIELDS)
        df = df[df["nb_out_reg"] > 0]
        print(df)


if __name__ == '__main__':
    main()

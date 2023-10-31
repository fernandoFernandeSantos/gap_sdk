#!/usr/bin/python3

import pandas as pd


def main():
    df = pd.read_csv("../logs/gvsocfi_parsed_fi_database_2000.csv", delimiter=";")
    df["DUE"] = df["DUE"].astype(int)

    # df = df.apply(define_sdc_due_mask, axis="columns")
    # gvsoc_crash = df[df["was_fault_injected"] & (df["GVSOC_crash"] == True)]
    filtered = df[df["was_fault_injected"] & (df["GVSOC_crash"] == False)]

    valid_faults = filtered.shape[0]

    grouped = filtered.groupby(["app"]).sum()[
        ["SDC", "DUE", "was_fault_injected", "test_success_found", "CRITICAL_SDC", "GVSOC_crash"]]
    grouped["AVF SDC"] = grouped["SDC"] / grouped["was_fault_injected"]
    grouped["AVF CRITICAL_SDC"] = grouped["CRITICAL_SDC"] / grouped["was_fault_injected"]
    grouped["AVF DUE"] = grouped["DUE"] / grouped["was_fault_injected"]
    print(grouped)
    # filtered = df[df["error_code"] != "POSSIBLE_GVSOC_CRASH"]
    # sdcs = filtered[(filtered["DUE"] == False) & (filtered["SDC"] == 1)]
    # masked = filtered[(filtered["DUE"] == False) & (filtered["SDC"] == 0)]


if __name__ == '__main__':
    main()

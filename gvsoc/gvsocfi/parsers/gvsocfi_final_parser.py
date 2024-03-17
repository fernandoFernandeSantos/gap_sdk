#!/usr/bin/python3
import math
import pandas as pd
import sys

from gvsocfi_pre_parser import ALL_STD_ERRORS

sys.path.insert(0, '../')

import common
import parameters

PAPER_DIR = "/home/fernando/git_research/iolts_2024"
FAULT_MODELS_PRETTY_NAME = {
    "RANDOM_VALUE": "Random", "SINGLE_BIT_FLIP": "Single Bit",
    "HALF_HIGHER_BITS": "Higher Bits", "HALF_LOWER_BITS": "Lower Bits",
    "DOUBLE_CELL_FLIP": "Double Bit", "ZERO_VALUE": "Zero",
    "MEMORY_CELL_BASED_ON_BEAM": "Mem",
    "INSTRUCTION_OUTPUT_95PCT_SINGLE": "Inst"
}

LAYER_NAMES = {
    "1C0": "Convolution 1", "1C1": "Convolution 1",
    "1M0": "Maxpool 1", "1M1": "Maxpool 1",
    "2C0": "Convolution 2",
    "2M0": "Maxpool 2", "3L0": "Linear", "3R0": "Linear",
    # 'Injected After Finishing': 'Injected After Finishing'
}


def post_process_gvsoc_crashes(row):
    if row["error_code"] == "POSSIBLE_GVSOC_CRASH":
        row["SDC"] = 0
        row["DUE"] = 1

    return row


def preparse_df(csv_file_path):
    df = pd.read_csv(csv_file_path, delimiter=";")
    df["DUE"] = df["DUE"].apply(convert_values)
    df["SDC"] = df["SDC"].apply(convert_values)
    # df = df[
    #     ~(df["error_code"] != "POSSIBLE_GVSOC_CRASH")
    #     & df["was_fault_injected"]
    #     ]
    df = df.apply(post_process_gvsoc_crashes, axis="columns")
    # print(df[(df["DUE"] == 0) & (df["error_code"] == "POSSIBLE_GVSOC_CRASH")])
    # print(df[(df["error_code"] == "POSSIBLE_GVSOC_CRASH") & ~df["was_fault_injected"]])
    df["MASKED"] = ((df["SDC"] == 0) & (df["DUE"] == 0)).astype(int)
    return df


def parse_cnn_ops():
    csv_file_path = "data/gvsocfi_parsed_fi_database_2000.csv"
    df = preparse_df(csv_file_path)

    # benchmarks_order = ['convsequential', 'convparallel', 'linearsequential', 'linearparallel', 'maxpoolsequential',
    #                     'maxpoolparallel']
    benchmarks_order = ['convparallel', 'linearparallel', 'maxpoolparallel']

    df["fault_site"] = df["fault_site"].apply(lambda x: "Mem" if x == common.MEMORY else "Inst")
    df["fault_model"] = df["fault_model"].apply(lambda x: FAULT_MODELS_PRETTY_NAME[x])

    avf_overall = df[["benchmark", "fault_model", "SDC", "DUE", "MASKED", "error_format", "fault_site"]].groupby(
        ["fault_site", "benchmark"]).sum()

    # all_events = ["SDC", "DUE", "MASKED"]
    avf_no_fault_site = avf_overall.groupby(["benchmark"]).sum()
    avf_no_fault_site = avf_no_fault_site.reindex(labels=benchmarks_order)

    # for event in all_events:
    #     avf_overall[f"AVF {event}"] = avf_overall[event] / avf_overall[all_events].sum(axis="columns")

    avf_overall = avf_overall.sort_index(level=["fault_site", "benchmark"])  # , "fault_model"])
    avf_overall = avf_overall.reindex(level="benchmark", labels=benchmarks_order)
    avf_no_fault_site = pd.concat({'Overall': avf_no_fault_site}, names=['fault_site'])
    avf_overall = pd.concat([avf_overall, avf_no_fault_site])
    avf_overall = (
        avf_overall
        .reorder_levels(["benchmark", "fault_site"])
        .sort_index(level=["benchmark", "fault_site"])
        .reindex(
            level="benchmark", labels=benchmarks_order)
    )
    # TODO: The number of injections from the instructions should be weighted by the number of

    # Calc error formats
    error_formats = df[["fault_site", "benchmark", "fault_model", "error_format"]]
    error_formats = error_formats[error_formats["error_format"] != "MASKED"]
    error_formats["count"] = 1
    error_formats = (
        error_formats
        .groupby(["fault_site", "benchmark", "fault_model", "error_format"])
        .sum()
        .unstack()
        .fillna(0)
        .droplevel(level=0, axis="columns")
        .reindex(level="benchmark", labels=benchmarks_order)
    )
    # all_formats = ["LINE", "SINGLE", "SQUARE"]
    # for err_format in all_formats:
    #     error_formats[f"%{err_format}"] = error_formats[err_format] / error_formats[all_formats].sum(axis="columns")

    error_formats = error_formats.sort_index(level=["fault_site", "benchmark", "fault_model"])
    error_formats = error_formats.reindex(level="benchmark", labels=benchmarks_order)
    error_formats_no_fault_sites = error_formats.groupby(["benchmark"]).sum()
    error_formats_no_fault_sites = error_formats_no_fault_sites.reindex(labels=benchmarks_order)
    return avf_overall, avf_no_fault_site, error_formats, error_formats_no_fault_sites


def convert_values(r):
    if r in [0, "0", "False"]:
        return 0
    elif r in [1, "1", "True"]:
        return 1
    else:
        raise ValueError(str(r))


def parse_crash_str(r):
    for std_err in ALL_STD_ERRORS:
        if std_err in r:
            return std_err

    return None


def parse_mnist():
    df = preparse_df(csv_file_path="data/gvsocfi_parsed_fi_database_10000_mnist.csv")
    df = df[df["benchmark"] == "Mnist"]
    df["crash_err"] = df["crash_str"].fillna('').apply(parse_crash_str)
    due_sources = df["crash_err"].value_counts() / df["crash_err"].value_counts().sum()
    print(due_sources)
    # df["injected_layer"] = df["injected_layer"].fillna('Injected After Finishing')

    df["layer"] = df.apply(lambda r: LAYER_NAMES[r["injected_layer"]], axis="columns")

    df["fault_model"] = df["fault_model"].apply(lambda x: FAULT_MODELS_PRETTY_NAME[x])

    reduced_df = df[["benchmark", "fault_model", "SDC", "Critical_SDC", "DUE", "MASKED", "fault_site", "layer"]]
    avf_fault_model = reduced_df.groupby(["layer", "fault_model"]).sum()
    avf_per_layer = reduced_df.groupby(["layer"]).sum()
    # avf_per_layer.loc["Linear"] += avf_per_layer.loc["Injected After Finishing"]
    # avf_per_layer = avf_per_layer.drop(index="Injected After Finishing")
    assert (avf_per_layer.sum(axis="columns") - avf_per_layer["Critical_SDC"]).sum() == 20000, f"Pau:{avf_per_layer}"
    avf_memory_per_layer = reduced_df[reduced_df["fault_model"] == "Mem"].groupby(
        ["layer", "benchmark"]).sum()

    avf_inst_per_layer = reduced_df[reduced_df["fault_model"] == "Inst"].groupby(["layer"]).sum()

    return avf_per_layer, avf_fault_model, avf_memory_per_layer, avf_inst_per_layer


def calc_err(row, event):
    return (1.96 * row[f"Cross Section {event}"]) / math.sqrt(row[f"{event}"])


def cross_section_prediction(avf_memory_per_layer, avf_inst_per_layer, cnn_op_avf_overall):
    # The values are extracted from MnistKernels.c on GreenWaves example
    # As the operators are fused I used the following reasoning:
    # Conv 1 has an input image of 28x28 + filters 800 + bias 32 ==> output of BASED ON MAXPOOL OUTPUT
    # MaxPool 1 has an output of 24x24x32 given the fact that Maxpool is 2x2, the input is (24x24x32)x4
    # Conv 2 has an input of 24*24*32 (aka, output of maxpool) + filters 51199 + bias 64
    # MaxPool 2 has an output of 4x4x64, so the input is (4x4x64) 4
    # Linear has an input of 4x4x64 and outputs 10
    mnist_parameters_size = pd.Series({
        "Convolution 1": 28 * 28 + 800 + 32,
        "Maxpool 1": 24 * 24 * 32 * 4,
        "Convolution 2": 24 * 24 * 32 + 51199 + 64,
        "Maxpool 2": 4 * 4 * 64 * 4,
        "Linear": 4 * 4 * 64 + 10
    })
    mnist_parameters_size_norm = mnist_parameters_size / mnist_parameters_size.sum()
    # For each short int
    mnist_parameters_size *= 2
    mnist_parameters_size.to_csv("/tmp/mnist_size.csv")
    print(f"MEM SIZE:{mnist_parameters_size.sum() / 1024}")
    microbenchmarks_sizes = pd.Series({
        # Always byte
        # filter_array_size size 25
        # input_array_size size 10000
        # golden_array_size size 9216
        "Convolution": 25 + 10000 + 9216,
        # filter_array_size size 16384
        # input_array_size size 1024
        # golden_array_size size 16
        "Linear": 16384 + 1024 + 16,
        # input_array_size size 12544
        # golden_array_size size 3136
        "Maxpool": 12544 + 3136
    })

    # CNN layers
    cnn_cs_df = pd.read_excel("~/git_research/nsrec_2023/data/gap8_cross_section_sep2022_tmp.xlsx", sheet_name="CNNOps")
    cnn_cs_df = cnn_cs_df.drop(columns=['Unnamed: 0']).groupby(['Micro', 'Exec type']).sum()
    # MEM
    mem_cs_df = pd.read_excel("~/git_research/nsrec_2023/data/gap8_cross_section_sep2022_tmp.xlsx", sheet_name="Mem")
    mem_cs_df = mem_cs_df.drop(columns=['Unnamed: 0']).groupby(['Micro']).sum()
    mem_cs_df.loc["L1", "Size"] = 62 * 1024
    mem_cs_df.loc["L2", "Size"] = 448 * 1024

    for event in ["SDC", "DUE"]:
        cnn_cs_df[f"Cross Section {event}"] = cnn_cs_df[f"{event}"] / cnn_cs_df["Fluency(Flux * $AccTime)"]
        cnn_cs_df[f"Err {event}"] = cnn_cs_df.apply(calc_err, args=(event,), axis="columns")

        mem_cs_df[f"Cross Section {event}"] = mem_cs_df[f"{event}"] / mem_cs_df["Fluency(Flux * $AccTime)"]
        mem_cs_df[f"Err {event}"] = mem_cs_df.apply(calc_err, args=(event,), axis="columns")
        mem_cs_df[f"Cross Section {event} Byte"] = mem_cs_df[f"Cross Section {event}"] / mem_cs_df["Size"]
        mem_cs_df[f"Err {event} Byte"] = mem_cs_df[f"Err {event}"] / mem_cs_df["Size"]

    mem_cs_df = mem_cs_df[['Cross Section SDC Byte', 'Cross Section DUE Byte', 'Err SDC Byte', 'Err DUE Byte']]

    # ========= Memory AVF
    memory_avf = avf_memory_per_layer[["SDC", "DUE", "Critical_SDC", 'MASKED']].droplevel(level="benchmark")
    memory_avf["SDC"] -= memory_avf["Critical_SDC"]
    # memory_avf = memory_avf.drop("Injected After Finishing")
    memory_avf = memory_avf.div(memory_avf.sum(axis="columns"), axis="rows")

    # ==================================================================================================================
    # Estimation using memory
    memory_estimation = pd.DataFrame({
        "SDC": mem_cs_df["Cross Section SDC Byte"]["L2"] * memory_avf["SDC"] * mnist_parameters_size,
        "Critical SDC": mem_cs_df["Cross Section SDC Byte"]["L2"] * memory_avf["Critical_SDC"] * mnist_parameters_size,
        "DUE": mem_cs_df["Cross Section DUE Byte"]["L2"] * memory_avf["DUE"] * mnist_parameters_size,
        "Err SDC": mem_cs_df["Err SDC Byte"]["L2"] * memory_avf["SDC"] * mnist_parameters_size,
        "Err Critical SDC": mem_cs_df["Err SDC Byte"]["L2"] * memory_avf["Critical_SDC"] * mnist_parameters_size,
        "Err DUE": mem_cs_df["Err DUE Byte"]["L2"] * memory_avf["DUE"] * mnist_parameters_size,
    })
    memory_estimation.loc["Sum"] = memory_estimation.sum()

    # ==================================================================================================================
    # Estimation using instruction
    # ========= CNN OPS AVF
    avf_per_layer = avf_inst_per_layer[["SDC", "DUE", "Critical_SDC", 'MASKED']]
    avf_per_layer["SDC"] -= avf_per_layer["Critical_SDC"]
    # layer_avf = layer_avf.drop("Injected After Finishing")
    avf_per_layer = avf_per_layer.div(avf_per_layer.sum(axis="columns"), axis="rows")
    avf_per_layer = avf_per_layer.rename(index={"MaxPooling 1": "Maxpool 1", "MaxPooling 2": "Maxpool 2"})

    # =================== Calc the micro op cross-section
    parallel_cs_beam = (
        cnn_cs_df
        .loc[pd.IndexSlice[:, "Parallel"], ["Cross Section SDC", "Cross Section DUE", "Err SDC", "Err DUE"]]
        .droplevel(level="Exec type")
    )

    # Gambiarra to find proportions on micro benchmarks CS
    cnn_op_avf_overall = (
        cnn_op_avf_overall
        .copy()
        .loc[pd.IndexSlice[:, "Mem"], :]
        .rename(index={"convparallel": "Convolution", "linearparallel": "Linear", "maxpoolparallel": "Maxpool"})
        .droplevel(level="fault_site")
    )
    cnn_op_avf_overall = cnn_op_avf_overall.div(cnn_op_avf_overall.sum(axis="columns"), axis="index")
    cnn_op_estimated_mem_cs = pd.DataFrame({
        "SDC": microbenchmarks_sizes * mem_cs_df["Cross Section SDC Byte"]["L1"] * cnn_op_avf_overall["SDC"],
        "DUE": microbenchmarks_sizes * mem_cs_df["Cross Section SDC Byte"]["L1"] * cnn_op_avf_overall["DUE"]
    })
    parallel_cs_beam["SDC:mem_cs/all"] = 1 - (
            cnn_op_estimated_mem_cs["SDC"] / parallel_cs_beam["Cross Section SDC"])
    parallel_cs_beam["DUE:mem_cs/all"] = 1 - (
            cnn_op_estimated_mem_cs["DUE"] / parallel_cs_beam["Cross Section DUE"])

    # Renaming to multiply
    parallel_cs_beam.loc["Convolution 1"] = parallel_cs_beam.loc["Convolution"]
    parallel_cs_beam = parallel_cs_beam.rename(index={"Convolution": "Convolution 2"})
    parallel_cs_beam.loc["Maxpool 1"] = parallel_cs_beam.loc["Maxpool"]
    parallel_cs_beam = parallel_cs_beam.rename(index={"Maxpool": "Maxpool 2"})
    print(avf_per_layer)
    instruction_estimation = pd.DataFrame({
        "SDC":
            parallel_cs_beam["Cross Section SDC"] * avf_per_layer["SDC"] * mnist_parameters_size_norm *
            parallel_cs_beam["SDC:mem_cs/all"],
        "Critical SDC":
            parallel_cs_beam["Cross Section SDC"] * avf_per_layer["Critical_SDC"] * mnist_parameters_size_norm *
            parallel_cs_beam["SDC:mem_cs/all"],
        "DUE":
            parallel_cs_beam["Cross Section DUE"] * avf_per_layer["DUE"] * mnist_parameters_size_norm *
            parallel_cs_beam["DUE:mem_cs/all"],
        "Err SDC":
            parallel_cs_beam["Err SDC"] * avf_per_layer["SDC"] * mnist_parameters_size_norm *
            parallel_cs_beam["SDC:mem_cs/all"],
        "Err Critical SDC":
            parallel_cs_beam["Err SDC"] * avf_per_layer["Critical_SDC"] * mnist_parameters_size_norm *
            parallel_cs_beam["SDC:mem_cs/all"],
        "Err DUE":
            parallel_cs_beam["Err DUE"] * avf_per_layer["DUE"] * mnist_parameters_size_norm *
            parallel_cs_beam["DUE:mem_cs/all"],
    })
    instruction_estimation.loc["Sum"] = instruction_estimation.sum()
    print(instruction_estimation)
    return instruction_estimation, memory_estimation


def main():
    cnn_op_avf_overall, cnn_op_avf_no_fault_site, error_formats, error_formats_no_fault_sites = parse_cnn_ops()
    avf_per_layer, avf_fault_model, avf_memory_per_layer, avf_inst_per_layer = parse_mnist()

    cs_prediction_ops, cs_prediction_mem = cross_section_prediction(avf_memory_per_layer=avf_memory_per_layer,
                                                                    avf_inst_per_layer=avf_inst_per_layer,
                                                                    cnn_op_avf_overall=cnn_op_avf_overall)

    avf_fault_model = avf_fault_model.reindex(["Convolution 1", "Maxpool 1", "Convolution 2", "Maxpool 2", "Linear"],
                                              level="layer").unstack()

    with pd.ExcelWriter(f"{PAPER_DIR}/data/avf_tmp.xlsx") as writer:
        cnn_op_avf_overall.to_excel(writer, sheet_name="AVF")
        cnn_op_avf_no_fault_site.to_excel(writer, sheet_name="AVFNoFaultSites")
        error_formats.to_excel(writer, sheet_name="ErrorFormats")
        error_formats_no_fault_sites.to_excel(writer, sheet_name="ErrorFormatsNoFaultSites")

        avf_per_layer.to_excel(writer, sheet_name="MNIST_AVF_layer")
        avf_fault_model.to_excel(writer, sheet_name="MNIST_AVF_Layer+Fault_Model")

        cs_prediction_ops.to_excel(writer, sheet_name="CSPrediction")
        cs_prediction_mem.to_excel(writer, sheet_name="CSPredictionMem")


if __name__ == '__main__':
    main()

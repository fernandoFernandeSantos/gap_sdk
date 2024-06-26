//
// Created by fernando on 08/08/22.
//

#ifndef GVSOC_FAULT_INJECTION_HPP
#define GVSOC_FAULT_INJECTION_HPP

#include <string>
#include <fstream>

static inline void gvsocfi_fatal(const std::string &error, int line, const std::string &file) {
    throw std::runtime_error("GVSOCFI_ERROR:::" + error + ":::AT:" + file + ":" + std::to_string(line));
}

#define GVSOFI_FATAL(x) gvsocfi_fatal(x, __LINE__, __FILE__)

static std::size_t iteration_counter_gvsocfi = 0;


typedef enum {
    PROFILER = 0,
    INST_INJECTOR,
    GVSOCFI_RUN_TYPE_OPTIONS
} gvsocfi_run_type_t;


static void profiler(iss_t *iss_wrapper_instance, iss_insn_t *insn) {
    static auto profiler_output_file = std::string(std::getenv("GVSOCFI_PROFILER_FILE"));

    std::ofstream profiler_file_obj(profiler_output_file, std::ios::out | std::ios::app);
    if (profiler_file_obj.good()) {
        // comparing a tuple <internal counter, add, opcode, label, size> is enough
        // the internal counter is necessary to remove duplicate executions
        profiler_file_obj << iteration_counter_gvsocfi << ";"
                          << insn->decoder_item->u.insn.label << ";"
                          << insn->size << ";"
                          << iss_wrapper_instance->cpu.config.mhartid << ";";

        // maximum number of reg is always 3 but nb_out_reg and nb_in_reg says how many are used
        profiler_file_obj << insn->nb_out_reg;
        for (auto out_reg: insn->out_regs) {
            profiler_file_obj << ";" << out_reg;
        }
//        profiler_file_obj << insn->nb_in_reg << ";";
//        for (auto in_reg: insn->in_regs) {
//            profiler_file_obj << in_reg << ";";
//        }
        profiler_file_obj << "\n";
    } else {
        GVSOFI_FATAL("Not able to read the profiler file:" + profiler_output_file);
    }

}

#define MAX_MULTIPLE_FAULTS_NUM 3

struct InjectionInfo {
    std::size_t injection_counter = -1;
    int gvsoc_fi_mask = 0;
    int reg_val_before_from_file = 0;
    iss_reg_t cpu_config_mhartid = -1;
    std::string instruction_label = "";
    bool is_ready_to_inject = false;
};

static InjectionInfo select_injection_info(int mhartid, char *current_label, InjectionInfo *injection_data) {
    InjectionInfo current_inf;
    for (auto i = 0; i < MAX_MULTIPLE_FAULTS_NUM; i++) {
        auto &inj_inf = injection_data[i];
        if (inj_inf.injection_counter == iteration_counter_gvsocfi && inj_inf.cpu_config_mhartid == mhartid &&
            inj_inf.instruction_label == current_label) {
            return inj_inf;
        }
    }
    return {};
}

static void inst_injector(iss_t *iss_wrapper_instance, iss_insn_t *insn) {
    // File that contains the fault input parameters
    static auto injection_input_file = std::string(std::getenv("GVSOCFI_INJECTION_IN_FILE"));
    static auto injection_output_file = std::string(std::getenv("GVSOCFI_INJECTION_OUT_FILE"));

    /**
     * Read the tuple
     */
    static auto file_read = false;
    static InjectionInfo injection_data[MAX_MULTIPLE_FAULTS_NUM];
//    static std::size_t injection_counter = -1;
//    static auto gvsoc_fi_mask = insn->out_regs[0];
//    static auto reg_val_before_from_file = insn->out_regs[0];
//    static auto cpu_config_mhartid = iss_wrapper_instance->cpu.config.mhartid;
//    static auto instruction_label = std::string("");
//    static auto double_injection_counter = -1;

    //load the file only once
    if (!file_read) {
        std::ifstream injection_input_file_stream(injection_input_file);
        if (injection_input_file_stream.good()) {
            auto num_of_injections = 0u;
            injection_input_file_stream >> num_of_injections;
            if (num_of_injections > MAX_MULTIPLE_FAULTS_NUM) {
                GVSOFI_FATAL("The injector is trying to inject more than maximum number of faults per run: " +
                             std::to_string(MAX_MULTIPLE_FAULTS_NUM));
            }
            for (auto i = 0; i < num_of_injections; i++) {
                auto &inj_inf = injection_data[i];
                injection_input_file_stream >> inj_inf.injection_counter;
                injection_input_file_stream >> inj_inf.gvsoc_fi_mask;
                injection_input_file_stream >> inj_inf.reg_val_before_from_file;
                injection_input_file_stream >> inj_inf.cpu_config_mhartid;
                injection_input_file_stream >> inj_inf.instruction_label;
                inj_inf.is_ready_to_inject = true;
            }
        } else {
            GVSOFI_FATAL("Not able to read the injection input file:" + injection_input_file);
        }
        file_read = true;
    }
    auto selected_inj = select_injection_info(iss_wrapper_instance->cpu.config.mhartid,
                                              insn->decoder_item->u.insn.label, injection_data);
//    if (injection_counter == iteration_counter_gvsocfi &&
//        cpu_config_mhartid == iss_wrapper_instance->cpu.config.mhartid &&
//        instruction_label == insn->decoder_item->u.insn.label)
    if (selected_inj.is_ready_to_inject) {
        if (insn->nb_out_reg != 1) {
            GVSOFI_FATAL(std::string("More than one output register not supported, inst label:") +
                         insn->decoder_item->u.insn.label + " nb_out_reg:" + std::to_string(insn->nb_out_reg) +
                         " iteration_counter_gvsocfi:" + std::to_string(iteration_counter_gvsocfi)
            );
        }
        auto reg_val_before = insn->out_regs[0];

        // Just a double-checking on the instruction
        if (selected_inj.reg_val_before_from_file != insn->out_regs[0]) {
            GVSOFI_FATAL(
                    "Something went wrong on the sampling process,"
                    " reg before values from file and current differs:" +
                    std::to_string(selected_inj.reg_val_before_from_file) + " " +
                    std::to_string(insn->out_regs[0]) +
                    std::to_string(selected_inj.injection_counter)
            );
        }
        insn->out_regs[0] = insn->out_regs[0] ^ selected_inj.gvsoc_fi_mask;
        std::cout << "FAULT_INJECTED_HERE\n";

        std::ofstream injection_output_file_stream(injection_output_file);
        if (injection_output_file_stream.good()) {
            injection_output_file_stream << "reg val before:" << reg_val_before
                                         << " reg val after:" << insn->out_regs[0] << std::endl;
            injection_output_file_stream << "variables set\n";

            injection_output_file_stream << "injection_counter:" << selected_inj.injection_counter << std::endl;
            injection_output_file_stream << "gvsoc_fi_mask:" << selected_inj.gvsoc_fi_mask << std::endl;
            injection_output_file_stream << "reg_val_before_from_file:" << selected_inj.reg_val_before_from_file
                                         << std::endl;
            injection_output_file_stream << "cpu_config_mhartid:" << selected_inj.cpu_config_mhartid << std::endl;
            injection_output_file_stream << "instruction_label:" << selected_inj.instruction_label << std::endl;
        } else {
            GVSOFI_FATAL("Not able to read the injection output file:" + injection_output_file);
        }
    }
}

static inline void fault_injection(iss_t *iss_wrapper_instance, iss_insn_t *insn) {
    if (insn->decoder_item) {
        // static is necessary to check only once
        static char *run_type_ptr = std::getenv("GVSOCFI_RUN_TYPE");

        // TODO: Check if the instance->cpu.config.mhartid is indeed the core id

        if (run_type_ptr != nullptr) {
            auto gvsoc_fi_run_type = std::stoi(std::string(run_type_ptr));
            if (gvsoc_fi_run_type < 0 || gvsoc_fi_run_type > GVSOCFI_RUN_TYPE_OPTIONS) {
                GVSOFI_FATAL("Option for the environment var GVSOCFI_RUN_TYPE, not valid.");
            }
            switch (gvsoc_fi_run_type) {
                case PROFILER:
                    profiler(iss_wrapper_instance, insn);
                    break;
                case INST_INJECTOR:
                    inst_injector(iss_wrapper_instance, insn);
                    break;
                default:
                    GVSOFI_FATAL("Option for the environment var GVSOCFI_RUN_TYPE, not valid.");

            }
        }
        iteration_counter_gvsocfi++;
    }
}


#endif //GVSOC_FAULT_INJECTION_HPP

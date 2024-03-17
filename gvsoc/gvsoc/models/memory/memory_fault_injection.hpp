//
// Created by fernando on 08/08/22.
//

#ifndef GVSOC_MEMORY_FAULT_INJECTION_HPP
#define GVSOC_MEMORY_FAULT_INJECTION_HPP

#include <string>
#include <fstream>

static inline void gvsocfi_fatal(const std::string &error, int line, const std::string &file) {
    throw std::runtime_error("GVSOCFI_ERROR:::" + error + ":::AT:" + file + ":" + std::to_string(line));
}

#define GVSOFI_FATAL(x) gvsocfi_fatal(x, __LINE__, __FILE__)

static std::size_t mem_iteration_counter_gvsocfi = 0;

typedef enum {
    MEM_PROFILER = 0, // Start in 3 to avoid conflict with inst FI
    MEM_INJECTOR,
    GVSOCFI_MEM_RUN_TYPE_OPTIONS
} gvsocfi_mem_run_type_t;


static void mem_profiler(uint8_t *mem_data, uint64_t offset, uint64_t operation_size, uint64_t total_memory_size) {
    static auto profiler_output_file = std::string(std::getenv("GVSOCFI_PROFILER_FILE"));

    std::ofstream profiler_file_obj(profiler_output_file, std::ios::out | std::ios::app);
    if (profiler_file_obj.good()) {
        // comparing a tuple <internal counter, add, opcode, label, size> is enough
        // the internal counter is necessary to remove duplicate executions
        profiler_file_obj << mem_iteration_counter_gvsocfi << ";"
                          << uint32_t(mem_data[0]) << ";"
                          << uint32_t(mem_data[1]) << ";"
                          << offset << ";"
                          << operation_size << ";"
                          << total_memory_size << ";"
                          << "\n";
    } else {
        GVSOFI_FATAL("Not able to read the profiler file:" + profiler_output_file);
    }
}

static void mem_injector(uint8_t *mem_data, uint64_t offset, uint64_t operation_size, uint64_t total_memory_size) {
    // File that contains the fault input parameters
    static auto injection_input_file = std::string(std::getenv("GVSOCFI_INJECTION_IN_FILE"));
    static auto injection_output_file = std::string(std::getenv("GVSOCFI_INJECTION_OUT_FILE"));

    /**
     * Read the tuple
     */
    static auto file_read = false;
    static std::size_t injection_counter = -1;
    static uint32_t gvsoc_fi_mask = mem_data[0];

    static uint32_t mem_val_before_from_file = mem_data[0];
    static uint64_t offset_from_file = offset;
    static uint64_t operation_size_from_file = operation_size;
    static uint64_t total_memory_size_from_file = total_memory_size;
    // 32 is the smallest observed offset
    static uint64_t next_offset_double_cell_from_file = 32;
    static bool is_double_cell_upset = false;

    //load the file only once
    if (!file_read) {
        std::ifstream injection_input_file_stream(injection_input_file);
        if (injection_input_file_stream.good()) {
            injection_input_file_stream >> injection_counter;
            injection_input_file_stream >> gvsoc_fi_mask;
            injection_input_file_stream >> mem_val_before_from_file;
            injection_input_file_stream >> offset_from_file;
            injection_input_file_stream >> operation_size_from_file;
            injection_input_file_stream >> total_memory_size_from_file;
            injection_input_file_stream >> is_double_cell_upset;
            injection_input_file_stream >> next_offset_double_cell_from_file;
        } else {
            GVSOFI_FATAL("Not able to read the injection input file:" + injection_input_file);
        }
        file_read = true;
    }

    if (injection_counter == mem_iteration_counter_gvsocfi &&
        offset == offset_from_file &&
        operation_size == operation_size_from_file) {
        if (offset + 1 > total_memory_size) {
            GVSOFI_FATAL(
                    "The total offset + 1 is larger than the total memory_size:" +
                    std::to_string(offset + 1) + " " +
                    std::to_string(total_memory_size)
            );
        }

        auto mem_val_before = mem_data[0];
        // Offset was calculated from the beam experiments
        uint8_t mem_val_before_double_bit = 0;

        // Just a double-checking on the instruction
        if (mem_val_before_from_file != mem_val_before) {
            GVSOFI_FATAL("Something went wrong on the sampling process,"
                         " mem values from file and current differs:" +
                         std::to_string(mem_val_before_from_file) + " " +
                         std::to_string(mem_val_before) + " " + std::to_string(injection_counter)
            );
        }
        auto byte_mask = uint8_t(gvsoc_fi_mask);
        mem_data[0] = mem_val_before ^ byte_mask;

        if (is_double_cell_upset) {
            if (offset + next_offset_double_cell_from_file < total_memory_size) {
                mem_val_before_double_bit = mem_data[next_offset_double_cell_from_file];
                mem_data[next_offset_double_cell_from_file] = mem_val_before_double_bit ^ byte_mask;
            } else {
                GVSOFI_FATAL(
                        "OFFSET_OUTSIDE_MEMORY_BOUNDS:" + std::to_string(offset + next_offset_double_cell_from_file) +
                        " " + std::to_string(total_memory_size));
            }
        }
        std::cout << "FAULT_INJECTED_HERE\n";

        std::ofstream injection_output_file_stream(injection_output_file);
        if (injection_output_file_stream.good()) {
            injection_output_file_stream << "mem val before:" << int(mem_val_before)
                                         << " mem val after:" << int(mem_data[0]) << std::endl;
            injection_output_file_stream << "mem val before:" << int(mem_val_before_double_bit)
                                         << " mem val after:" << int(mem_data[next_offset_double_cell_from_file])
                                         << std::endl;
            injection_output_file_stream << "variables set\n";

            injection_output_file_stream << "injection_counter:" << injection_counter << std::endl;
            injection_output_file_stream << "gvsoc_fi_mask:" << gvsoc_fi_mask << std::endl;
            injection_output_file_stream << "mem_val_before_from_file:" << mem_val_before_from_file << std::endl;
            injection_output_file_stream << "offset_from_file:" << offset_from_file << std::endl;
            injection_output_file_stream << "operation_size_from_file:" << operation_size_from_file << std::endl;
            injection_output_file_stream << "total_memory_size_from_file:" << total_memory_size_from_file << std::endl;
            injection_output_file_stream << "is_double_cell_upset:" << is_double_cell_upset << std::endl;
            injection_output_file_stream << "next_offset_double_cell_from_file:" << next_offset_double_cell_from_file
                                         << std::endl;
        } else {
            GVSOFI_FATAL("Not able to read the injection output file:" + injection_output_file);
        }
    }
}


static inline void
memory_fault_injection(uint8_t *mem_data, uint64_t offset, uint64_t operation_size, uint64_t total_memory_size) {
    if (mem_data != nullptr) {
        // static is necessary to check only once
        static char *run_type_ptr = std::getenv("GVSOCFI_MEM_RUN_TYPE");

        if (run_type_ptr != nullptr) {
            auto gvsoc_fi_run_type = std::stoi(std::string(run_type_ptr));
            if (gvsoc_fi_run_type < 0 || gvsoc_fi_run_type > GVSOCFI_MEM_RUN_TYPE_OPTIONS) {
                GVSOFI_FATAL("Option for the environment var GVSOCFI_MEM_RUN_TYPE, not valid.");
            }
            switch (gvsoc_fi_run_type) {
                case MEM_PROFILER:
                    mem_profiler(mem_data, offset, operation_size, total_memory_size);
                    break;
                case MEM_INJECTOR:
                    mem_injector(mem_data, offset, operation_size, total_memory_size);
                    break;
                default:
                    GVSOFI_FATAL("Option for the environment var GVSOCFI_MEM_RUN_TYPE, not valid.");
            }
        }
        mem_iteration_counter_gvsocfi++;
    }
}


#endif //GVSOC_MEMORY_FAULT_INJECTION_HPP

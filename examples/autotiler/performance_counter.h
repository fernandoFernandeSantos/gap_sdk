//
// Created by fernando on 21/09/22.
//

#ifndef GAP_SDK_BEAM_PERFORMANCE_COUNTER_H
#define GAP_SDK_BEAM_PERFORMANCE_COUNTER_H

#define PROFILE_APP 1
#define SETUP_RADIATION_ITERATIONS 1024


typedef struct {
    uint32_t perf_cycles;
    uint32_t perf_inst;
} rad_setup_metrics_t;

static rad_setup_metrics_t rad_metrics_diff = {0, 0};
static rad_setup_metrics_t begin_rad_metrics_iteration = {0, 0};
static rad_setup_metrics_t end_rad_metrics_iteration = {0, 0};

static inline __attribute__((always_inline)) void start_counters() {
#if PROFILE_APP == 1
    pi_perf_conf(1 << PI_PERF_CYCLES | 1 << PI_PERF_INSTR);
    pi_perf_reset();

    pi_perf_start();
    rad_metrics_diff.perf_cycles = pi_perf_read(PI_PERF_CYCLES);
    rad_metrics_diff.perf_inst = pi_perf_read(PI_PERF_INSTR);
#endif
}

static inline __attribute__((always_inline)) void end_counters() {
#if PROFILE_APP == 1
    printf("RATIT:%d CORE:%d CYCLES_IN:%d CYCLES_OUT:%d INST_IN:%d INST_OUT:%d\n",
           SETUP_RADIATION_ITERATIONS,
           gap_ncore(),
           rad_metrics_diff.perf_cycles,
           pi_perf_read(PI_PERF_CYCLES),
           rad_metrics_diff.perf_inst,
           pi_perf_read(PI_PERF_INSTR)
    );
    pi_perf_stop();
#else
    printf("IT:%d\n");
#endif
}

static inline __attribute__((always_inline)) void begin_perf_iteration_i() {
#if PROFILE_APP == 1
    begin_rad_metrics_iteration.perf_cycles = pi_perf_read(PI_PERF_CYCLES);
    begin_rad_metrics_iteration.perf_inst = pi_perf_read(PI_PERF_INSTR);
#endif
}

static inline __attribute__((always_inline)) void end_perf_iteration_i() {
#if PROFILE_APP == 1
    end_rad_metrics_iteration.perf_cycles = pi_perf_read(PI_PERF_CYCLES);
    end_rad_metrics_iteration.perf_inst = pi_perf_read(PI_PERF_INSTR);
#endif
}

static inline __attribute__((always_inline)) void print_iteration_perf(int its) {
#if PROFILE_APP == 1
    printf("ITS:%d CORE:%d CYCLES_T1:%d CYCLES_T2:%d INST_T1:%d INST_T2:%d\n",
           its,
           gap_ncore(),
           begin_rad_metrics_iteration.perf_cycles,
           end_rad_metrics_iteration.perf_cycles,
           begin_rad_metrics_iteration.perf_inst,
           end_rad_metrics_iteration.perf_inst
    );
#endif
}


#endif //GAP_SDK_BEAM_PERFORMANCE_COUNTER_H

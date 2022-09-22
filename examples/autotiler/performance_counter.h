//
// Created by fernando on 21/09/22.
//

#ifndef GAP_SDK_BEAM_PERFORMANCE_COUNTER_H
#define GAP_SDK_BEAM_PERFORMANCE_COUNTER_H

#define PROFILE_APP 1
#define SETUP_RADIATION_ITERATIONS 1024


typedef struct {
    int perf_cycles;
    int perf_inst;
} rad_setup_metrics_t;

static rad_setup_metrics_t rad_metrics_diff = {0, 0};

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
    printf("CORE:%d CYCLES_IN:%d CYCLES_OUT:%d INST_IN:%d INST_OUT:%d\n",
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


#endif //GAP_SDK_BEAM_PERFORMANCE_COUNTER_H

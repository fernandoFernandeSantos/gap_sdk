//
// Created by fernando on 21/09/22.
//

#ifndef GAP_SDK_BEAM_PERFORMANCE_COUNTER_H
#define GAP_SDK_BEAM_PERFORMANCE_COUNTER_H

static inline __attribute__((always_inline)) void start_counters() {
    pi_perf_conf(1 << PI_PERF_CYCLES | 1 << PI_PERF_INSTR);
    pi_perf_reset();

    pi_perf_start();
    printf("CYCLE_IN-Core:%d Cycles:%d Inst:%d\n",
           gap_ncore(),
           pi_perf_read(PI_PERF_CYCLES),
           pi_perf_read(PI_PERF_INSTR)
    );
}

static inline __attribute__((always_inline)) void end_counters() {
    printf("CYCLE_IN-Core:%d Cycles:%d Inst:%d\n",
           gap_ncore(),
           pi_perf_read(PI_PERF_CYCLES),
           pi_perf_read(PI_PERF_INSTR)
    );
    pi_perf_stop();
}


#endif //GAP_SDK_BEAM_PERFORMANCE_COUNTER_H

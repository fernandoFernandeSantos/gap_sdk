/*
 * Copyright (C) 2017 GreenWaves Technologies
 * All rights reserved.
 *
 * This software may be modified and distributed under the terms
 * of the BSD license.  See the LICENSE file for details.
 *
 */

/* Matrix add example main file. This code actually runs on GAP8 */

#include <stdio.h>
#include "pmsis.h"
#include "Gap.h"
#include "MatAddKernels.h"

#include "../performance_counter.h"

#define STACK_SIZE ( 1024 )
#define CID        ( 0 )

#define MAT_W      ( 100 )
#define MAT_H      ( 100 )
#define MAT_SIZE   ( MAT_W * MAT_H )
#define SUM_INPUT 33

extern char *L1_Memory;

PI_L2 int Mat1[MAT_SIZE];
PI_L2 int Mat2[MAT_SIZE];
PI_L2 int MatOut[MAT_SIZE];

static void cluster_main() {
//    printf("cluster master start\n");

    MatADD(Mat1, Mat2, MatOut);
}

static void init_test() {
    for (int i = 0; i < MAT_SIZE; i++) {
        Mat1[i] = i;
        Mat2[i] = SUM_INPUT;
//        MatOut[i] = 0;
    }
}

void run_MatAdd(void) {
//    printf("Entering main controller\n");
    uint32_t errors = 0;

    /* Load matrices to add. */
    init_test();

    struct pi_device cluster_dev;
    struct pi_cluster_conf conf;
    /* Init cluster configuration structure. */
    pi_cluster_conf_init(&conf);
    conf.id = (uint32_t)CID;   /* Cluster ID. */
    /* Configure & open cluster. */
    pi_open_from_conf(&cluster_dev, (void *) &conf);
    if (pi_cluster_open(&cluster_dev)) {
        printf("Cluster open failed !\n");
        pmsis_exit(-1);
    }

    /* Allocate L1 memory used by AutoTiler in L1. */
    L1_Memory = (char *) pi_l1_malloc(&cluster_dev, _L1_Memory_SIZE);
    if (L1_Memory == 0) {
        printf("Memory Allocation Error! Quit...");
        pmsis_exit(-2);
    }
    printf("Allocated: %p, for %d bytes\n", L1_Memory, _L1_Memory_SIZE);
    start_counters();
    int its = 0;

    for (its = 0; its < SETUP_RADIATION_ITERATIONS && errors == 0; its++) {
        for (int i = 0; i < MAT_SIZE; i++) {
            MatOut[i] = 0;
        }
        /* Prepare task to be offload to Cluster. */
        struct pi_cluster_task task;
        pi_cluster_task(&task, cluster_main, NULL);
        task.stack_size = (uint32_t)STACK_SIZE;

        /* Offloading Task to cluster. */
        pi_cluster_send_task(&cluster_dev, &task);

        /* Checking result. */
//    for (int i = 0; i < MAT_H; i++) {
//        for (int j = 0; j < MAT_W; j++) {
//            if (MatOut[(i * MAT_W) + j] != 3) {
//                errors++;
//                printf("Error: MatOut[%d][%d]=%d != 3\n", i, j, MatOut[(i * MAT_W) + j]);
//            }
//        }
//    }
//        MatOut[4 * MAT_H] = 33;
        for (int i = 0; i < MAT_SIZE; i++) {
            errors += (MatOut[i] != (i + SUM_INPUT));
//                    {
//                errors++;
//                break;
//                printf("Error:[%d]=%d != %d\n", i, MatOut[i], gold);
//            }
        }
    }
    end_counters();

    if (errors != 0){
        printf("ErrorIt:%d\n", its);

        for (int i = 0; i < MAT_SIZE; i++) {
            const int gold = i + SUM_INPUT;
            if (MatOut[i] != gold) {
                printf("Error:[%d]=%d != %d\n", i, MatOut[i], gold);
            }
        }
    }
    pi_l1_free(&cluster_dev, L1_Memory, _L1_Memory_SIZE);

//    printf("Close cluster after end of computation.\n");
    pi_cluster_close(&cluster_dev);

    printf("Test %s with %ld error(s) !\n", (errors) ? "failed" : "success", errors);

    pmsis_exit(errors);
}


int main(void) {
//    printf("\n\n\t *** MatAdd ***\n\n");
    return pmsis_kickoff((void *) run_MatAdd);
}

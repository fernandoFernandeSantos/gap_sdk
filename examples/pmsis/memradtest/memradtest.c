#include <stdio.h>
/* PMSIS includes */
#include "pmsis.h"


#ifndef SETUP_RADIATION_ITERATIONS
#define SETUP_RADIATION_ITERATIONS 1024
#endif

/*
A level 2 Memory (512KB) for all the cores
A level 1 Memory (64 KB) shared by all the cores in Cluster
A level 1 memory (8 KB) owned by FC
 */

//does not work more than 48K on L1
#define L1_SIZE (62 * 1024)
//does not work more than 448K on L2
#define L2_SIZE (448 * 1024)
#define ONE_SECOND_TO_MICRO_SECONDS 1000 * 1000

typedef uint32_t double_word_t;

#define DOUBLE_WORD_AA (double_word_t) 0xAAAAAAAA
#define L1_ELEMENTS L1_SIZE / sizeof (double_word_t)
#define L2_ELEMENTS L2_SIZE / sizeof (double_word_t)

#ifndef MEM_LEVEL
#define MEM_LEVEL 1
#endif

double_word_t *MEMORY = 0;

void test_mem(void) {
    // We need to alloc the cluster for the L1 testing
#if MEM_LEVEL == 1
    printf("Testing L1\n");
    struct pi_device cluster_dev;
    struct pi_cluster_conf cl_conf;

    /* Init cluster configuration structure. */
    pi_cluster_conf_init(&cl_conf);
    cl_conf.id = 0;                /* Set cluster ID. */
    /* Configure & open cluster. */
    pi_open_from_conf(&cluster_dev, &cl_conf);
    if (pi_cluster_open(&cluster_dev)) {
        printf("Cluster open failed !\n");
        pmsis_exit(-1);
    }
    // Alloc the memory
    MEMORY = (double_word_t *) pi_cl_l1_malloc(&cluster_dev, L1_SIZE);
    const uint32_t elements = L1_ELEMENTS;
#elif MEM_LEVEL == 2
    printf("Testing L2\n");
    MEMORY = (double_word_t *) pi_l2_malloc(L2_SIZE);
    const uint32_t elements = L2_ELEMENTS;
#endif

    if (MEMORY == 0) {
        printf("Memory Allocation Error!");
        pmsis_exit(-2);
    }
    uint32_t errors = 0;
    for (uint32_t its = 0; its < SETUP_RADIATION_ITERATIONS && errors == 0; its++) {
        // Set the memory
        for (uint32_t i = 0; i < elements; i++) {
            MEMORY[i] = DOUBLE_WORD_AA;
        }

        // Wait for 1 second
        pi_time_wait_us(ONE_SECOND_TO_MICRO_SECONDS);
//        MEMORY[33] = 0xF0000d75;
        // Compare
        for (uint32_t i = 0; i < elements; i++) {
            if (MEMORY[i] != DOUBLE_WORD_AA) {
                printf("it:%d M[%d]=%x\n", its, i, MEMORY[i]);
                errors++;
            }
        }
    }
    printf("Test finished\n");
#if MEM_LEVEL == 1
    pi_cl_l1_free(&cluster_dev, MEMORY, L1_SIZE);
    pi_cluster_close(&cluster_dev);

#elif MEM_LEVEL == 2
    pi_l2_free(MEMORY, L2_SIZE);
#endif
    pmsis_exit(errors);
}


/* Program Entry. */
int main(void) {
    return pmsis_kickoff((void *) test_mem);
}

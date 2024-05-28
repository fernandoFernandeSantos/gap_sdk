#include <stdio.h>
/* PMSIS includes */
#include "pmsis.h"


#ifndef SETUP_RADIATION_ITERATIONS
#define SETUP_RADIATION_ITERATIONS 60
#endif

/*
A level 2 Memory (512KB) for all the cores
A level 1 Memory (64 KB) shared by all the cores in Cluster
A level 1 memory (8 KB) owned by FC
 */
typedef uint32_t double_word_t;

//does not work more than 48K on L1
#define L1_SIZE (48 * 1024)
//does not work more than 448K on L2
#define L2_SIZE (448 * 1024)
#define ONE_SECOND_TO_MICRO_SECONDS 1000 * 1000
#define L1_ELEMENTS L1_SIZE / sizeof (double_word_t)
#define L2_ELEMENTS L2_SIZE / sizeof (double_word_t)

#if MEM_LEVEL == 1
#define ELEMENTS L1_ELEMENTS
#else
#define ELEMENTS L2_ELEMENTS
#endif

double_word_t *MEMORY = NULL;
uint32_t ERRORS = 0;

void set_memory(){
    // Set the memory
    for (uint32_t i = 0; i < ELEMENTS; i++) {
        MEMORY[i] = SET_VALUE;
    }
}

void compare_memory(){
    for (uint32_t i = 0; i < ELEMENTS; i++) {
        if (MEMORY[i] != SET_VALUE) {
            printf("%d=%x\n", i, MEMORY[i]);
            ERRORS++;
        }
    }
}

void test_l1() {
    struct pi_device cluster_dev;
    struct pi_cluster_conf cl_conf;

    /* Init cluster configuration structure. */
    pi_cluster_conf_init(&cl_conf);
    cl_conf.id = 0;                /* Set cluster ID. */
    /* Configure & open cluster. */
    pi_open_from_conf(&cluster_dev, &cl_conf);
    if (pi_cluster_open(&cluster_dev)) {
        printf("Cluster open failed!\n");
        pmsis_exit(-1);
    }
    // Alloc the memory
    MEMORY = (double_word_t *) pi_cl_l1_malloc(&cluster_dev, L1_SIZE);

    if (MEMORY == 0) {
        printf("Memory Allocation Error!\n");
        pmsis_exit(-2);
    }

    //----------------------------------------------------------------------------------------------------------

    struct pi_cluster_task set_memory_task, compare_memory_task;
    pi_cluster_task(&set_memory_task, set_memory, NULL);
    pi_cluster_task(&compare_memory_task, compare_memory, NULL);

    for (uint32_t its = 0; its < SETUP_RADIATION_ITERATIONS && ERRORS == 0; its++) {
//        printf("i:%d\n", its);
        pi_cluster_send_task_to_cl(&cluster_dev, &set_memory_task);
        // Wait for 1 second
        pi_time_wait_us(ONE_SECOND_TO_MICRO_SECONDS);
//        MEMORY[33] = 0xF0000d75;
        // Compare
        pi_cluster_send_task_to_cl(&cluster_dev, &compare_memory_task);
    }
    //----------------------------------------------------------------------------------------------------------

    pi_cl_l1_free(&cluster_dev, MEMORY, L1_SIZE);
    pi_cluster_close(&cluster_dev);
}

void test_l2() {
    // We need to alloc the cluster for the L1 testing
    MEMORY = (double_word_t *) pi_l2_malloc(L2_SIZE);

    if (MEMORY == 0) {
        printf("Memory Allocation Error!\n");
        pmsis_exit(-2);
    }

    for (uint32_t its = 0; its < SETUP_RADIATION_ITERATIONS && ERRORS == 0; its++) {
//        printf("i:%d\n", its);
        set_memory();
        // Wait for 1 second
        pi_time_wait_us(ONE_SECOND_TO_MICRO_SECONDS);
//        MEMORY[33] = 0xF0000d75;
        // Compare
        compare_memory();
    }

    pi_l2_free(MEMORY, L2_SIZE);
}

void test_mem(void) {
    printf("L%u-%x\n", MEM_LEVEL, SET_VALUE);
    if (MEM_LEVEL == 1) {
        test_l1();
    } else {
        test_l2();
    }
    printf("L%u-%x\n", MEM_LEVEL, SET_VALUE);

    pmsis_exit(ERRORS);
}


/* Program Entry. */
int main(void) {
    return pmsis_kickoff((void *) test_mem);
}

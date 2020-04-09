/*
 * Copyright (c) 2020, GreenWaves Technologies, Inc.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without modification,
 * are permitted provided that the following conditions are met:
 *
 * o Redistributions of source code must retain the above copyright notice, this list
 *   of conditions and the following disclaimer.
 *
 * o Redistributions in binary form must reproduce the above copyright notice, this
 *   list of conditions and the following disclaimer in the documentation and/or
 *   other materials provided with the distribution.
 *
 * o Neither the name of GreenWaves Technologies, Inc. nor the names of its
 *   contributors may be used to endorse or promote products derived from this
 *   software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
 * ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include "pmsis.h"

/*******************************************************************************
 * Definitions
 ******************************************************************************/

/*******************************************************************************
 * Driver data
 *****************************************************************************/

extern struct dmacpy_driver_fifo_s *g_dmacpy_driver_fifo[];

/*******************************************************************************
 * API implementation
 ******************************************************************************/

void pi_dmacpy_conf_init(struct pi_dmacpy_conf *conf)
{
    __pi_dmacpy_conf_init(conf);
}

int pi_dmacpy_open(struct pi_device *device)
{
    int32_t status = -1;
    struct pi_dmacpy_conf *conf = (struct pi_dmacpy_conf *) device->config;
    DMACPY_TRACE("Open device id=%d\n", conf->id);
    status = __pi_dmacpy_open(conf, (struct dmacpy_driver_fifo_s **) &(device->data));
    DMACPY_TRACE("Open status : %d\n", status);
    return status;
}

void pi_dmacpy_close(struct pi_device *device)
{
    struct dmacpy_driver_fifo_s *fifo = (struct dmacpy_driver_fifo_s *) device->data;
    if (fifo != NULL)
    {
        DMACPY_TRACE("Close device id=%d\n", fifo->device_id);
        __pi_dmacpy_close(fifo->device_id);
        device->data = NULL;
    }
}

int pi_dmacpy_copy(struct pi_device *device, void *src, void *dst,
                   uint32_t size, pi_dmacpy_dir_e dir)
{
    int status = 0;
    pi_task_t task = {0};
    pi_task_block(&task);
    status = pi_dmacpy_copy_async(device, src, dst, size, dir, &task);
    if (status != 0)
    {
        DMACPY_TRACE_ERR("Error on copy %d!\n", status);
        pi_task_destroy(&task);
        return status;
    }
    pi_task_wait_on(&task);
    pi_task_destroy(&task);
    return status;
}

int pi_dmacpy_copy_async(struct pi_device *device, void *src, void *dst,
                         uint32_t size, pi_dmacpy_dir_e dir, struct pi_task *task)
{
    struct dmacpy_driver_fifo_s *fifo = (struct dmacpy_driver_fifo_s *) device->data;
    DMACPY_TRACE("DMA Memcpy(%ld): %lx %lx %ld %ld\n",
                 fifo->device_id, (uint32_t) src, (uint32_t) dst, size, dir);
    return __pi_dmacpy_copy(fifo->device_id, src, dst, size, dir, task);
}
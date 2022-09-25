#
# Copyright (C) 2020 GreenWaves Technologies
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import gsystree as st
import ips.iss.iss as iss
import ips.memory.memory as memory
import ips.interco.router as router
import ips.cache.cache as cache
import ips.interco.interleaver as interleaver
import gap.gap9.soc_interco as soc_interco
import gap.gap9.apb_soc_ctrl as apb_soc_ctrl
import ips.itc.itc_v1 as itc
import ips.gpio.gpio_v3 as gpio_module
import ips.soc_eu.soc_eu_v3 as soc_eu_module
from ips.timer.timer_v2 import Timer
from ips.stdout.stdout_v3 import Stdout
from ips.efuse.efuse_v1 import Efuse
from ips.icache_ctrl.icache_ctrl_v2 import Icache_ctrl
from ips.fll.fll_v2 import Fll
from gap.gap9.cluster import get_cluster_name
from ips.clock.clock_domain import Clock_domain
from gap.gap9.udma import Udma
from ips.xip.xip_v1 import Xip
from ips.interco.bus_watchpoint import Bus_watchpoint
from ips.debug.pulp_tap import Pulp_tap
from ips.debug.riscv_tap import Riscv_tap
from ips.mram.mram import Mram
from ips.gdbserver.gdbserver import Gdbserver


class Soc(st.Component):

    def __init__(self, parent, name, config_file, chip, cluster):
        super(Soc, self).__init__(parent, name)

        #
        # Properties
        #

        self.add_properties(self.load_property_file(config_file))

        nb_cluster = chip.get_property('nb_cluster', int)
        nb_pe = cluster.get_property('nb_pe', int)
        soc_events = self.get_property('soc_events')
        udma_conf_path = 'gap/gap9/udma.json'
        udma_conf = self.load_property_file(udma_conf_path)
        fc_events = self.get_property('peripherals/fc_itc/irq')
        rtc_irq = fc_events['evt_rtc']
        rtc_apb_irq = fc_events['evt_rtc_apb']

    
        #
        # Components
        #

        # ROM
        rom = memory.Memory(self, 'rom',
            size=self.get_property('apb_ico/mappings/rom/size'),
            stim_file=os.path.join(os.environ.get('INSTALL_DIR'), 'python', 'pulp', 'chips', 'gap9_v2', 'rom.bin')
        )

        # Debug ROM
        debug_rom = memory.Memory(self, 'debug_rom',
            size=self.get_property('apb_ico/mappings/debug_rom/size'),
            stim_file=os.path.join(os.environ.get('INSTALL_DIR'), 'python', 'pulp', 'chips', 'gap9_v2', 'debug_rom.bin')
        )

        # FLL
        fll = Fll(self, 'fll')

        # FC
        fc = iss.Iss(self, 'fc', **self.get_property('fc/iss_config'))

        # FC ITC
        fc_itc = itc.Itc_v1(self, 'fc_itc')
    
        # FC icache
        fc_icache = cache.Cache(self, 'fc_icache', **self.get_property('peripherals/fc_icache/config'))
    
        # FC icache controller
        fc_icache_ctrl = Icache_ctrl(self, 'fc_icache_ctrl')
    
        # XIP
        xip = Xip(self, 'xip', nb_refill_itfs=2)

        # APB soc controller
        soc_ctrl = apb_soc_ctrl.Apb_soc_ctrl(self, 'apb_soc_ctrl', self)

        # APB
        apb_ico = router.Router(self, 'apb_ico', latency=8)

        # Soc interconnect
        soc_ico = soc_interco.Soc_interco(self, 'soc_ico', self, cluster)

        # AXI
        axi_ico = router.Router(self, 'axi_ico', latency=12)

        # GPIO
        gpio = gpio_module.Gpio(self, 'gpio', nb_gpio=self.get_property('peripherals/gpio/nb_gpio'), soc_event=soc_events['soc_evt_gpio'])

        # UDMA
        udma = Udma(self, 'udma', config_file=udma_conf_path)

        # RISCV bus watchpoint
        fc_tohost = self.get_property('fc/riscv_fesvr_tohost_addr')
        if fc_tohost is not None:
            bus_watchpoint = Bus_watchpoint(self, 'bus_watchpoint', fc_tohost)

        # L2
        l2_priv0 = memory.Memory(self, 'l2_priv0', size=self.get_property('l2/priv0/mapping/size'), power_trigger=True)
        l2_priv1 = memory.Memory(self, 'l2_priv1', size=self.get_property('l2/priv1/mapping/size'))

        l2_shared_size = self.get_property('l2/shared/mapping/size', int)
    
        l2_shared_nb_banks = self.get_property('l2/shared/nb_banks', int)
        l2_shared_nb_regions = self.get_property('l2/shared/nb_regions', int)
        cut_size = int(l2_shared_size / l2_shared_nb_regions / l2_shared_nb_banks)

        for i in range(0, l2_shared_nb_regions):

            l2_shared_interleaver = interleaver.Interleaver(self, 'l2_shared_%d' % i, nb_slaves=l2_shared_nb_banks, interleaving_bits=self.get_property('l2/shared/interleaving_bits'))

            self.bind(soc_ico, 'l2_shared_%d' % i, l2_shared_interleaver, 'input')

            for j in range(0, l2_shared_nb_banks):

                cut = memory.Memory(self, 'l2_shared_%d_cut_%d' % (i, j), size=cut_size)

                self.bind(l2_shared_interleaver, 'out_%d' % j, cut, 'input')

                self.bind(soc_ctrl, 'l2_power_ctrl_' + str(i), cut, 'power_ctrl')

        # SOC EU
        soc_eu = soc_eu_module.Soc_eu(self, 'soc_eu', ref_clock_event=soc_events['soc_evt_ref_clock'], **self.get_property('peripherals/soc_eu/config'))

        # Timers
        timer = Timer(self, 'timer')
        timer_1 = Timer(self, 'timer_1')

        # Stdout
        stdout = Stdout(self, 'stdout')

        # Efuse
        efuse = Efuse(self, 'efuse', **self.get_property('peripherals/efuse/config'))

        # Pulp TAP
        pulp_tap = Pulp_tap(self, 'pulp_tag', **self.get_property('pulp_tap/config'))

        # RISCV TAP
        harts = []
        harts.append([(self.get_property('fc/iss_config/cluster_id') << 5) | (self.get_property('fc/iss_config/core_id') << 0), 'fc'])

        for cid in range(0, nb_cluster):
            for pe in range(0, nb_pe):
                hart_id = (cid << 5) | pe
    
                name = 'cluster%d_pe%d' % (cid, pe)
                harts.append([hart_id, name])

        riscv_tap = Riscv_tap(self, 'riscv_tap', **self.get_property('riscv_tap/config'), harts=harts)

        # MRAM
        mram = Mram(self, 'mram', size=2*1024*1024)

        # GDB server
        gdbserver = Gdbserver(self, 'gdbserver')



        #
        # Bindings
        #

        # FLL
        clocks = self.get_property('peripherals/fll/clocks')

        for i in range(0, len(clocks)):

            target = clocks[i]
            clock_itf = 'clock_' + str(i)

            if target == 'soc':
                self.bind(fll, clock_itf, self, 'fll_soc_clock')

            elif target == 'cluster':
                for cid in range(0, nb_cluster):
                    self.bind(fll, clock_itf, self, get_cluster_name(cid) + '_fll')

            elif target == 'periph':
                periph_clock = Clock_domain(self, 'periph_clock', frequency=50000000)
                periph_clock_dual_edges = Clock_domain(self, 'periph_clock_dual_edges', 100000000, factor=2)

                self.bind(fll, clock_itf, periph_clock, 'clock_in')
                self.bind(fll, clock_itf, periph_clock_dual_edges, 'clock_in')
                self.bind(periph_clock, 'out', udma, 'periph_clock')
                self.bind(periph_clock_dual_edges, 'out', udma, 'periph_clock_dual_edges')


        # FC
        self.bind(fc, 'fetch', fc_icache, 'input_0')
        self.bind(fc, 'irq_ack', fc_itc, 'irq_ack')
        if self.get_property('fc/riscv_fesvr_tohost_addr') is not None:
            self.bind(fc, 'data', bus_watchpoint, 'input')
        else:
            self.bind(fc, 'data', soc_ico, 'fc_data')
        self.bind(fc, 'flush_cache_req', fc_icache, 'flush')

        # FC icache
        self.bind(fc_icache, 'refill', soc_ico, 'fc_fetch')
        self.bind(fc_icache, 'flush_ack', fc, 'flush_cache_ack')

        # FC ITC
        self.bind(fc_itc, 'irq_req', fc, 'irq_req')

        # FC icache controller
        self.bind(fc_icache_ctrl, 'enable', fc_icache, 'enable')
        self.bind(fc_icache_ctrl, 'flush', fc_icache, 'flush')
        self.bind(fc_icache_ctrl, 'flush', fc, 'flush_cache')
        self.bind(fc_icache_ctrl, 'flush_line', fc_icache, 'flush_line')
        self.bind(fc_icache_ctrl, 'flush_line_addr', fc_icache, 'flush_line_addr')

        # Interrupts
        for name, irq in fc_events.items():
            if len(name.split('.')) == 2:
                comp_name, itf_name = name.split('.')
                self.bind(self.get_component(comp_name), itf_name, fc_itc, 'in_event_%d' % irq)

        # XIP
        self.bind(xip, 'fc_data_output', soc_ico, 'input')
        self.bind(xip, 'fc_fetch_output', soc_ico, 'input')
        self.bind(xip, 'refill_0', udma, 'refill_hyper0')
        self.bind(xip, 'refill_1', udma, 'refill_hyper1')

        # APB soc controller
        self.bind(soc_ctrl, 'ref_clock_muxed', timer, 'ref_clock')
        self.bind(soc_ctrl, 'ref_clock_muxed', timer_1, 'ref_clock')
        self.bind(soc_ctrl, 'fast_clk_ctrl', self, 'fast_clk_ctrl')
        self.bind(soc_ctrl, 'ref_clk_ctrl', self, 'ref_clk_ctrl')
        self.bind(self, 'fast_clock', fll, 'ref_clock')
        self.bind(self, 'fast_clock', soc_ctrl, 'fast_clock')
        self.bind(self, 'ref_clock', soc_ctrl, 'ref_clock')

        for i in range(0, 10):
            self.bind(soc_ctrl, 'dm_hart_available_' + str(i), riscv_tap, 'hart_available_' + str(i))

        self.bind(soc_ctrl, 'wakeup_out', self, 'wakeup_out')
        self.bind(soc_ctrl, 'wakeup_seq', self, 'wakeup_seq')
        self.bind(soc_ctrl, 'bootaddr', fc, 'bootaddr')
        self.bind(self, 'bootsel', soc_ctrl, 'bootsel')
        self.bind(soc_ctrl, 'confreg_soc', pulp_tap, 'confreg_soc')
        self.bind(pulp_tap, 'confreg_ext', soc_ctrl, 'confreg_ext')

        # APB
        apb_ico_mappings = self.get_property('apb_ico/mappings')
        self.bind(apb_ico, 'stdout', stdout, 'input')
        self.bind(apb_ico, 'fc_icache_ctrl', fc_icache_ctrl, 'input')
        self.bind(apb_ico, 'apb_soc_ctrl', soc_ctrl, 'input')
        self.bind(apb_ico, 'soc_eu', soc_eu, 'input')
        self.bind(apb_ico, 'gpio', gpio, 'input')
        self.bind(apb_ico, 'udma', udma, 'input')
        self.bind(apb_ico, 'xip', xip, 'apb_input')
        self.bind(apb_ico, 'fc_itc', fc_itc, 'input')
        self.bind(apb_ico, 'fc_dbg_unit', riscv_tap, 'input')
        self.bind(apb_ico, 'efuse', efuse, 'input')
        self.bind(apb_ico, 'pmu', self, 'pmu_input')
        self.bind(apb_ico, 'rom', rom, 'input')
        self.bind(apb_ico, 'debug_rom', debug_rom, 'input')
        self.bind(apb_ico, 'rtc', self, 'rtc_input')
        self.bind(apb_ico, 'fll', fll, 'input')
        self.bind(apb_ico, 'fc_timer', timer, 'input')
        self.bind(apb_ico, 'fc_timer_1', timer_1, 'input')
        self.bind(apb_ico, 'debug_rom', debug_rom, 'input')
        self.bind(apb_ico, 'fc_dbg_unit', fc, 'dbg_unit')

        # Soc interconnect 
        self.bind(soc_ico, 'fc_fetch_input', xip, 'fc_fetch_input')
        self.bind(soc_ico, 'fc_data_input', xip, 'fc_data_input')
        self.bind(soc_ico, 'apb', apb_ico, 'input')
        self.bind(soc_ico, 'l2_priv0', l2_priv0, 'input')
        self.bind(soc_ico, 'l2_priv1', l2_priv1, 'input')
        self.bind(soc_ico, 'axi_master', axi_ico, 'input')

        # AXI
        self.bind(axi_ico, 'soc', soc_ico, 'axi_slave')
        self.bind(self, 'soc_input', axi_ico, 'input')
        axi_ico.add_mapping('soc'      , **self.get_property('mapping'))
        base = cluster.get_property('mapping/base')
        size = cluster.get_property('mapping/size')
        for cid in range(0, nb_cluster):
            axi_ico.add_mapping(get_cluster_name(cid), base=base + size * cid, size=size)
            self.bind(axi_ico, get_cluster_name(cid), self, get_cluster_name(cid) + '_input')

        # GPIO
        self.bind(gpio, 'irq', fc_itc, 'in_event_%d' % self.get_property('peripherals/fc_itc/irq/evt_gpio'))
        self.bind(gpio, 'event', soc_eu, 'event_in')
        for i in range(0, self.get_property('peripherals/gpio/nb_gpio')):
            self.bind(self, 'gpio%d' % i, gpio, 'gpio%d' % i)

        # UDMA
        self.bind(self, 'fast_clock_out', udma, 'fast_clock')
        self.bind(udma, 'l2_itf', soc_ico, 'udma_tx')
        self.bind(udma, 'event_itf', soc_eu, 'event_in')

        for itf in udma_conf['interfaces']:
            itf_conf = udma_conf.get(itf)
            nb_channels = itf_conf.get('nb_channels')
            is_master = itf_conf.get('is_master')
            is_slave = itf_conf.get('is_slave')
            is_dual = itf_conf.get('is_dual')
            for channel in range(0, nb_channels):
                itf_name = itf + str(channel)
    
                if is_master:
                    self.bind(udma, itf_name, self, itf_name)
                if is_slave:
                    if is_dual:
                        self.bind(self, itf + str(channel*2), udma, itf + str(channel*2))
                        self.bind(self, itf + str(channel*2+1), udma, itf + str(channel*2+1))
                    else:
                        self.bind(self, itf_name, udma, itf_name)

            if itf == 'i2s':
                for slave_itf in range(0, nb_channels):
                    self.bind(udma, "commit_master_%d" % slave_itf, udma, "commit_slave_%d" % slave_itf)

              
        self.bind(udma, 'i2s0_clk_out', udma, 'i2s1_clk_in')
        self.bind(udma, 'i2s0_ws_out', udma, 'i2s1_ws_in')
        self.bind(udma, 'i2s0_clk_out', udma, 'i2s2_clk_in')
        self.bind(udma, 'i2s0_ws_out', udma, 'i2s2_ws_in')
    
        self.bind(udma, 'i2s0_pdm_out_0', udma, 'sfu_pdm_out_0')
        self.bind(udma, 'i2s0_pdm_out_1', udma, 'sfu_pdm_out_1')
        self.bind(udma, 'i2s1_pdm_out_0', udma, 'sfu_pdm_out_2')
        self.bind(udma, 'i2s1_pdm_out_1', udma, 'sfu_pdm_out_3')
        self.bind(udma, 'i2s2_pdm_out_0', udma, 'sfu_pdm_out_4')
        self.bind(udma, 'i2s2_pdm_out_1', udma, 'sfu_pdm_out_5')

        self.bind(udma, 'i2s0_pdm_in_0', udma, 'sfu_pdm_in_0')
        self.bind(udma, 'i2s0_pdm_in_1', udma, 'sfu_pdm_in_1')
        self.bind(udma, 'i2s0_pdm_in_2', udma, 'sfu_pdm_in_2')
        self.bind(udma, 'i2s0_pdm_in_3', udma, 'sfu_pdm_in_3')
        self.bind(udma, 'i2s1_pdm_in_0', udma, 'sfu_pdm_in_4')
        self.bind(udma, 'i2s1_pdm_in_1', udma, 'sfu_pdm_in_5')
        self.bind(udma, 'i2s1_pdm_in_2', udma, 'sfu_pdm_in_6')
        self.bind(udma, 'i2s1_pdm_in_3', udma, 'sfu_pdm_in_7')
        self.bind(udma, 'i2s2_pdm_in_0', udma, 'sfu_pdm_in_8')
        self.bind(udma, 'i2s2_pdm_in_1', udma, 'sfu_pdm_in_9')
        self.bind(udma, 'i2s2_pdm_in_2', udma, 'sfu_pdm_in_10')
        self.bind(udma, 'i2s2_pdm_in_3', udma, 'sfu_pdm_in_11')

        self.bind(udma, 'i2s0_ws_out', udma, 'sfu_ws_in_0')
        self.bind(udma, 'i2s1_ws_out', udma, 'sfu_ws_in_1')
        self.bind(udma, 'i2s2_ws_out', udma, 'sfu_ws_in_2')

        self.bind(udma, 'sfu_stream_in_ready_0', udma, 'stream_in_ready_0')
        self.bind(udma, 'sfu_stream_in_ready_1', udma, 'stream_in_ready_1')
        self.bind(udma, 'sfu_stream_in_ready_2', udma, 'stream_in_ready_2')
        self.bind(udma, 'sfu_stream_in_ready_3', udma, 'stream_in_ready_3')
        self.bind(udma, 'sfu_stream_in_ready_4', udma, 'stream_in_ready_4')
        self.bind(udma, 'sfu_stream_in_ready_5', udma, 'stream_in_ready_5')
        self.bind(udma, 'sfu_stream_in_ready_6', udma, 'stream_in_ready_6')
        self.bind(udma, 'sfu_stream_in_ready_7', udma, 'stream_in_ready_7')
        self.bind(udma, 'sfu_stream_in_ready_8', udma, 'stream_in_ready_8')
        self.bind(udma, 'sfu_stream_in_ready_9', udma, 'stream_in_ready_9')
        self.bind(udma, 'sfu_stream_in_ready_10', udma, 'stream_in_ready_10')
        self.bind(udma, 'sfu_stream_in_ready_11', udma, 'stream_in_ready_11')
        self.bind(udma, 'sfu_stream_in_ready_12', udma, 'stream_in_ready_12')
        self.bind(udma, 'sfu_stream_in_ready_13', udma, 'stream_in_ready_13')
        self.bind(udma, 'sfu_stream_in_ready_14', udma, 'stream_in_ready_14')
        self.bind(udma, 'sfu_stream_in_ready_15', udma, 'stream_in_ready_15')
          
        self.bind(udma, 'stream_in_data_0', udma, 'sfu_stream_in_data_0')
        self.bind(udma, 'stream_in_data_1', udma, 'sfu_stream_in_data_1')
        self.bind(udma, 'stream_in_data_2', udma, 'sfu_stream_in_data_2')
        self.bind(udma, 'stream_in_data_3', udma, 'sfu_stream_in_data_3')
        self.bind(udma, 'stream_in_data_4', udma, 'sfu_stream_in_data_4')
        self.bind(udma, 'stream_in_data_5', udma, 'sfu_stream_in_data_5')
        self.bind(udma, 'stream_in_data_6', udma, 'sfu_stream_in_data_6')
        self.bind(udma, 'stream_in_data_7', udma, 'sfu_stream_in_data_7')
        self.bind(udma, 'stream_in_data_8', udma, 'sfu_stream_in_data_8')
        self.bind(udma, 'stream_in_data_9', udma, 'sfu_stream_in_data_9')
        self.bind(udma, 'stream_in_data_10', udma, 'sfu_stream_in_data_10')
        self.bind(udma, 'stream_in_data_11', udma, 'sfu_stream_in_data_11')
        self.bind(udma, 'stream_in_data_12', udma, 'sfu_stream_in_data_12')
        self.bind(udma, 'stream_in_data_13', udma, 'sfu_stream_in_data_13')
        self.bind(udma, 'stream_in_data_14', udma, 'sfu_stream_in_data_14')
        self.bind(udma, 'stream_in_data_15', udma, 'sfu_stream_in_data_15')

        self.bind(udma, 'stream_out_ready_0', udma, 'sfu_stream_out_ready_0')
        self.bind(udma, 'stream_out_ready_1', udma, 'sfu_stream_out_ready_1')
        self.bind(udma, 'stream_out_ready_2', udma, 'sfu_stream_out_ready_2')
        self.bind(udma, 'stream_out_ready_3', udma, 'sfu_stream_out_ready_3')
        self.bind(udma, 'stream_out_ready_4', udma, 'sfu_stream_out_ready_4')
        self.bind(udma, 'stream_out_ready_5', udma, 'sfu_stream_out_ready_5')
        self.bind(udma, 'stream_out_ready_6', udma, 'sfu_stream_out_ready_6')
        self.bind(udma, 'stream_out_ready_7', udma, 'sfu_stream_out_ready_7')
        self.bind(udma, 'stream_out_ready_8', udma, 'sfu_stream_out_ready_8')
        self.bind(udma, 'stream_out_ready_9', udma, 'sfu_stream_out_ready_9')
        self.bind(udma, 'stream_out_ready_10', udma, 'sfu_stream_out_ready_10')
        self.bind(udma, 'stream_out_ready_11', udma, 'sfu_stream_out_ready_11')
        self.bind(udma, 'stream_out_ready_12', udma, 'sfu_stream_out_ready_12')
        self.bind(udma, 'stream_out_ready_13', udma, 'sfu_stream_out_ready_13')
        self.bind(udma, 'stream_out_ready_14', udma, 'sfu_stream_out_ready_14')
        self.bind(udma, 'stream_out_ready_15', udma, 'sfu_stream_out_ready_15')

        self.bind(udma, 'sfu_stream_out_data_0', udma, 'stream_out_data_0')
        self.bind(udma, 'sfu_stream_out_data_1', udma, 'stream_out_data_1')
        self.bind(udma, 'sfu_stream_out_data_2', udma, 'stream_out_data_2')
        self.bind(udma, 'sfu_stream_out_data_3', udma, 'stream_out_data_3')
        self.bind(udma, 'sfu_stream_out_data_4', udma, 'stream_out_data_4')
        self.bind(udma, 'sfu_stream_out_data_5', udma, 'stream_out_data_5')
        self.bind(udma, 'sfu_stream_out_data_6', udma, 'stream_out_data_6')
        self.bind(udma, 'sfu_stream_out_data_7', udma, 'stream_out_data_7')
        self.bind(udma, 'sfu_stream_out_data_8', udma, 'stream_out_data_8')
        self.bind(udma, 'sfu_stream_out_data_9', udma, 'stream_out_data_9')
        self.bind(udma, 'sfu_stream_out_data_10', udma, 'stream_out_data_10')
        self.bind(udma, 'sfu_stream_out_data_11', udma, 'stream_out_data_11')
        self.bind(udma, 'sfu_stream_out_data_12', udma, 'stream_out_data_12')
        self.bind(udma, 'sfu_stream_out_data_13', udma, 'stream_out_data_13')
        self.bind(udma, 'sfu_stream_out_data_14', udma, 'stream_out_data_14')
        self.bind(udma, 'sfu_stream_out_data_15', udma, 'stream_out_data_15')
              
        # Riscv bus watchpoint
        if self.get_property('fc/riscv_fesvr_tohost_addr') is not None:
            self.bind(bus_watchpoint, 'output', soc_ico, 'fc_data')

        # Soc eu
        self.bind(soc_eu, 'fc_event_itf', fc_itc, 'soc_event')
        self.bind(self, 'event', soc_eu, 'event_in')
        self.bind(self, 'ref_clock', soc_eu, 'ref_clock')
        self.bind(soc_eu, 'ref_clock_event', fc_itc, 'in_event_%d' % fc_events['evt_clkref'])
        self.bind(self, 'rtc_event_in', soc_eu, 'event_in')
        self.bind(soc_ctrl, 'event', soc_eu, 'event_in')
        self.bind(soc_eu, 'event_status', fc_itc, 'in_event_%d' % fc_events['evt_sw_event7'])

        # Timers
        self.bind(timer, 'irq_itf_0', fc_itc, 'in_event_10')
        self.bind(timer, 'irq_itf_1', fc_itc, 'in_event_11')

        self.bind(timer_1, 'irq_itf_0', fc_itc, 'in_event_12')
        self.bind(timer_1, 'irq_itf_1', fc_itc, 'in_event_13')

        # Pulp TAP
        self.bind(self, 'jtag0', pulp_tap, 'jtag_in')
        self.bind(pulp_tap, 'jtag_out', riscv_tap, 'jtag_in')

        # RISCV TAP
        self.bind(riscv_tap, 'jtag_out', self, 'jtag0_out')
        self.bind(riscv_tap, 'fc', fc, 'halt')

        for cluster in range(0, nb_cluster):
            for pe in range(0, nb_pe):
                name = 'cluster%d_pe%d' % (cluster, pe)
                self.bind(riscv_tap, name, self, 'halt_' + name)

        # MRAM
        self.bind(periph_clock, 'out', mram, 'clock')
        self.bind(udma, 'mram0_req', mram, 'input_req')
        self.bind(udma, 'mram0_data', mram, 'input_data')
        self.bind(udma, 'mram0_conf', mram, 'input_conf')

        # GDB server
        self.bind(gdbserver, 'out', soc_ico, 'debug')
    
        # RTC
        self.bind(self, 'wakeup_rtc', soc_ctrl, 'wakeup_rtc')
        self.bind(self, 'wakeup_rtc', fc_itc, 'in_event_16')
        self.bind(self, 'wakeup_rtc', fc_itc, 'in_event_%d' % (rtc_irq))
        self.bind(self, 'rtc_apb_irq', fc_itc, 'in_event_%d' % (rtc_apb_irq))
    
        # PMU
        self.bind(self, 'scu_ok', fc_itc, 'in_event_25')
        self.bind(self, 'picl_ok', fc_itc, 'in_event_24')

        # Cluster
        self.bind(self, 'dma_irq', fc_itc, 'in_event_8')

        # Pulp TAP
        self.bind(pulp_tap, 'io', soc_ico, 'debug')

        # RISCV TAP
        self.bind(riscv_tap, 'io', soc_ico, 'debug')


    def gen_gtkw_conf(self, tree, traces):
        if tree.get_view() == 'overview':
            self.vcd_group(self, skip=True)
        else:
            self.vcd_group(self, skip=False)
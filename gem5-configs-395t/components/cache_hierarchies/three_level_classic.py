"""
A three-level cache hierarchy with private L1 data and instruction cache, private
L2 cache, and an LLC (L3) shared between all cores.  The shared LLC is mostly-
inclusive with respect to the private caches.

The constructor accepts an arguments to change the memory bus (default: 192-bit
crossbar). The cache size, associativity, prefetcher, and replacement policy at
each cache level can be changed from their defaults via command-line arg.
"""
from typing import Type

from m5.objects import (
    L2XBar, SystemXBar, BadAddr, SnoopFilter, Cache, BaseXBar, Port
)
from gem5.components.cachehierarchies.classic.abstract_classic_cache_hierarchy import (
    AbstractClassicCacheHierarchy
)
from gem5.components.boards.abstract_board import AbstractBoard
from gem5.utils.override import *

from components.cache_hierarchies.caches.classic_caches import (
    L1DCache,
    L1ICache,
    L2Cache,
    LLCache,
    MMUCache
)
import components.cache_hierarchies.simargs_cache_hierarchy as simargs

class ThreeLevelClassicHierarchy(AbstractClassicCacheHierarchy):
    @staticmethod
    def _get_default_membus() -> SystemXBar:
        """
        Returns the default memory bus for the cache hierarchy, a 192-bit crossbar
        """
        membus = SystemXBar(width=192)
        membus.badaddr_responder = BadAddr()
        membus.default = membus.badaddr_responder.pio
        return membus

    def __init__(
        self,
        membus : BaseXBar = _get_default_membus.__func__()
    ) -> None:
        super().__init__()
        self.membus = membus

        # In SimObjects, internal attributes should be marked as such with
        # Python's weak private specifier (_var), otherwise they'll be
        # parsed as SimObject Params
        # Get command-line args related to the cache hierarchy
        self._l1d_params = simargs.get_l1d_params()
        self._l1i_params = simargs.get_l1i_params()
        self._l2_params = simargs.get_l2_params()
        self._llc_params = simargs.get_llc_params()

        print("Creating ThreeLevelClassicHierarchy")

    @overrides(AbstractClassicCacheHierarchy)
    def get_mem_side_port(self) -> Port:
        return self.membus.mem_side_ports

    @overrides(AbstractClassicCacheHierarchy)
    def get_cpu_side_port(self) -> Port:
        return self.membus.cpu_side_ports

    @overrides(AbstractClassicCacheHierarchy)
    def incorporate_cache(self, board: AbstractBoard) -> None:
        board.connect_system_port(self.membus.cpu_side_ports)

        for cntr in board.get_memory().get_memory_controllers():
            cntr.port = self.membus.mem_side_ports

        # Create divided L1s private to each core
        self.l1dcaches = [
            L1DCache(**self._l1d_params)
            for i in range(board.get_processor().get_num_cores())
        ]
        self.l1icaches = [
            L1ICache(**self._l1i_params)
            for i in range(board.get_processor().get_num_cores())
        ]

        # Create unified L2s private to each core
        # and the buses to connect their L1s
        self.l2caches = [
            L2Cache(**self._l2_params)
            for i in range(board.get_processor().get_num_cores())
        ]
        self.l2buses = [
            L2XBar(width=192)
            for i in range(board.get_processor().get_num_cores())
        ]

        # Each TLB is backed by a page table entry cache
        self.iptw_caches = [
            MMUCache()
            for i in range(board.get_processor().get_num_cores())
        ]
        self.dptw_caches = [
            MMUCache()
            for i in range(board.get_processor().get_num_cores())
        ]

        # Create an LLC to be shared by all cores
        # and a coherent crossbar for its bus
        self.llcache = LLCache(**self._llc_params)
        self.llcXbar = L2XBar(width=192, 
                              snoop_filter = SnoopFilter(max_capacity='32MB'))

        if board.has_coherent_io():
            self._setup_io_cache(board)

        for i, cpu in enumerate(board.get_processor().get_cores()):
            # connect each CPU to its L1 caches
            cpu.connect_icache(self.l1icaches[i].cpu_side)
            cpu.connect_dcache(self.l1dcaches[i].cpu_side)

            # connect each L1 caches to the bus to its L2
            self.l1icaches[i].mem_side = self.l2buses[i].cpu_side_ports
            self.l1dcaches[i].mem_side = self.l2buses[i].cpu_side_ports

            # connect each PTE cache to the bus to its L2
            self.iptw_caches[i].mem_side = self.l2buses[i].cpu_side_ports
            self.dptw_caches[i].mem_side = self.l2buses[i].cpu_side_ports

            # connect each L2 bus to its L2 cache
            self.l2buses[i].mem_side_ports = self.l2caches[i].cpu_side

            # connect each L2 cache to the crossbar to the shared LLC
            self.l2caches[i].mem_side = self.llcXbar.cpu_side_ports

            # connect the core's page-table walkers to the MMU caches
            cpu.connect_walker_ports(
                self.iptw_caches[i].cpu_side, self.dptw_caches[i].cpu_side
            )

            # connect interrupt port
            int_req_port = self.membus.mem_side_ports
            int_resp_port = self.membus.cpu_side_ports
            cpu.connect_interrupt(int_req_port, int_resp_port)

        # connect the LLC crossbar to the shared LLC
        self.llcXbar.mem_side_ports = self.llcache.cpu_side

        # connect the LLC to the memory bus
        self.membus.cpu_side_ports = self.llcache.mem_side

    """ Create a cache for coherent I/O connections """
    def _setup_io_cache(self, board: AbstractBoard) -> None:
        self.iocache = Cache(
            size = "1kB",
            assoc = 8,
            tag_latency = 50,
            data_latency = 50,
            response_latency = 50,
            mshrs = 20,
            tgts_per_mshr = 12,
            addr_ranges=board.mem_ranges
        )
        self.iocache.mem_side = self.membus.cpu_side_ports
        self.iocache.cpu_side = board.get_mem_side_coherent_io_port()

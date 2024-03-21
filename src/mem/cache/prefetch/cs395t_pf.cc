#include "mem/cache/prefetch/cs395t_pf.hh"
#include "params/CS395TPrefetcher.hh"

#include <cassert>

#include "base/intmath.hh"
#include "base/logging.hh"
#include "base/random.hh"
#include "base/trace.hh"
#include "debug/HWPrefetch.hh"
#include "mem/cache/prefetch/associative_set_impl.hh"
#include "mem/cache/replacement_policies/base.hh"

// TODO FIXME: See stride.cc/.hh for reference.  There are many utility
// functions that may help with building a prefetcher.

namespace gem5
{

namespace prefetch
{

CS395TPrefetcher::CS395TPrefetcher(const CS395TPrefetcherParams &params)
    : Queued(params), example_size(params.size)
    // TODO: Add more params here
{
}

void
CS395TPrefetcher::calculatePrefetch(const PrefetchInfo &pfi,
                                    std::vector<AddrPriority> &addresses,
                                    const CacheAccessor &cache)
{
    // TODO FIXME: Generate a prefetch.
}

} // namespace prefetch
} // namespace gem5

#ifndef __MEM_CACHE_PREFETCH_CS395T_PF_HH__
#define __MEM_CACHE_PREFETCH_CS395T_PF_HH__

#include <string>
#include <unordered_map>
#include <vector>

#include "mem/cache/prefetch/queued.hh"
#include "base/sat_counter.hh"
#include "base/types.hh"
#include "mem/cache/prefetch/associative_set.hh"
#include "mem/cache/replacement_policies/replaceable_entry.hh"
#include "mem/cache/tags/indexing_policies/set_associative.hh"
#include "mem/packet.hh"

namespace gem5
{

struct CS395TPrefetcherParams;

namespace prefetch
{

class CS395TPrefetcher : public Queued
{
  protected:
    const unsigned example_size; // example parameter
    // TODO: Add more params here

  public:
    CS395TPrefetcher(const CS395TPrefetcherParams &params);
    ~CS395TPrefetcher() = default;

    void calculatePrefetch(const PrefetchInfo &pfi,
                           std::vector<AddrPriority> &addresses,
                           const CacheAccessor &cache) override;
};

} // namespace prefetch
} // namespace gem5

#endif // __MEM_CACHE_PREFETCH_CS395T_PF_HH__

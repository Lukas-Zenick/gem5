#include "mem/cache/replacement_policies/cs395t_rp.hh"
#include "params/CS395TRP.hh"

// TODO FIXME: See lru_rp.cc/.hh for reference.

namespace gem5
{
namespace replacement_policy
{

CS395TRP::CS395TRP(const CS395TRPParams &params)
    : Base(params), example_size(params.size)
    // TODO: Add more params here
{
}

void
CS395TRP::invalidate(const std::shared_ptr<ReplacementData>& replacement_data)
{
    // TODO FIXME: this block has been invalidated, set its replacement data to
    // whatever encodes the next victim.
}

void
CS395TRP::touch(const std::shared_ptr<ReplacementData>& replacement_data) const
{
    // TODO FIXME: this block has been accessed, update its replacement data
}

void
CS395TRP::reset(const std::shared_ptr<ReplacementData>& replacement_data) const
{
    // TODO FIXME: this block is newly inserted into the cache, reset its replacement
    // data to the insertion state
}

ReplaceableEntry*
CS395TRP::getVictim(const ReplacementCandidates& candidates) const
{
    assert(candidates.size() > 0);

    // TODO FIXME: choose a replacement victim among the candidates, i.e., the
    // replacement data entries in the ways of this set
    return candidates[0];
}

std::shared_ptr<ReplacementData>
CS395TRP::instantiateEntry()
{
    // create a new replacement data entry
    return std::shared_ptr<ReplacementData>(new CS395TReplData());
}

} // namespace replacement_policy
} // namespace gem5

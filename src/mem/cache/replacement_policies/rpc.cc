#include "mem/cache/replacement_policies/rpc.hh"
#include "base/logging.hh" // For fatal_if
#include "params/RPC.hh"
#include "debug/MockingjayDebug.hh"

namespace gem5
{
namespace replacement_policy
{

uint64_t getAccessType(const PacketPtr &pkt) {
    if (pkt->isRead() && !pkt->isWriteback()) {
        return 0; // LOAD
    } else if (pkt->cmd == MemCmd::WriteReq) { // Assuming WriteReq as RFO for simplification
        return 1; // RFO?
    } else if (pkt->isWriteback()) {
        return 2; // WRITEBACK
    } else if (pkt->req->isPrefetch()) {
        return 3; // PREFETCH
    } else {
        return 0; // Default case, adjust based on your requirements
    }
}

RPC::RPC(const RPCParams &params)
    : Base(params),  _num_etr_bits(params.num_etr_bits) {
    sampled_cache = std::make_unique<rpc::SampledCache>(params.num_sampled_sets, params.num_cache_sets, params.cache_block_size, params.timer_size, params.num_cpus, params.num_internal_sampled_sets);
    predictor = std::make_unique<rpc::ReuseDistPredictor>(params.num_pred_entries, params.num_pred_bits, params.num_clock_bits, params.num_cpus);
    age_ctr.resize(params.num_cache_sets, 0);
    _log2_block_size = (int) std::log2(params.cache_block_size);
    _log2_num_cache_sets = (int) std::log2(params.num_cache_sets);
    _num_clock_bits = params.num_clock_bits;

    DPRINTF(MockingjayDebug, "Cache Initialization ---- Number of Cache Sets: %d, Cache Block Size: %d, Number of Cache Ways: %d\n", params.num_cache_sets, params.cache_block_size, params.num_cache_ways);
    DPRINTF(MockingjayDebug, "History Sampler Initialization ---- Number of Sample Sets: %d, Timer Size: %d\n", params.num_sampled_sets, params.timer_size);
    DPRINTF(MockingjayDebug, "Predictor Initialization ---- Number of Predictor Entries: %d, Counter of Predictors: %d\n", params.num_pred_entries, params.num_pred_bits);
    DPRINTF(MockingjayDebug, "CPU Core Initialization ---- Number of Cores: %d\n", params.num_cpus);
}

void
RPC::invalidate(const std::shared_ptr<ReplacementData>& replacement_data) {
    std::shared_ptr<RPCReplData> casted_replacement_data = std::static_pointer_cast<RPCReplData>(replacement_data);
    casted_replacement_data->valid = false;
    casted_replacement_data->etr = 0;
}

void
RPC::touch(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt, const ReplacementCandidates& candidates) {
    std::shared_ptr<RPCReplData> casted_replacement_data =
        std::static_pointer_cast<RPCReplData>(replacement_data);

    // TODO: Which requests should we monitor?
    if (!pkt->isRequest() || !pkt->req->hasPC() || !pkt->req->hasContextId()) {
        //TODO: Change to hasVaddr?
        return;
    }

    // DPRINTF(MockingjayDebug, "Cache hit ---- Packet type having PC: %s\n", pkt->cmdString());

    // Warning: This is not aligned with indexing policy if it use interleave set indexing technique
    int set = (pkt->getAddr() >> _log2_block_size) & ((1 << _log2_num_cache_sets) - 1);

    DPRINTF(MockingjayDebug, "Cache hit ---- Request Address: 0x%.8x, Set Index: %d\n", pkt->getAddr(), set);

    // Warning: Timestamp is 8-bit integer in this design
    uint8_t curr_timestamp = 0;
    uint8_t last_timestamp = 0;
    uint16_t last_PC = 0;
    bool evict = false;
    bool sample_hit = false;

    // Cache hit
    // Sampled cache
    //  1. If sampled cache hit, predictor will train with signature in the sampled cache for new reuse distance
    //  2. If sampled cache miss and sampled cache no eviction, no training needed
    //  3. If sampled cache miss and sampled cache eviction, the eviction line should be detrained as scan line

    uint64_t access_type = getAccessType(pkt);
    
    if (sampled_cache->sample(pkt->getAddr(), access_type, &curr_timestamp, set, &last_PC, &last_timestamp, true, &evict, &sample_hit, pkt->req->contextId(), predictor->getInfRd())) {
        predictor->train(last_PC, sample_hit, curr_timestamp, last_timestamp, evict);
        DPRINTF(MockingjayDebug, "Cache hit ---- Sampler, Last timestamp: %d, Current timestamp: %d, Last PC: 0x%.8x\n", last_timestamp, curr_timestamp, last_PC);
    }

    // If aging clock reaches maximum point, then all cache lines should be aged.
    uint64_t aging_max = (1 << _num_clock_bits) - 1;
    if (age_ctr[set] != aging_max) {
        age_ctr[set] += 1;
    } else {
        age_ctr[set] = 0;

        for (const auto &candidate : candidates) {
            std::shared_ptr<RPCReplData> candidate_repl_data =
                std::static_pointer_cast<RPCReplData>(
                    candidate->replacementData);
            candidate_repl_data->aging();
        }
    }
    // casted_replacement_data->etr = predictor->predict(pkt->req->getPC(), true, pkt->req->contextId(), casted_replacement_data->abs_max_etr);
    casted_replacement_data->etr = predictor->predict(pkt->getAddr(), access_type, true, pkt->req->contextId(), casted_replacement_data->abs_max_etr);
    DPRINTF(MockingjayDebug, "Cache hit ---- ETR update: %d, INF_ETR: %d\n", casted_replacement_data->etr, casted_replacement_data->abs_max_etr);
}

void
RPC::reset(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt, const ReplacementCandidates& candidates) {
    std::shared_ptr<RPCReplData> casted_replacement_data =
        std::static_pointer_cast<RPCReplData>(replacement_data);

    uint64_t access_type = getAccessType(pkt);
    
    // TODO: Which requests should we monitor?
    if (!pkt->isResponse() || !pkt->req->hasVaddr() || !pkt->req->hasContextId()) {
        return;
    }

    // ETR for replacement_data should be the maximum absolute value in the whole set
    // if (predictor->bypass(pkt->req->getPC(), casted_replacement_data->etr, false, pkt->req->contextId(), casted_replacement_data->valid)) {
    if(predictor->bypass(pkt->getAddr(), getAccessType(pkt), casted_replacement_data->abs_max_etr, false, pkt->req->contextId(), casted_replacement_data->valid)) {
        // DPRINTF(MockingjayDebug, "Cache miss ---- Bypass cache: PC: 0x%.8x\n", pkt->req->getPC());
        return;
    }

    // DPRINTF(MockingjayDebug, "Cache miss ---- Packet type having PC: %s\n", pkt->cmdString());

    // Warning: This is not aligned with indexing policy if it use interleave set indexing technique
    int set = (pkt->getAddr() >> _log2_block_size) & ((1 << _log2_num_cache_sets) - 1);

    // DPRINTF(MockingjayDebug, "Cache miss ---- Request Address: 0x%.8x, Set Index: %d, PC: 0x%.8x\n", pkt->getAddr(), set, pkt->req->getPC());

    // Warning: Timestamp is 8-bit integer in this design
    uint8_t curr_timestamp = 0;
    uint8_t last_timestamp = 0;
    uint16_t last_PC = 0;
    bool evict = false;
    bool sample_hit = false;

    // Cache miss
    // Sampled cache
    //  1. If sampled cache hit, predictor will train with signature in the sampled cache for new reuse distance
    //  2. If sampled cache miss and sampled cache no eviction, no training needed
    //  3. If sampled cache miss and sampled cache eviction, the eviction line should be detrained as scan line
    if (sampled_cache->sample(pkt->getAddr(), access_type, &curr_timestamp, set, &last_PC, &last_timestamp, false, &evict, &sample_hit, pkt->req->contextId(), predictor->getInfRd())) {
        predictor->train(last_PC, sample_hit, curr_timestamp, last_timestamp, evict);
        DPRINTF(MockingjayDebug, "Cache miss ---- Sampler, Last timestamp: %d, Current timestamp: %d, Last PC: 0x%.8x\n", last_timestamp, curr_timestamp, last_PC);
    }

    // If aging clock reaches maximum point, then all cache lines should be aged.
    uint64_t aging_max = (1 << _num_clock_bits) - 1;
    if (age_ctr[set] != aging_max) {
        age_ctr[set] += 1;
    } else {
        age_ctr[set] = 0;

        for (const auto &candidate : candidates) {
            std::shared_ptr<RPCReplData> candidate_repl_data =
                std::static_pointer_cast<RPCReplData>(
                    candidate->replacementData);
            candidate_repl_data->aging();
        }
    }

    // replacement status update
    // casted_replacement_data->etr = predictor->predict(pkt->getAddr(), false, pkt->req->contextId(), casted_replacement_data->abs_max_etr);
    casted_replacement_data->etr = predictor->predict(pkt->getAddr(), access_type, false, pkt->req->contextId(), casted_replacement_data->abs_max_etr);
    DPRINTF(MockingjayDebug, "Cache miss ---- ETR update: %d, INF_ETR: %d\n", casted_replacement_data->etr, casted_replacement_data->abs_max_etr);
    casted_replacement_data->valid = true;
}

ReplaceableEntry*
RPC::getVictim(const ReplacementCandidates& candidates) const {
    assert(candidates.size() > 0);

    // Use first candidate as dummy victim
    ReplaceableEntry* victim = candidates[0];

    // Store victim->etr in a variable to improve code readability
    int victim_etr = std::static_pointer_cast<RPCReplData>(victim->replacementData)->etr;
    int abs_victim_etr = std::abs(victim_etr);

    // Visit all candidates to find victim
    for (const auto& candidate : candidates) {
        std::shared_ptr<RPCReplData> candidate_repl_data =
            std::static_pointer_cast<RPCReplData>(
                candidate->replacementData);

        // Stop searching for victims if an invalid entry is found
        if (!candidate_repl_data->valid) {
            return candidate;
        }

        // Update victim entry if necessary
        // Choose the one with maximum reuse distance (ETR allow negative value to avoid cache line s)
        int candidate_etr = candidate_repl_data->etr;
        int abs_candidate_etr = std::abs(candidate_etr);
        if (abs_candidate_etr > abs_victim_etr || ((abs_candidate_etr == abs_victim_etr) && (candidate_etr < 0))) {
            victim = candidate;
            victim_etr = candidate_etr;
            abs_victim_etr = abs_candidate_etr;
        }
    }

    return victim;
}

std::shared_ptr<ReplacementData>
RPC::instantiateEntry() {
   return std::shared_ptr<ReplacementData>(new RPCReplData(_num_etr_bits));
}

void RPC::reset(const std::shared_ptr<ReplacementData>& replacement_data) const {
    panic("Cant train Mockingjay's predictor without access information.");
}

void RPC::touch(const std::shared_ptr<ReplacementData>& replacement_data) const {
    panic("Cant train Mockingjay's predictor without access information.");
}

void RPC::reset(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt) {
    panic("Cant train Mockingjay's predictor without all cache blocks reference. RESET DOES NOT HAVE THE REPLACEMENT CANDIDATES.");
}

void RPC::touch(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt) {
    panic("Cant train Mockingjay's predictor without all cache blocks reference. TOUCH DOES NOT HAVE THE REPLACEMENT CANDIDATES.");
}

} // namespace replacement_policy
} // namespace gem5

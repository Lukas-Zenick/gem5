// #include "mem/cache/replacement_policies/ee.hh"
// #include "base/logging.hh" // For fatal_if
// #include "params/EE.hh"
// #include "debug/MockingjayDebug.hh"
// #include "debug/LUKAS.hh"

// namespace gem5
// {
// namespace replacement_policy
// {

// uint64_t accessType(const PacketPtr &pkt) {
//     if (pkt->isRead() && !pkt->isWriteback()) {
//         return 0; // LOAD
//     } else if (pkt->cmd == MemCmd::WriteReq) { // Assuming WriteReq as RFO for simplification
//         return 1; // RFO?
//     } else if (pkt->isWriteback()) {
//         return 2; // WRITEBACK
//     } else if (pkt->req->isPrefetch()) {
//         return 3; // PREFETCH
//     } else {
//         return 0; // Default case, adjust based on your requirements
//     }
// }

// EE::EE(const EEParams &params)
//     : Base(params),  _num_etr_bits(params.num_etr_bits) {
//     sampled_cache = std::make_unique<ee::SampledCache>(params.num_sampled_sets, params.num_cache_sets, params.cache_block_size, params.timer_size, params.num_cpus, params.num_internal_sampled_sets);
//     predictor = std::make_unique<ee::ReuseDistPredictor>(params.num_pred_entries, params.num_pred_bits, params.num_clock_bits, params.num_cpus);
//     age_ctr.resize(params.num_cache_sets, 0);
//     _log2_block_size = (int) std::log2(params.cache_block_size);
//     _log2_num_cache_sets = (int) std::log2(params.num_cache_sets);
//     _num_clock_bits = params.num_clock_bits;

//     DPRINTF(MockingjayDebug, "Cache Initialization ---- Number of Cache Sets: %d, Cache Block Size: %d, Number of Cache Ways: %d\n", params.num_cache_sets, params.cache_block_size, params.num_cache_ways);
//     DPRINTF(MockingjayDebug, "History Sampler Initialization ---- Number of Sample Sets: %d, Timer Size: %d\n", params.num_sampled_sets, params.timer_size);
//     DPRINTF(MockingjayDebug, "Predictor Initialization ---- Number of Predictor Entries: %d, Counter of Predictors: %d\n", params.num_pred_entries, params.num_pred_bits);
//     DPRINTF(MockingjayDebug, "CPU Core Initialization ---- Number of Cores: %d\n", params.num_cpus);
// }

// void
// EE::invalidate(const std::shared_ptr<ReplacementData>& replacement_data) {
//     std::shared_ptr<EEReplData> casted_replacement_data = std::static_pointer_cast<EEReplData>(replacement_data);
//     casted_replacement_data->valid = false;
//     casted_replacement_data->etr = 0;
// }

// void
// EE::touch(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt, const ReplacementCandidates& candidates) {
//     std::shared_ptr<EEReplData> casted_replacement_data =
//         std::static_pointer_cast<EEReplData>(replacement_data);

//     // TODO: Which requests should we monitor?
//     // if (!pkt->isRequest() || !pkt->req->hasVaddr() || !pkt->req->hasContextId()) { //normal
//     if(!(pkt->isWriteback() || pkt->req->isPrefetch())) {
//         if (!pkt->isRequest() || !pkt->req->hasPC() || !pkt->req->hasContextId()) {
//             DPRINTF(MockingjayDebug, "Cache miss ---- Bypass cache: PC: 0x%.8x\n", pkt->req->getPC());
//             return;
//         }
//     }

//     // if(pkt->isWriteback()) {
//     //     DPRINTF(LUKAS, "1: IM A WRITEBACK. hasPC: %d\n", pkt->req->hasPC());
//     // }

//     // DPRINTF(MockingjayDebug, "Cache hit ---- Packet type having PC: %s\n", pkt->cmdString());

//     // Warning: This is not aligned with indexing policy if it use interleave set indexing technique
//     int set = (pkt->getAddr() >> _log2_block_size) & ((1 << _log2_num_cache_sets) - 1);

//     DPRINTF(MockingjayDebug, "Cache hit ---- Request Address: 0x%.8x, Set Index: %d\n", pkt->getAddr(), set);

//     // Warning: Timestamp is 8-bit integer in this design
//     uint8_t curr_timestamp = 0;
//     uint8_t last_timestamp = 0;
//     uint16_t last_PC = 0;
//     bool evict = false;
//     bool sample_hit = false;

//     // Cache hit
//     // Sampled cache
//     //  1. If sampled cache hit, predictor will train with signature in the sampled cache for new reuse distance
//     //  2. If sampled cache miss and sampled cache no eviction, no training needed
//     //  3. If sampled cache miss and sampled cache eviction, the eviction line should be detrained as scan line

//     uint64_t access_type = accessType(pkt);

//     int context_id = pkt->req->hasContextId() ? pkt->req->contextId() : 0;
    
//     if (sampled_cache->sample(pkt->getAddr(), access_type, &curr_timestamp, set, &last_PC, &last_timestamp, true, &evict, &sample_hit, context_id, predictor->getInfRd())) {
//         predictor->train(last_PC, sample_hit, curr_timestamp, last_timestamp, evict, access_type);
//         DPRINTF(MockingjayDebug, "Cache hit ---- Sampler, Last timestamp: %d, Current timestamp: %d, Last PC: 0x%.8x\n", last_timestamp, curr_timestamp, last_PC);
//     }

//     // If aging clock reaches maximum point, then all cache lines should be aged.
//     uint64_t aging_max = (1 << _num_clock_bits) - 1;
//     if (age_ctr[set] != aging_max) {
//         age_ctr[set] += 1;
//     } else {
//         age_ctr[set] = 0;

//         for (const auto &candidate : candidates) {
//             std::shared_ptr<EEReplData> candidate_repl_data =
//                 std::static_pointer_cast<EEReplData>(
//                     candidate->replacementData);
//             candidate_repl_data->aging();
//         }
//     }
//     // casted_replacement_data->etr = predictor->predict(pkt->req->getPC(), true, pkt->req->contextId(), casted_replacement_data->abs_max_etr);
//     casted_replacement_data->etr = predictor->predict(pkt->getAddr(), access_type, true, context_id, casted_replacement_data->abs_max_etr);
//     DPRINTF(MockingjayDebug, "Cache hit ---- ETR update: %d, INF_ETR: %d\n", casted_replacement_data->etr, casted_replacement_data->abs_max_etr);
// }

// void
// EE::reset(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt, const ReplacementCandidates& candidates) {
//     std::shared_ptr<EEReplData> casted_replacement_data =
//         std::static_pointer_cast<EEReplData>(replacement_data);
    
//     // TODO: Which requests should we monitor?
//     // if (!pkt->isRequest() || !pkt->req->hasVaddr() || !pkt->req->hasContextId()) { //normal
//     if(!(pkt->isWriteback() || pkt->req->isPrefetch())) {
//         if (!pkt->isRequest() || !pkt->req->hasPC() || !pkt->req->hasContextId()) {
//             DPRINTF(MockingjayDebug, "Cache miss ---- Bypass cache: PC: 0x%.8x\n", pkt->req->getPC());
//             return;
//         }
//     }

//     // if(pkt->isWriteback()) {
//     //     DPRINTF(LUKAS, "2: IM A WRITEBACK. hasPC: %d\n", pkt->req->hasPC());
//     // }

//     uint64_t access_type = accessType(pkt);
//     int context_id = pkt->req->hasContextId() ? pkt->req->contextId() : 0;


//     // ETR for replacement_data should be the maximum absolute value in the whole set
//     // if (predictor->bypass(pkt->req->getPC(), casted_replacement_data->etr, false, pkt->req->contextId(), casted_replacement_data->valid)) {
//     if(!pkt->isWriteback() && !pkt->req->isPrefetch()) {
//         if(predictor->bypass(pkt->getAddr(), access_type, casted_replacement_data->abs_max_etr, false, context_id, casted_replacement_data->valid)) {
//             // DPRINTF(MockingjayDebug, "Cache miss ---- Bypass cache: PC: 0x%.8x\n", pkt->req->getPC());
//             return;
//         }
//     }

//     // DPRINTF(MockingjayDebug, "Cache miss ---- Packet type having PC: %s\n", pkt->cmdString());

//     // Warning: This is not aligned with indexing policy if it use interleave set indexing technique
//     int set = (pkt->getAddr() >> _log2_block_size) & ((1 << _log2_num_cache_sets) - 1);

//     // DPRINTF(MockingjayDebug, "Cache miss ---- Request Address: 0x%.8x, Set Index: %d, PC: 0x%.8x\n", pkt->getAddr(), set, pkt->req->getPC());

//     // Warning: Timestamp is 8-bit integer in this design
//     uint8_t curr_timestamp = 0;
//     uint8_t last_timestamp = 0;
//     uint16_t last_PC = 0;
//     bool evict = false;
//     bool sample_hit = false;

//     // Cache miss
//     // Sampled cache
//     //  1. If sampled cache hit, predictor will train with signature in the sampled cache for new reuse distance
//     //  2. If sampled cache miss and sampled cache no eviction, no training needed
//     //  3. If sampled cache miss and sampled cache eviction, the eviction line should be detrained as scan line


//     if (sampled_cache->sample(pkt->getAddr(), access_type, &curr_timestamp, set, &last_PC, &last_timestamp, false, &evict, &sample_hit, context_id, predictor->getInfRd())) {
//         predictor->train(last_PC, sample_hit, curr_timestamp, last_timestamp, evict, access_type);
//         DPRINTF(MockingjayDebug, "Cache miss ---- Sampler, Last timestamp: %d, Current timestamp: %d, Last PC: 0x%.8x\n", last_timestamp, curr_timestamp, last_PC);
//     }

//     // If aging clock reaches maximum point, then all cache lines should be aged.
//     uint64_t aging_max = (1 << _num_clock_bits) - 1;
//     if (age_ctr[set] != aging_max) {
//         age_ctr[set] += 1;
//     } else {
//         age_ctr[set] = 0;

//         for (const auto &candidate : candidates) {
//             std::shared_ptr<EEReplData> candidate_repl_data =
//                 std::static_pointer_cast<EEReplData>(
//                     candidate->replacementData);
//             candidate_repl_data->aging();
//         }
//     }

//     // replacement status update
//     // casted_replacement_data->etr = predictor->predict(pkt->getAddr(), false, pkt->req->contextId(), casted_replacement_data->abs_max_etr);
//     casted_replacement_data->etr = predictor->predict(pkt->getAddr(), access_type, false, context_id, casted_replacement_data->abs_max_etr);
//     DPRINTF(MockingjayDebug, "Cache miss ---- ETR update: %d, INF_ETR: %d\n", casted_replacement_data->etr, casted_replacement_data->abs_max_etr);
//     casted_replacement_data->valid = true;
// }

// ReplaceableEntry*
// EE::getVictim(const ReplacementCandidates& candidates) const {
//     assert(candidates.size() > 0);

//     // Use first candidate as dummy victim
//     ReplaceableEntry* victim = candidates[0];

//     // Store victim->etr in a variable to improve code readability
//     int victim_etr = std::static_pointer_cast<EEReplData>(victim->replacementData)->etr;
//     int abs_victim_etr = std::abs(victim_etr);

//     // Visit all candidates to find victim
//     for (const auto& candidate : candidates) {
//         std::shared_ptr<EEReplData> candidate_repl_data =
//             std::static_pointer_cast<EEReplData>(
//                 candidate->replacementData);

//         // Stop searching for victims if an invalid entry is found
//         if (!candidate_repl_data->valid) {
//             return candidate;
//         }

//         // Update victim entry if necessary
//         // Choose the one with maximum reuse distance (ETR allow negative value to avoid cache line s)
//         int candidate_etr = candidate_repl_data->etr;
//         int abs_candidate_etr = std::abs(candidate_etr);
//         if (abs_candidate_etr > abs_victim_etr || ((abs_candidate_etr == abs_victim_etr) && (candidate_etr < 0))) {
//             victim = candidate;
//             victim_etr = candidate_etr;
//             abs_victim_etr = abs_candidate_etr;
//         }
//     }

//     return victim;
// }

// std::shared_ptr<ReplacementData>
// EE::instantiateEntry() {
//    return std::shared_ptr<ReplacementData>(new EEReplData(_num_etr_bits));
// }

// void EE::reset(const std::shared_ptr<ReplacementData>& replacement_data) const {
//     panic("Cant train Mockingjay's predictor without access information.");
// }

// void EE::touch(const std::shared_ptr<ReplacementData>& replacement_data) const {
//     panic("Cant train Mockingjay's predictor without access information.");
// }

// void EE::reset(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt) {
//     panic("Cant train Mockingjay's predictor without all cache blocks reference. RESET DOES NOT HAVE THE REPLACEMENT CANDIDATES.");
// }

// void EE::touch(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt) {
//     panic("Cant train Mockingjay's predictor without all cache blocks reference. TOUCH DOES NOT HAVE THE REPLACEMENT CANDIDATES.");
// }

// } // namespace replacement_policy
// } // namespace gem5

#include "mem/cache/replacement_policies/ee.hh"
#include "base/logging.hh" // For fatal_if
#include "params/EE.hh"
#include "debug/MockingjayDebug.hh"
#include "debug/LUKAS.hh"

namespace gem5
{
namespace replacement_policy
{

uint64_t accessType(const PacketPtr &pkt) {
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

EE::EE(const EEParams &params)
    : Base(params),  _num_etr_bits(params.num_etr_bits) {
    sampled_cache = std::make_unique<ee::SampledCache>(params.num_sampled_sets, params.num_cache_sets, params.cache_block_size, params.timer_size, params.num_cpus, params.num_internal_sampled_sets);
    predictor = std::make_unique<ee::ReuseDistPredictor>(params.num_pred_entries, params.num_pred_bits, params.num_clock_bits, params.num_cpus);
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
EE::invalidate(const std::shared_ptr<ReplacementData>& replacement_data) {
    std::shared_ptr<EEReplData> casted_replacement_data = std::static_pointer_cast<EEReplData>(replacement_data);
    casted_replacement_data->valid = false;
    casted_replacement_data->etr = 0;
}

void
EE::touch(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt, const ReplacementCandidates& candidates) {
    std::shared_ptr<EEReplData> casted_replacement_data =
        std::static_pointer_cast<EEReplData>(replacement_data);

    // TODO: Which requests should we monitor?
    if(!(pkt->isWriteback() || pkt->req->isPrefetch())) {
        if (!pkt->isRequest() || !pkt->req->hasPC() || !pkt->req->hasContextId()) {
            return;
        }
    }

    uint64_t type = accessType(pkt);

    int contextID = pkt->req->hasContextId() ? pkt->req->contextId() : 0;

    int PC = pkt->req->hasPC() ? pkt->req->getPC() : pkt->getAddr() << 2 | type;

    DPRINTF(MockingjayDebug, "Cache hit ---- Packet type having PC: %s\n", pkt->cmdString());

    // Warning: This is not aligned with indexing policy if it use interleave set indexing technique
    int set = (pkt->getAddr() >> _log2_block_size) & ((1 << _log2_num_cache_sets) - 1);

    DPRINTF(MockingjayDebug, "Cache hit ---- Request Address: 0x%.8x, Set Index: %d, PC: 0x%.8x\n", pkt->getAddr(), set, PC);

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


    bool sample;

    if(type == 2 || type == 3) {
        DPRINTF(LUKAS, "type1: %d, addr: %x, pc: %x, set: %d, contextID: %d, predictor->getInfRd(): %d\n", type, pkt->getAddr(), PC, set, contextID, predictor->getInfRd());
        sample = sampled_cache->sample(pkt->getAddr(), PC, &curr_timestamp, set, &last_PC, &last_timestamp, true, &evict, &sample_hit, contextID, predictor->getInfRd(), true);
        DPRINTF(LUKAS, "SAMPLE1: %d\n", sample);
    } else {
        sample = sampled_cache->sample(pkt->getAddr(), PC, &curr_timestamp, set, &last_PC, &last_timestamp, true, &evict, &sample_hit, contextID, predictor->getInfRd(), false);
    }
    
    if (sample) {
        predictor->train(last_PC, sample_hit, curr_timestamp, last_timestamp, evict, type);
        DPRINTF(MockingjayDebug, "Cache hit ---- Sampler, Last timestamp: %d, Current timestamp: %d, Last PC: 0x%.8x\n", last_timestamp, curr_timestamp, last_PC);
    }

    // If aging clock reaches maximum point, then all cache lines should be aged.
    uint64_t aging_max = (1 << _num_clock_bits) - 1;
    if (age_ctr[set] != aging_max) {
        age_ctr[set] += 1;
    } else {
        age_ctr[set] = 0;

        for (const auto &candidate : candidates) {
            std::shared_ptr<EEReplData> candidate_repl_data =
                std::static_pointer_cast<EEReplData>(
                    candidate->replacementData);
            candidate_repl_data->aging();
        }
    }
    casted_replacement_data->etr = predictor->predict(PC, true, contextID, casted_replacement_data->abs_max_etr);
    DPRINTF(MockingjayDebug, "Cache hit ---- ETR update: %d, INF_ETR: %d\n", casted_replacement_data->etr, casted_replacement_data->abs_max_etr);
}

void
EE::reset(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt, const ReplacementCandidates& candidates) {
    std::shared_ptr<EEReplData> casted_replacement_data =
        std::static_pointer_cast<EEReplData>(replacement_data);
    
    // TODO: Which requests should we monitor?
    if ((!pkt->isRequest() || !pkt->req->hasPC() || !pkt->req->hasContextId()) && (!pkt->isWriteback() || !pkt->req->isPrefetch())) {
        return;
    }

    // ETR for replacement_data should be the maximum absolute value in the whole set
    if(!(pkt->isWriteback() || pkt->req->isPrefetch())) {
        if (!pkt->isRequest() || !pkt->req->hasPC() || !pkt->req->hasContextId()) {
            DPRINTF(MockingjayDebug, "Cache miss ---- Bypass cache: PC: 0x%.8x\n", pkt->req->getPC());
            return;
        }
    }

    uint64_t type = accessType(pkt);

    int contextID = pkt->req->hasContextId() ? pkt->req->contextId() : 0;

    int PC = pkt->req->hasPC() ? pkt->req->getPC() : pkt->getAddr() << 2 | type;

    DPRINTF(MockingjayDebug, "Cache miss ---- Packet type having PC: %s\n", pkt->cmdString());

    // Warning: This is not aligned with indexing policy if it use interleave set indexing technique
    int set = (pkt->getAddr() >> _log2_block_size) & ((1 << _log2_num_cache_sets) - 1);

    DPRINTF(MockingjayDebug, "Cache miss ---- Request Address: 0x%.8x, Set Index: %d, PC: 0x%.8x\n", pkt->getAddr(), set, PC);

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

    bool sample;

    if(type == 2 || type == 3) {
        DPRINTF(LUKAS, "type2: %d, addr: %x, pc: %x, set: %d, contextID: %d, predictor->getInfRd(): %d\n", type, pkt->getAddr(), PC, set, contextID, predictor->getInfRd());
        sample = sampled_cache->sample(pkt->getAddr(), PC, &curr_timestamp, set, &last_PC, &last_timestamp, false, &evict, &sample_hit, contextID, predictor->getInfRd(), true);
        DPRINTF(LUKAS, "SAMPLE2: %d\n", sample);
    } else {
        sample = sampled_cache->sample(pkt->getAddr(), PC, &curr_timestamp, set, &last_PC, &last_timestamp, false, &evict, &sample_hit, contextID, predictor->getInfRd(), false);
    }

    if (sample) {
        predictor->train(last_PC, sample_hit, curr_timestamp, last_timestamp, evict, type);
        DPRINTF(MockingjayDebug, "Cache miss ---- Sampler, Last timestamp: %d, Current timestamp: %d, Last PC: 0x%.8x\n", last_timestamp, curr_timestamp, last_PC);
    }

    // If aging clock reaches maximum point, then all cache lines should be aged.
    uint64_t aging_max = (1 << _num_clock_bits) - 1;
    if (age_ctr[set] != aging_max) {
        age_ctr[set] += 1;
    } else {
        age_ctr[set] = 0;

        for (const auto &candidate : candidates) {
            std::shared_ptr<EEReplData> candidate_repl_data =
                std::static_pointer_cast<EEReplData>(
                    candidate->replacementData);
            candidate_repl_data->aging();
        }
    }

    // replacement status update
    casted_replacement_data->etr = predictor->predict(pkt->getAddr(), false, contextID, casted_replacement_data->abs_max_etr);
    DPRINTF(MockingjayDebug, "Cache miss ---- ETR update: %d, INF_ETR: %d\n", casted_replacement_data->etr, casted_replacement_data->abs_max_etr);
    casted_replacement_data->valid = true;
}

ReplaceableEntry*
EE::getVictim(const ReplacementCandidates& candidates) const {
    assert(candidates.size() > 0);

    // Use first candidate as dummy victim
    ReplaceableEntry* victim = candidates[0];

    // Store victim->etr in a variable to improve code readability
    int victim_etr = std::static_pointer_cast<EEReplData>(victim->replacementData)->etr;
    int abs_victim_etr = std::abs(victim_etr);

    // Visit all candidates to find victim
    for (const auto& candidate : candidates) {
        std::shared_ptr<EEReplData> candidate_repl_data =
            std::static_pointer_cast<EEReplData>(
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
EE::instantiateEntry() {
   return std::shared_ptr<ReplacementData>(new EEReplData(_num_etr_bits));
}

void EE::reset(const std::shared_ptr<ReplacementData>& replacement_data) const {
    panic("Cant train Mockingjay's predictor without access information.");
}

void EE::touch(const std::shared_ptr<ReplacementData>& replacement_data) const {
    panic("Cant train Mockingjay's predictor without access information.");
}

void EE::reset(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt) {
    panic("Cant train Mockingjay's predictor without all cache blocks reference. RESET DOES NOT HAVE THE REPLACEMENT CANDIDATES.");
}

void EE::touch(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt) {
    panic("Cant train Mockingjay's predictor without all cache blocks reference. TOUCH DOES NOT HAVE THE REPLACEMENT CANDIDATES.");
}

} // namespace replacement_policy
} // namespace gem5

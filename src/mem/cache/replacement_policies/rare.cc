#include "mem/cache/replacement_policies/rare.hh"
#include "params/RARE.hh"

#include <cassert>
#include <memory>
#include "sim/cur_tick.hh"

#define EVICTION_RANK_NUM 4

// TODO FIXME: See lru_rp.cc/.hh for reference.

namespace gem5 {
    namespace replacement_policy {

        RARE::RARE(const RAREParams &params) : Base(params) // TODO: Add more params here
        {

        }

        void
        RARE::invalidate(const std::shared_ptr<ReplacementData>& replacement_data)
        {
            std::static_pointer_cast<RAREReplData>(replacement_data)->lastTouchTick = Tick(0);
            std::static_pointer_cast<RAREReplData>(replacement_data)->rank_num = EVICTION_RANK_NUM;
        }

        void
        RARE::touch(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt) {
            // TODO FIXME: this block has been accessed, update its replacement data
            std::static_pointer_cast<RAREReplData>(replacement_data)->lastTouchTick = curTick();
            std::static_pointer_cast<RAREReplData>(replacement_data)->rank_num = ((pkt->getAddr() & 0x40000) << 1) + (pkt->getAddr() & 0x40);
        }

        void
        RARE::touch(const std::shared_ptr<ReplacementData>& replacement_data) const {
            panic("Can't train without access information.");
        }

        void
        RARE::reset(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt) {
            // TODO FIXME: this block is newly inserted into the cache, reset its replacement
            // data to the insertion state
            std::static_pointer_cast<RAREReplData>(replacement_data)->lastTouchTick = curTick();
            std::static_pointer_cast<RAREReplData>(replacement_data)->rank_num = ((pkt->getAddr() & 0x40000) << 1) + (pkt->getAddr() & 0x40);
        }

        void
        RARE::reset(const std::shared_ptr<ReplacementData>& replacement_data) const {
            panic("Can't train without access information.");
        }

        ReplaceableEntry* RARE::getVictim(const ReplacementCandidates& candidates) const {
            assert(candidates.size() > 0);

            uint64_t tick = curTick();

            uint64_t special_rank_0;
            uint64_t special_rank_1;

            if ((tick / 10000000) % 4 == 0) {
                special_rank_0 = 0;
                special_rank_1 = 1;
            } else if ((tick / 10000000) % 4 == 1) {
                special_rank_0 = 1;
                special_rank_1 = 2;
            } else if ((tick / 10000000) % 4 == 2) {
                special_rank_0 = 2;
                special_rank_1 = 3;
            } else {
                special_rank_0 = 3;
                special_rank_1 = 0;
            }

            ReplaceableEntry* victim = nullptr;
            for (const auto& candidate : candidates) {
                if (std::static_pointer_cast<RAREReplData>(candidate->replacementData)->rank_num == special_rank_0 || std::static_pointer_cast<RAREReplData>(candidate->replacementData)->rank_num == special_rank_1) {
                    continue;
                }

                if (std::static_pointer_cast<RAREReplData>(candidate->replacementData)->rank_num == EVICTION_RANK_NUM) {
                    return candidate;
                }

                if (victim == nullptr) {
                    victim = candidate;
                    continue;
                }

                // Update victim entry if necessary
                if (std::static_pointer_cast<RAREReplData>(candidate->replacementData)->lastTouchTick <std::static_pointer_cast<RAREReplData>(victim->replacementData)->lastTouchTick) {
                    victim = candidate;
                }
            }

            if (victim != nullptr) {
                return victim;
            }

            victim = candidates[0];
            for (const auto& candidate : candidates) {
                // Update victim entry if necessary
                if (std::static_pointer_cast<RAREReplData>(
                            candidate->replacementData)->lastTouchTick <
                        std::static_pointer_cast<RAREReplData>(
                            victim->replacementData)->lastTouchTick) {
                    victim = candidate;
                }
            }

            return victim;
        }

        std::shared_ptr<ReplacementData> RARE::instantiateEntry() {
            return std::shared_ptr<ReplacementData>(new RAREReplData());
        }

    } // namespace replacement_policy
} // namespace gem5

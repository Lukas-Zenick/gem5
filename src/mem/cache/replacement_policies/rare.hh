#ifndef __MEM_CACHE_REPLACEMENT_POLICIES_RARE_HH__
#define __MEM_CACHE_REPLACEMENT_POLICIES_RARE_HH__

#include "base/sat_counter.hh"
#include "base/types.hh"
#include "mem/cache/replacement_policies/base.hh"

namespace gem5 {

    struct RAREParams;

    namespace replacement_policy {

        class RARE : public Base {
            protected:
                struct RAREReplData : ReplacementData
                {
                    Tick lastTouchTick;
                    uint32_t rank_num;

                    // constructor (default creation data state)
                    RAREReplData() : lastTouchTick(0), rank_num(0) { }
                };

            public:
                typedef RAREParams Params;
                RARE(const RAREParams &params);
                ~RARE() = default;

                void invalidate(const std::shared_ptr<ReplacementData>& replacement_data) override;
                
                void touch(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt) override;
                void touch(const std::shared_ptr<ReplacementData>& replacement_data) const override;

                void reset(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt) override;
                void reset(const std::shared_ptr<ReplacementData>& replacement_data) const override;

                ReplaceableEntry* getVictim(const ReplacementCandidates& candidates) const override;

                std::shared_ptr<ReplacementData> instantiateEntry() override;
        };

    } // namespace replacement_policy
} // namespace gem5

#endif // __MEM_CACHE_REPLACEMENT_POLICIES_RARE_RP_HH__

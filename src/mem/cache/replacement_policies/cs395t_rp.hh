#ifndef __MEM_CACHE_REPLACEMENT_POLICIES_CS395T_RP_HH__
#define __MEM_CACHE_REPLACEMENT_POLICIES_CS395T_RP_HH__

#include "base/sat_counter.hh"
#include "base/types.hh"
#include "mem/cache/replacement_policies/base.hh"
#include "mem/cache/tags/mockingjay_sampler.hh"

namespace gem5
{

struct CS395TRPParams;

namespace replacement_policy
{

class CS395TRP : public Base
{
    protected:
        struct CS395TReplData : ReplacementData
        {
            int8_t etr;
            const int abs_max_etr;

            /** Whether the entry is valid. */
            bool valid;

            void aging() {
            if (std::abs(etr) < abs_max_etr) {
                etr -= 1;
            }
            }

            /**
             * Default constructor. Invalidate data.
             */
            CS395TReplData(const int num_bits) : etr(0), abs_max_etr((1 << (num_bits - 1)) - 1), valid(false) {}
        };

    public:
        typedef CS395TRPParams Params;
        CS395TRP(const CS395TRPParams &params);
        ~CS395TRP() = default;

        /** History Sampler */
        std::unique_ptr<SampledCache> sampled_cache;

        /** Reuse Distance Predictor */
        std::unique_ptr<ReuseDistPredictor> predictor;

        /** Number of bits of ETR counter */
        const int _num_etr_bits;

        /** Clock age counter for each set */
        std::vector<uint8_t> age_ctr;

        /** Number of bits of target cache block size */
        int _log2_block_size;

        /** Number of bits of target cache sets */
        int _log2_num_cache_sets;

        /** Numer of bits of aging clock */
        int _num_clock_bits;

        void invalidate(const std::shared_ptr<ReplacementData>& replacement_data) override;
        
        void touch(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt, const ReplacementCandidates& candidates) override;
        void touch(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt) override;
        void touch(const std::shared_ptr<ReplacementData>& replacement_data) const override;

        void reset(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt, const ReplacementCandidates& candidates) override;
        void reset(const std::shared_ptr<ReplacementData>& replacement_data, const PacketPtr pkt) override;
        void reset(const std::shared_ptr<ReplacementData>& replacement_data) const override;

        ReplaceableEntry* getVictim(const ReplacementCandidates& candidates) const override;

        std::shared_ptr<ReplacementData> instantiateEntry() override;
};

} // namespace replacement_policy
} // namespace gem5

#endif // __MEM_CACHE_REPLACEMENT_POLICIES_CS395T_RP_HH__

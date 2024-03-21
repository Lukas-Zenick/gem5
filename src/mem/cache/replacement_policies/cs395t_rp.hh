#ifndef __MEM_CACHE_REPLACEMENT_POLICIES_CS395T_RP_HH__
#define __MEM_CACHE_REPLACEMENT_POLICIES_CS395T_RP_HH__

#include "mem/cache/replacement_policies/base.hh"

namespace gem5
{

struct CS395TRPParams;

namespace replacement_policy
{

class CS395TRP : public Base
{
    protected:
        const unsigned example_size; // example parameter.
        // TODO: Add more params here

        // Custom replacement data
        struct CS395TReplData : ReplacementData
        {
            // constructor (default creation data state)
            CS395TReplData() { }
        };

    public:
        CS395TRP(const CS395TRPParams &params);
        ~CS395TRP() = default;

        void invalidate(const std::shared_ptr<ReplacementData>& replacement_data)
                                                                        override;
        void touch(const std::shared_ptr<ReplacementData>& replacement_data)
                                                            const override;
        void reset(const std::shared_ptr<ReplacementData>& replacement_data)
                                                            const override;
        ReplaceableEntry* getVictim(const ReplacementCandidates& candidates)
                                                             const override;
        std::shared_ptr<ReplacementData> instantiateEntry() override;
};

} // namespace replacement_policy
} // namespace gem5

#endif // __MEM_CACHE_REPLACEMENT_POLICIES_CS395T_RP_HH__

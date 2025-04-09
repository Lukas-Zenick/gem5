#!/bin/bash
#
# runScript.sh
#
# Usage:
#   1) chmod +x runScript.sh
#   2) ./runScript.sh
#        → Parses the current directory's stats.txt → writes newStats.txt
#   3) ./runScript.sh -global
#        → Expects current directory to have multiple subfolders, each of which
#          may contain a stats.txt. For each subfolder:
#             - Parse stats.txt in that subfolder (if present) into subfolder's newStats.txt
#             - Extract the IPC from there
#          Then in the current “parent” directory, it creates globalNewStats.txt
#          listing each subfolder's name and IPC value (or blank if not found).
#
# The logic for extracting stats is basically the same as our original single-folder script:
#   - We parse simInsts, simTicks, simFreq.
#   - Convert ticks to CPU cycles, using CPU_FREQ_GHZ=3 by default (adjust if needed).
#   - Compute IPC = simInsts / CPU cycles.
#   - Summation of L1-D hits/misses across l1_controllers0..3 for a system-wide L1-D miss rate.
#   - Output is written to newStats.txt in that folder.
#
# If -global is used, we do that for each subfolder in alphabetical order, and
# also produce globalNewStats.txt here in the parent, with lines like:
#   SubfolderName, 123.456
#   NextFolderName,
# etc.  (blank if no IPC)
#
# ─────────────────────────────────────────────────────────────────────
# Methodology/Commentary:
#   1. We interpret stats.txt's "simInsts" as the total instructions
#      committed across all cores in the system. If you have multiple
#      cores/threads, "simInsts" is an aggregate sum.
#   2. We parse "simTicks" and "simFreq" to figure out how many CPU cycles
#      were simulated. By default, the run script sets board.clk_freq="3GHz".
#      So if the script says 3 GHz, that means each CPU cycle = 1 / 3e9 s,
#      or 333 ps. gem5 often uses simFreq=1e12 ticks/second, meaning each
#      tick = 1 ps. We do: CPU cycles = simTicks * (3e9 / 1e12) in that scenario.
#   3. "IPC" is then total instructions / total CPU cycles. This is a whole-system
#      average across all cores. If you want “per-core” IPC, you could do:
#        Per-core IPC = (per-core committedInsts) / cycles
#      but gem5’s default "simInsts" is typically a system sum.
#   4. We sum the L1 data cache hits/misses from each of 4 controllers: l1_controllers0..3.
#      If you have more/fewer cores, change numControllers. The script then
#      prints total L1 misses, total L1 hits, and the ratio (miss / total).
#   5. If you run multiple benchmarks/policies, you can run this script on each stats.txt
#      and record the results in newStats.txt. For geomean, you’d gather all results
#      externally (e.g., in a spreadsheet or separate aggregator script).
# ─────────────────────────────────────────────────────────────────────

CPU_FREQ_GHZ=3   # CPU frequency used in the gem5 board (3 GHz default)
OUTFILE="newStats.txt"
GLOBAL_OUTFILE="globalNewStats.txt"

# ------------------------------------------------------------------------------
#  Function: parse_folder
#     Takes one directory path as $1, tries to parse "stats.txt" in it.
#     Writes newStats.txt in that folder. Returns the IPC string or blank.
# ------------------------------------------------------------------------------
parse_folder() {
    local folder="$1"
    local statsFile="${folder}/stats.txt"
    local newStatsFile="${folder}/${OUTFILE}"

    # If stats.txt not found or empty, just write minimal newStats and return.
    if [ ! -s "$statsFile" ]; then
        echo ""
        > "$newStatsFile"
        echo ""  # Return blank for IPC
        return
    fi

    # Grab lines from stats.txt
    local simInsts simTicks simFreq
    simInsts=$(grep -m1 '^simInsts' "$statsFile" | awk '{print $2}')
    simTicks=$(grep -m1 '^simTicks' "$statsFile" | awk '{print $2}')
    simFreq=$( grep -m1 '^simFreq'  "$statsFile" | awk '{print $2}')

    # Prepare newStats.txt
    cat /dev/null > "$newStatsFile"

    # Basic checks
    if [ -z "$simInsts" ] || [ -z "$simTicks" ] || [ -z "$simFreq" ]; then
        echo "Error: missing simInsts/simTicks/simFreq in $folder." >> "$newStatsFile"
        echo ""  # Return blank for IPC
        return
    fi

    # Convert ticks → CPU cycles
    local cpuHz cycles ipc
    cpuHz=$(awk -v ghz="$CPU_FREQ_GHZ" 'BEGIN{printf "%.0f", ghz*1e9}')
    cycles=$(awk -v st="$simTicks" -v sf="$simFreq" -v cf="$cpuHz" \
             'BEGIN{printf "%.0f", st*cf/sf}')
    ipc=$(awk -v inst="$simInsts" -v cyc="$cycles" \
             'BEGIN{ if(cyc==0) {printf "0"} else {printf "%.4f", inst/cyc} }')

    # L1-D aggregator: sum hits/misses across 4 controllers
    local numControllers=4
    local totalHits=0
    local totalMiss=0

    for i in $(seq 0 $((numControllers-1))); do
        local h m
        h=$(grep -m1 "l1_controllers${i}\.L1Dcache\.m_demand_hits" "$statsFile"    | awk '{print $2}')
        m=$(grep -m1 "l1_controllers${i}\.L1Dcache\.m_demand_misses" "$statsFile" | awk '{print $2}')
        h=${h:-0}
        m=${m:-0}
        totalHits=$((totalHits + h))
        totalMiss=$((totalMiss + m))
    done

    local sumAccess=$((totalHits + totalMiss))
    local l1MissRate="0.0000"
    if [ "$sumAccess" -gt 0 ]; then
        l1MissRate=$(awk -v h="$totalHits" -v m="$totalMiss" 'BEGIN{printf "%.4f", m/(m+h)}')
    fi

    # Write results
    {
        echo "===== gem5 Basic Stats ====="
        echo "simInsts:            $simInsts"
        echo "simTicks:            $simTicks"
        echo "simFreq:             $simFreq"
        echo "Calculated CPU cycles (assuming ${CPU_FREQ_GHZ} GHz): $cycles"
        echo "IPC (system-wide):   $ipc"
        echo
        echo "----- Summed L1-D Demand Accesses (4 controllers) -----"
        echo "L1-D total hits:     $totalHits"
        echo "L1-D total misses:   $totalMiss"
        echo "L1-D miss rate:      $l1MissRate"
    } >> "$newStatsFile"

    # Return the IPC value via stdout
    echo "$ipc"
}

# ------------------------------------------------------------------------------
# Main script logic
# ------------------------------------------------------------------------------
if [ "$1" == "-global" ]; then
    # 1) Clear out or create a fresh globalNewStats.txt in the current directory
    > "$GLOBAL_OUTFILE"

    # 2) Loop over subfolders in alphabetical order
    #    For each subfolder, parse stats, produce local newStats.txt
    #    Then collect the IPC from parse_folder
    #    Print "FolderName, IPC" into globalNewStats.txt

    # A subfolder matches "*/" in a for-loop. We'll trim trailing slash for the key.
    for d in */; do
        [ -d "$d" ] || continue  # skip non-directories
        folderName=$(basename "$d")  # e.g. "A" or "B" etc.

        echo "Processing subfolder: $folderName ..."
        ipcVal=$(parse_folder "$d")  # calls parse_folder, which outputs the IPC or blank
        echo "${folderName}, ${ipcVal}" >> "$GLOBAL_OUTFILE"
    done

    echo "All done. See $GLOBAL_OUTFILE for global consolidated IPC list."

else
    # No -global flag => just parse the local folder's stats.txt => local newStats.txt
    echo "Parsing stats in the current folder only..."
    # We'll call parse_folder "." but not capture its IPC, since not needed
    parse_folder "."
    echo "Done. Generated $OUTFILE in the current directory."
fi

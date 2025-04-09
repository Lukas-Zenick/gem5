#!/bin/bash

###############################################################################
# Bash script to run multi-threaded MESI-Two-Level Ruby simulations in gem5.
# Invokes a separate Python config script for each job. Each job runs in tmux.
# Usage:
#   ./zGPTrun.sh <L2_REPL_POLICY>
# Example:
#   ./zGPTrun.sh LRU
###############################################################################

# --[ User Configuration ]-----------------------------------------------------

# 1) Which benchmarks do you want to run, and how many instructions to run?
#    For simplicity we provide an example with only a single benchmark and
#    a small number of instructions. Modify as desired.
declare -A benchmarks=(
    ["facesim"]="250"      # This means: ROI interval = 1000M instructions, etc.
)

# 2) The path to your gem5 binary (MESI Two-Level build).
#    Adjust this to reflect wherever you built gem5 with the Ruby MESI protocol.
GEM5_BIN="$GEM5_HOME/build/X86_MESI_Two_Level/gem5.opt"

# 3) Where to store simulation outputs and final results.
OUTDIR_BASE="./GPT/large-maxinst/outdir"
RESULTS_BASE="./GPT/large-maxinst/resultsdir"

# 4) Some default global parameters for your sampling logic:
#    (Note: It's up to you how you want to interpret these in Python.)
FF_INTERVAL=100            # e.g. 100 million instructions fast-forward
WARMUP_INTERVAL=50         # 50 million instructions warmup
ROI_INTERVAL=250           # 200 million instructions ROI
MAX_ROIS=2                 # Example: Collect 2 ROI intervals, then stop
BENCHMARK_SIZE="large"    # e.g. parsec "simmedium"
NUM_PHYSICAL_CORES="1"     # Example: 1 core
NUM_HW_THREADS="2"         # Example: 2 threads per core => "SMT"

# 5) Additional settings:
TIMEOUT_HOURS=12           # Each run is given a 12-hour timeout
DEBUG="0"                  # Set to "1" to run under gdb, for debug
###############################################################################

# Check usage
if [ "$#" -lt 1 ]; then
  echo "ERROR: No L2 replacement policy specified."
  echo "Usage: $0 <L2_REPL_POLICY>"
  exit 1
fi
L2_REPL_POLICY="$1"

# Create directories if needed
mkdir -p "${OUTDIR_BASE}"
mkdir -p "${RESULTS_BASE}"

# Iterate over benchmarks
for BENCHMARK in "${!benchmarks[@]}"; do

    ROI_INSTR_MILLIONS=${benchmarks[$BENCHMARK]}

    # Construct output and result directories for this benchmark/policy
    OUTDIR="${OUTDIR_BASE}/${BENCHMARK}_${L2_REPL_POLICY}"
    RESULTSDIR="${RESULTS_BASE}/${BENCHMARK}_${L2_REPL_POLICY}"
    mkdir -p "$OUTDIR"
    mkdir -p "$RESULTSDIR"

    # Decide on the gem5 command line
    # We'll pass all relevant parameters to the Python script.
    if [ "$DEBUG" = "1" ]; then
        echo "Running in debug mode (gdb)."
        # Debug mode: run with GDB, no timeout, pipe gem5 output to logs
        CMD="gdb --args \
            $GEM5_BIN \
            --outdir=$OUTDIR \
            ./gem5-configs-395t/zGPTmesi.py \
            --benchmark $BENCHMARK \
            --size $BENCHMARK_SIZE \
            --l2_replacement_policy $L2_REPL_POLICY \
            --physical_cores $NUM_PHYSICAL_CORES \
            --threads_per_core $NUM_HW_THREADS \
            --sample --max_rois $MAX_ROIS \
            $FF_INTERVAL $WARMUP_INTERVAL $ROI_INTERVAL \
            1> ${RESULTSDIR}/stdout.log 2> ${RESULTSDIR}/stderr.log"
    else
        echo "Running in normal mode (timeout)."
        # Normal mode: impose a timeout, run gem5, redirect logs
        CMD="timeout ${TIMEOUT_HOURS}h \
            $GEM5_BIN \
            --outdir=$OUTDIR \
            ./gem5-configs-395t/zGPTmesi.py \
            --benchmark $BENCHMARK \
            --size $BENCHMARK_SIZE \
            --l2_replacement_policy $L2_REPL_POLICY \
            --physical_cores $NUM_PHYSICAL_CORES \
            --threads_per_core $NUM_HW_THREADS \
            --sample --max_rois $MAX_ROIS \
            $FF_INTERVAL $WARMUP_INTERVAL $ROI_INTERVAL \
            1> ${RESULTSDIR}/stdout.log 2> ${RESULTSDIR}/stderr.log"
    fi

    # Create a unique tmux session name
    SESSION_NAME="mesi_${BENCHMARK}_${L2_REPL_POLICY}_$(date +%Y%m%d_%H%M%S)"

    # Launch in tmux (detached)
    tmux new-session -d -s "${SESSION_NAME}" "${CMD}"

    echo "[LAUNCHED] Benchmark: $BENCHMARK, L2 Policy: $L2_REPL_POLICY, Session: $SESSION_NAME"
done

echo "All runs have been launched in tmux sessions."
echo "Use 'tmux ls' or 'tmux attach -t <session>' to inspect them."

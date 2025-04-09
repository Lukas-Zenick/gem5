#!/bin/bash

# Declare benchmarks and their parameters
declare -A benchmarks=(
    ["facesim"]="8600"
)

# declare -A benchmarks=(
#     ["blackscholes"]="200"
#     ["bodytrack"]="700"
#     ["canneal"]="2100"
#     ["dedup"]="300"
#     ["facesim"]="8600"
#     ["ferret"]="200"
#     ["fluidanimate"]="300"
#     ["freqmine"]="200"
#     ["raytrace"]="43200"
#     ["streamcluster"]="200"
#     ["swaptions"]="200"
#     ["vips"]="200"
#     ["x264"]="2500"
# )

# declare -A benchmarks=( ["facesim"]="8600" ["bodytrack"]="700" )

declare -A binaries=(
    ["default"]="$GEM5_HOME/build/X86_MESI_Two_Level/gem5.opt"
)

OUT=./lukas/1/outdir
RESULTS=./lukas/1/resultsdir

mkdir -p "${RESULTS}"
mkdir -p "${OUT}"

# GEM5_FLAGS: uncomment or add any global flags you might need
GEM5_FLAGS=""

# Tunable parameters
cores="4"  # example: single core count; add more if needed
ROI=1000 # one billion instructions
WARMUP=50 # 50 million instructions
FF=1000 # one billion instructions
L2_REPL_POLICY=$1  # provided as first command-line argument

# Loop over all combinations
for CORE_COUNT in $cores; do
    for BENCHMARK in "${!benchmarks[@]}"; do
        for POLICY in "${!binaries[@]}"; do
            SIM=${binaries[$POLICY]}
            echo "Queueing ${BENCHMARK} with ${CORE_COUNT} cores using ${POLICY} policy - Sim: ${SIM}"

            OUTDIR=${OUT}/${L2_REPL_POLICY}/${BENCHMARK}_${POLICY}_${CORE_COUNT}_cores
            RESULTS_DIR=${RESULTS}/${L2_REPL_POLICY}/${BENCHMARK}_${POLICY}_${CORE_COUNT}_cores
            mkdir -p "${OUTDIR}"
            mkdir -p "${RESULTS_DIR}"

            # Create a temporary flags variable so GEM5_FLAGS doesn't accumulate multiple outdir options
            current_flags="${GEM5_FLAGS} --outdir=${OUTDIR}"

            # Build the command to run
            if [ "$DEBUG" = "1" ]; then
                cmd="gdb --args $SIM $current_flags ./gem5-configs-395t/run_fs_mesi_two_level.py \
--benchmark ${BENCHMARK} --l2_replacement_policy ${L2_REPL_POLICY} --size medium \
--cores ${CORE_COUNT} --max_rois 1 --sample ${FF} ${WARMUP} ${ROI}"
            else
                cmd="timeout 12h $SIM $current_flags ./gem5-configs-395t/run_fs_mesi_two_level.py \
--benchmark ${BENCHMARK} --l2_replacement_policy ${L2_REPL_POLICY} --size medium \
--cores ${CORE_COUNT} --max_rois 1 --sample ${FF} ${WARMUP} ${ROI} \
2> ${RESULTS_DIR}/stderr.log 1> ${RESULTS_DIR}/stdout.log"
            fi

            # Define a unique tmux session name (avoid spaces/special characters)
            session_name="${L2_REPL_POLICY}_${BENCHMARK}_${POLICY}_${CORE_COUNT}"

            # Launch the command in a new detached tmux session
            tmux new-session -d -s "$session_name" "$cmd"
            echo "Started tmux session '$session_name'"
        done
    done
done

echo "All jobs have been queued in tmux sessions."

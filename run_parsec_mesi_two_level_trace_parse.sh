#!/bin/bash

# Currently only using the benchmark names here, but you can consider having per-benchmark parameters (for example, ROI length)
declare -A benchmarks=( ["blackscholes"]="200 " ["bodytrack"]="700" ["canneal"]="2100" ["dedup"]="300" \
                        ["facesim"]="8600" ["ferret"]="200" ["fluidanimate"]="300" ["freqmine"]="200" \
                        ["raytrace"]="43200" ["streamcluster"]="200" ["swaptions"]="200" ["vips"]="200" \
                        ["x264"]="2500" )

declare -A binaries=( ["default"]="$GEM5_HOME/build/X86_MESI_Two_Level/gem5.opt" \
                       )

OUT=./jake/outdir
RESULTS=./jake/resultsdir

mkdir -p ${RESULTS}
mkdir -p ${OUT}

GEM5_FLAGS=""
# To enable protocol trace with compressed output, uncomment the following line
# GEM5_FLAGS+="--debug-flags=ProtocolTrace --debug-file=${RESULTS_DIR}/trace.out.gz "

# The following parameters should be tuned
cores="4 8 12"
ROI=1000
WARMUP=50
# Very large fast-forward interval because we wait for parsec benchmark to send a signal to start
FF=1000000
L2_REPL_POLICY=$1


# Run each benchmark with each number of cores
for CORE_COUNT in $cores;
do
    for BENCHMARK in "${!benchmarks[@]}";
    do
        for POLICY in "${!binaries[@]}";
        do
            SIM=${binaries[$POLICY]};
            echo "Running ${BENCHMARK} with ${CORE_COUNT} cores using ${POLICY} policy - Sim: ${SIM}"


            OUTDIR=${OUT}/${L2_REPL_POLICY}/${BENCHMARK}_${POLICY}_${CORE_COUNT}_cores
            RESULTS_DIR=${RESULTS}/${L2_REPL_POLICY}/${BENCHMARK}_${POLICY}_${CORE_COUNT}_cores
            GEM5_FLAGS+="--outdir=${OUTDIR} "

            mkdir -p ${OUTDIR}
            mkdir -p ${RESULTS_DIR}

            printf "Benchmark: ${BENCHMARK}\n Cores: ${CORE_COUNT}\nROI: ${ROI}\nWarmup: ${WARMUP}\nFF: ${FF}\n"

            timeout 12h \
            $SIM $GEM5_FLAGS \
            ./gem5-configs-395t/run_fs_mesi_two_level.py \
            --benchmark $BENCHMARK \
            --l2_replacement_policy $L2_REPL_POLICY \
            --size medium \
            --cores ${CORE_COUNT} --max_rois 1 --sample $FF $WARMUP $ROI \
            2> ${RESULTS_DIR}/stderr.log \
            1> ${RESULTS_DIR}/stdout.log &
            sleep 1800;
            # if job count >= 2, wait
            if [ $(jobs -r -p | wc -l) -gt 1 ]; then
                wait
            fi
        done
    done
done

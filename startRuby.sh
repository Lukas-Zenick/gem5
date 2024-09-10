#!/bin/bash

# Check if exactly two parameters are provided
# if [ "$#" -eq 2 ]; then
#     llc_repl="$1"
#     benchmark="$2"

#     output="$llc_repl/$benchmark"
# elif [ "$#" -eq 3 ]; then
#     llc_repl="$1"
#     optional="$2"
#     benchmark="$3"

#     output="$llc_repl-$optional/$benchmark"
# else
#     echo "Usage: $0 <llc_replacement> [optional] <benchmark>"
#     exit 1
# fi

llc_repl="$1"

# pythonScript="./gem5-configs-395t/se_single_thread.py"
pythonScript="/scratch/cluster/lukas/gem5-research/configs/learning_gem5/part3/lukas-threaded.py"

bpred="perceptron"
cores=1
start_core_type="kvm"
switch_core_type="o3"

l1d_size="32KiB"
l1d_assoc="8"
l1d_pref="no"
l1d_repl="lru"

l1i_size="32KiB"
l1i_assoc="8"
l1i_pref="no"
l1i_repl="lru"

l2_size="256KiB"
l2_assoc="8"
l2_pref="no"
l2_repl="lru"

llc_size="2MiB"
llc_assoc="16"
llc_pref="no"
#llc_repl=$1 #LLC REPLACEMENT POLICY

ff=10000
warmup=25
roi=50
init_ff=50000
max_rois=3


./build/X86_MSI/gem5.opt --outdir=./results/ruby/"$output" "$pythonScript" --cores=4 --bpred="$bpred" --cores="$cores" --start_core_type="$start_core_type" --switch_core_type="$switch_core_type" \
--l1d_size="$l1d_size" --l1d_assoc="$l1d_assoc" --l1d_pref="$l1d_pref" --l1d_repl="$l1d_repl" --l1i_size="$l1i_size" --l1i_assoc="$l1i_assoc" --l1i_pref="$l1i_pref" --l1i_repl="$l1i_repl" \
--l2_size="$l2_size" --l2_assoc="$l2_assoc" --l2_pref="$l2_pref" --l2_repl="$l2_repl" --llc_size="$llc_size" --llc_assoc="$llc_assoc" --llc_pref="$llc_pref" --llc_repl="$llc_repl" \
--ff="$ff" --warmup="$warmup" --roi="$roi" --init_ff="$init_ff" --max_rois="$max_rois"

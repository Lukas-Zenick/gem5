#!/bin/bash

# Function to run gem5 command with given X and Y values
run_gem5() {
    local X=$1
    local Y=$2
    local session_name="gem5_${X}_${Y}"

    # Replace X and Y values in the gem5 command
    cmd="./build/X86/gem5.opt --outdir=output/$X/$Y gem5-configs-395t/fs_spec06gap_with_sampling.py --benchmark $X --init_ff 50000 --ff 10000 --warmup 25 --roi 50 --max_rois 3 --llc_repl $Y"
    # cmd="./build/X86/gem5.opt --debug-flags=LUKAS --outdir=output/$X/$Y gem5-configs-395t/fs_spec06gap_with_sampling.py --benchmark $X --init_ff 50000 --ff 10000 --warmup 25 --roi 50 --max_rois 3 --llc_repl $Y"

    # Run the gem5 command in a new tmux session
    tmux new-session -d -s "$session_name" "$cmd"
}

# Input X value
read -p "Job Name: " X

# Array of Y values
Y=("lru" "rare" "cs395t" "rpc")
# Y=("ee")

# Run gem5 command for each Y value in separate tmux sessions
for y_value in "${Y[@]}"; do
    run_gem5 "$X" "$y_value"
done

#!/bin/bash

# Define the input and output file names
input_file="stats.txt"
output_ipc_file="z_IPC.txt" # New output file for IPC stats

# Check if the input file exists
if [ ! -f "$input_file" ]; then
    echo "Input file $input_file not found."
    exit 1
fi

# Temporary files to store intermediate results
tmp_switch0=$(mktemp)
tmp_switch1=$(mktemp)
tmp_switch2=$(mktemp)
tmp_switch3=$(mktemp)

# Extract IPC stats for each switch
grep -E "board.processor.switch0.core.ipc" "$input_file" | awk '{print $2}' | sed 's/nan//g' > "$tmp_switch0"
grep -E "board.processor.switch1.core.ipc" "$input_file" | awk '{print $2}' | sed 's/nan//g' > "$tmp_switch1"
grep -E "board.processor.switch2.core.ipc" "$input_file" | awk '{print $2}' | sed 's/nan//g' > "$tmp_switch2"
grep -E "board.processor.switch3.core.ipc" "$input_file" | awk '{print $2}' | sed 's/nan//g' > "$tmp_switch3"

# Combine the stats into a single line per row with commas
paste -d ',' "$tmp_switch0" "$tmp_switch1" "$tmp_switch2" "$tmp_switch3" > "$output_ipc_file"

# Remove temporary files
rm -f "$tmp_switch0" "$tmp_switch1" "$tmp_switch2" "$tmp_switch3"

# Notify the user that the process is complete
echo "Processed IPC stats saved to $output_ipc_file"

code z_IPC.txt

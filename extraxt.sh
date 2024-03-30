#!/bin/bash

# Define the input and output file names
input_file="stats.txt"
output_energy_file="z_energy.txt"
output_ipc_file="z_IPC.txt" # New output file for IPC stats

# Check if the input file exists
if [ ! -f "$input_file" ]; then
    echo "Input file $input_file not found."
    exit 1
fi

# Extract the lines containing energy stats and strip comments
extracted_energy_stats=$(grep -E "board.memory.mem_ctrl[0-9]+.dram.rank[0-9]+.(act|pre|read|write|refresh|actBack|preBack|actPowerDown|prePowerDown|selfRefresh|total)Energy" "$input_file" | sed 's/\s*#.*//' | awk '{print $2}')

# Extract the lines containing IPC stats (new requirement)
extracted_ipc_stats=$(grep -E "board.processor.switch.core.ipc" "$input_file" | awk '{print $2}')

# Counter to keep track of sections
section_counter=0

# Iterate over each line of energy stats
filtered_energy_stats=""
while IFS= read -r line; do
    # Replace "nan" values with a blank line
    if [[ "$line" == "nan" ]]; then
        line=""
    fi
    
    if [[ "$line" == "0" ]]; then
        filtered_energy_stats+="\n"
    else
        filtered_energy_stats+="$line\n"
    fi

    if [[ "$line" =~ ^[0-9.e+-]+$ ]]; then
        ((section_counter++))
        if (( section_counter % 11 == 0 )); then
            filtered_energy_stats+="\n"
        fi
    fi
done <<< "$extracted_energy_stats"

# Remove trailing newlines from energy stats
filtered_energy_stats=$(echo -e "$filtered_energy_stats" | sed -e :a -e '/^\n*$/{$d;N;ba}')

# Save the filtered energy stats to the output file
echo -e "$filtered_energy_stats" > "$output_energy_file"

# Process IPC stats to replace "nan" with a blank line
processed_ipc_stats=""
while IFS= read -r line; do
    if [[ "$line" == "nan" ]]; then
        line=""
    fi

    processed_ipc_stats+="$line\n"
done <<< "$extracted_ipc_stats"

# Save the processed IPC stats to the output file, removing trailing newlines
echo -e "$processed_ipc_stats" | sed -e :a -e '/^\n*$/{$d;N;ba}' > "$output_ipc_file"

# This line is not needed in a bash script
code z_energy.txt
code z_IPC.txt
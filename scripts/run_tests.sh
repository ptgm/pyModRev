#!/bin/bash

# Loop through all subdirectories two levels deep inside 'examples/'
for DIR in examples/*/*; do
    # Check if it is a directory
    if [ -d "$DIR" ]; then
        echo "pyModRev on: $DIR"
        
        # Build arguments for all observation files in the directory
        obs_args=()
        for obs_file in "$DIR"/*.lp; do
            # Check if file exists and is not model.lp
            if [ -f "$obs_file" ] && [ "$(basename "$obs_file")" != "model.lp" ]; then
                filename=$(basename "$obs_file")
                base="${filename%.lp}"
                type="${base%%_*}"
                obs_args+=("$obs_file" "${type}updater")
            fi
        done
        
        if [ ${#obs_args[@]} -gt 0 ]; then
            # Run the commands specified
            python3 main.py -m "$DIR/model.lp" -obs "${obs_args[@]}" -v 0 > tmp
            python3 scripts/compare_outputs.py tmp "$DIR/output.txt"
            
            # Optional: Check if the comparison succeeded based on exit code
            if [ $? -eq 0 ]; then
                echo -e "[\033[32mPASS\033[0m]"
            else
                echo -e "[\033[31mFAIL\033[0m]"
            fi
            echo "----------------------------------------"
        else
            echo "Warning: No observation file (like steadystate.lp) found in $DIR"
        fi
    fi
done

# Clean up the temporary file after all tests finish
rm -f tmp

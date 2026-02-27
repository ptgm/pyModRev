#!/bin/bash

# Loop through all subdirectories two levels deep inside 'examples/'
for DIR in examples/*/*; do
    # Check if it is a directory
    if [ -d "$DIR" ]; then
        echo "pyModRev on: $DIR"
        
        # Find the .lp file that is NOT model.lp to determine the $type
        obs_file=$(ls "$DIR"/*.lp 2>/dev/null | grep -v 'model.lp$' | head -n 1)
        
        if [ -n "$obs_file" ]; then
            # Extract just the filename without the path and without the .lp extension
            filename=$(basename "$obs_file")
            type="${filename%.lp}"
            
            # Run the commands specified
            python3 main.py -m "$DIR/model.lp" -obs "$DIR/$type.lp" "${type}updater" -v 0 > tmp
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

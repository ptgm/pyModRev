
#!/bin/bash

# Loop through all subdirectories two levels deep inside 'examples/'
for DIR in examples/*/*; do
    # Check if it is a directory
    if [ -d "$DIR" ]; then
        echo "ModRev on: $DIR"
        
        # Find the .lp file that is NOT model.lp to determine the $type
        obs_file=$(ls "$DIR"/*.lp 2>/dev/null | grep -v 'model.lp$' | head -n 1)
        
        if [ -n "$obs_file" ]; then
            # Extract just the filename without the path and without the .lp extension
            filename=$(basename "$obs_file")
            # type should be "-ss" if filename=="steadystate" else "-ts"
            type="ss"
            up=""
            if [ "$filename" != "steadystate.lp" ]; then
                type="ts"
                up="-up a"
                if [ "$filename" == "sync.lp" ]; then
                    up="-up s"
                fi
            fi
            
            # Run the commands specified
            ../ModRev/src/modrev -m "$DIR/model.lp" -obs "$obs_file" -ot "${type}" ${up} -v 0 > tmp
            if cmp -s tmp "$DIR/output.txt"; then
                echo -e "[\033[32mPASS\033[0m]"
            else
              python3 scripts/compare_outputs.py tmp "$DIR/output.txt"
              if [ $? -eq 0 ]; then
                  echo -e "[\033[32mPASS\033[0m]"
              else
                  echo -e "[\033[31mFAIL\033[0m]"
              fi
            fi
            echo "----------------------------------------"
        else
            echo "Warning: No observation file (like [updater].lp) found in $DIR"
        fi
    fi
done

# Clean up the temporary file after all tests finish
rm -f tmp

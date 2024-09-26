#!/bin/bash
SLEEP_DURATION=65
MAX_TRIALS=5
trial_count=0

sh run.sh & sleep $SLEEP_DURATION &&
while [ $trial_count -lt $MAX_TRIALS ]; do
    # Replace this with the actual command to check if running tests is possible
    if ! pytest -sv; then
        echo "Waiting for servers to finish setting up to retry running tests..."
    else
        sh clean_up.sh
        break
    fi
    # Increment the trial counter
    trial_count=$((trial_count + 1))
    # Sleep for the specified duration
    sleep $SLEEP_DURATION
done

if [ $trial_count -ge $MAX_TRIALS ]; then
    echo "Error: Timeout after $MAX_TRIALS attempts retrying to run tests."
fi
#!/bin/bash

# Check if VYPYR_DIR is set
if [ -z "$VYPYR_DIR" ]; then
  echo "Error: VYPYR_DIR is not set."
  exit 1
fi

# Navigate to the directory
cd "$VYPYR_DIR/src/scholyr" || { echo "Directory not found: $VYPYR_DIR/src/scholyr"; exit 1; }

# Run the Python script in the background
python -m main &

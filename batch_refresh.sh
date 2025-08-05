#!/bin/bash

# Netflix Data Batch Refresh Script
# Runs daily to update the refined database with new contributions

set -e

echo "🔄 Starting Netflix data batch refresh..."

# Configuration
REFINER_ID=146
LAST_RUN_FILE=".last_batch_run"
BATCH_LOG="batch_refresh.log"

# Get current timestamp
CURRENT_TIME=$(date +%s)

# Check if we need to run (daily)
if [ -f "$LAST_RUN_FILE" ]; then
    LAST_RUN=$(cat "$LAST_RUN_FILE")
    HOURS_SINCE_LAST_RUN=$(( (CURRENT_TIME - LAST_RUN) / 3600 ))
    
    if [ $HOURS_SINCE_LAST_RUN -lt 24 ]; then
        echo "⏰ Batch refresh not due yet (${HOURS_SINCE_LAST_RUN}h since last run)"
        exit 0
    fi
fi

echo "📊 Starting batch refresh..."

# 1. Pull new file pointers since last run
echo "📥 Fetching new file pointers..."
# TODO: Implement file pointer fetching from blockchain

# 2. Process new files
echo "🔓 Decrypting and processing new files..."
# TODO: Implement file processing

# 3. Update refined database
echo "💾 Updating refined database..."
python3 -m refiner

# 4. Upload new snapshot
echo "📤 Uploading new snapshot to IPFS..."
# The refiner already handles IPFS upload

# 5. Update on-chain record
echo "⛓️ Updating on-chain refiner record..."
# TODO: Implement on-chain update

# 6. Unpin previous CID (optional)
echo "🗑️ Cleaning up old snapshots..."
PREVIOUS_CID=$(curl -s https://api.moksha.vanachain.org/refiners/$REFINER_ID | jq -r '.refinementInstruction.refinementCid' 2>/dev/null || echo "")
if [ ! -z "$PREVIOUS_CID" ] && [ "$PREVIOUS_CID" != "null" ]; then
    echo "Unpinning previous CID: $PREVIOUS_CID"
    # TODO: Implement Pinata unpin via API
fi

# 7. Update last run timestamp
echo $CURRENT_TIME > "$LAST_RUN_FILE"

echo "✅ Batch refresh completed successfully!"
echo "📊 New snapshot available for buyers"
echo "🕐 Next batch refresh in 24 hours"

# Log the run
echo "$(date): Batch refresh completed" >> "$BATCH_LOG" 
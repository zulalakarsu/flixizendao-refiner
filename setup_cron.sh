#!/bin/bash

# Setup cron job for Netflix data batch refresh
# This will run the batch refresh daily at 2 AM

echo "🕐 Setting up daily batch refresh cron job..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BATCH_SCRIPT="$SCRIPT_DIR/batch_refresh.sh"

# Create cron job entry (runs daily at 2 AM)
CRON_JOB="0 2 * * * cd $SCRIPT_DIR && $BATCH_SCRIPT >> batch_refresh.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "batch_refresh.sh"; then
    echo "⚠️ Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "batch_refresh.sh" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Cron job set up successfully!"
echo "📅 Batch refresh will run daily at 2:00 AM"
echo "📝 Logs will be saved to: $SCRIPT_DIR/batch_refresh.log"

# Show current cron jobs
echo ""
echo "📋 Current cron jobs:"
crontab -l

echo ""
echo "🔧 To manually run batch refresh:"
echo "   cd $SCRIPT_DIR && ./batch_refresh.sh" 
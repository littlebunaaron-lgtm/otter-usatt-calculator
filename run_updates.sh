#!/bin/bash
# Navigate to the project directory
PROJECT_DIR="/home/aaron/OTTER"
cd "$PROJECT_DIR"

# Activate the virtual environment
source venv/bin/activate

# Run the automator once (modified to not loop)
echo "Starting update at $(date)"
# We will use a modified version of automator.py that runs once or call the specific function
python3 -c "from automator import process_tournaments; process_tournaments()"

# Check if data.js changed and push to GitHub
if [[ -n $(git status --porcelain data.js) ]]; then
    echo "Data changed, pushing to GitHub..."
    git add data.js
    # Optional: also add tournament folders if new ones were created
    git add "202*"
    git commit -m "Automated data update: $(date)"
    git push origin main
else
    echo "No changes in data.js, skipping push."
fi

echo "Update finished at $(date)"

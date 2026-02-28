#!/bin/bash
# ============================================
# Scholar's Terminal - Database Builder
# ============================================

echo ""
echo "============================================"
echo "Scholar's Terminal - Database Builder"
echo "============================================"
echo ""
echo "This will build your knowledge base from"
echo "the sources configured in database_config.yaml"
echo ""
echo "Press Ctrl+C to cancel, or press Enter to continue..."
read

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if config file exists
if [ ! -f "database_config.yaml" ]; then
    echo "Error: database_config.yaml not found"
    echo "Please create the configuration file first"
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import yaml" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip3 install pyyaml chromadb pypdf2 tqdm
    echo ""
fi

# Run the builder
echo "Starting database build..."
echo ""
python3 build_database.py

# Check result
echo ""
echo "============================================"
if [ $? -eq 0 ]; then
    echo "Build complete!"
    echo "Your knowledge base is ready to use."
else
    echo "Build failed! Check database_build.log"
fi
echo "============================================"
echo ""

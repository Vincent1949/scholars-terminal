#!/bin/bash
# AI Knowledge Base System Launcher for Linux/Mac
# This script starts both the document processor and chatbot

echo "============================================================"
echo "AI Knowledge Base System"
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8+ from python.org"
    exit 1
fi

echo "Python found: $(python3 --version)"
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "No virtual environment found"
    echo "Run 'python3 -m venv venv' to create one"
fi

echo ""
echo "Starting Document Processor..."
echo "This will run in the background and monitor your books directory"
echo ""

# Start document processor in background
python3 document_processor.py &
PROCESSOR_PID=$!

# Wait a moment
sleep 2

echo ""
echo "Starting Interactive Chatbot..."
echo ""

# Start chatbot in foreground
python3 unified_knowledge_chatbot_v8_enhanced.py

# When chatbot exits, kill processor
echo ""
echo "Stopping document processor..."
kill $PROCESSOR_PID 2>/dev/null

echo ""
echo "Goodbye!"
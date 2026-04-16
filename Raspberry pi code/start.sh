#!/bin/bash
# Raspberry Pi Car - Startup Script
# This script starts both the web GUI and the controller

echo "======================================"
echo "   Raspberry Pi Car Control System"
echo "======================================"
echo ""

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then 
   echo "⚠️  Warning: Running as root. Consider running as 'pi' user instead."
   echo ""
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if required files exist
echo "🔍 Checking files..."
if [ ! -f "web_gui.py" ]; then
    echo "❌ Error: web_gui.py not found!"
    exit 1
fi

if [ ! -f "picar_controller_integrated.py" ]; then
    echo "❌ Error: picar_controller_integrated.py not found!"
    exit 1
fi

if [ ! -d "templates" ]; then
    echo "❌ Error: templates/ directory not found!"
    exit 1
fi

echo "✅ All required files found"
echo ""

# Check if dependencies are installed
echo "🔍 Checking dependencies..."
python3 -c "import flask, flask_socketio, cv2, serial, pygame" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Some dependencies missing. Installing..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies!"
        echo "Try manually: pip3 install -r requirements.txt"
        exit 1
    fi
fi
echo "✅ Dependencies OK"
echo ""

# Get local IP address
IP_ADDR=$(hostname -I | awk '{print $1}')
echo "📡 Network Information:"
echo "   Local:   http://localhost:5000"
echo "   Network: http://${IP_ADDR}:5000"
echo ""

# Kill any existing instances
echo "🧹 Cleaning up old processes..."
pkill -f web_gui.py 2>/dev/null
pkill -f picar_controller_integrated.py 2>/dev/null
sleep 1

# Create log directory
mkdir -p logs

# Start web GUI in background
echo "🚀 Starting Web GUI Server..."
python3 web_gui.py > logs/web_gui.log 2>&1 &
WEB_PID=$!
echo "   PID: $WEB_PID"

# Wait for web server to start
sleep 3

# Check if web GUI is running
if ! ps -p $WEB_PID > /dev/null; then
    echo "❌ Web GUI failed to start! Check logs/web_gui.log"
    exit 1
fi
echo "✅ Web GUI started successfully"
echo ""

# Start controller
echo "🎮 Starting Car Controller..."
python3 picar_controller_integrated.py > logs/controller.log 2>&1 &
CONTROLLER_PID=$!
echo "   PID: $CONTROLLER_PID"

# Wait for controller to initialize
sleep 2

# Check if controller is running
if ! ps -p $CONTROLLER_PID > /dev/null; then
    echo "❌ Controller failed to start! Check logs/controller.log"
    echo "   Common issues:"
    echo "   - No controller connected"
    echo "   - Arduino not found"
    echo "   - USB permissions"
    kill $WEB_PID 2>/dev/null
    exit 1
fi

echo "✅ Controller started successfully"
echo ""
echo "======================================"
echo "   🎉 SYSTEM READY!"
echo "======================================"
echo ""
echo "📱 Open in browser: http://${IP_ADDR}:5000"
echo ""
echo "🛑 To stop: Press Ctrl+C or run: ./stop.sh"
echo ""
echo "📋 Process IDs:"
echo "   Web GUI:    $WEB_PID"
echo "   Controller: $CONTROLLER_PID"
echo ""
echo "📝 Logs:"
echo "   Web GUI:    logs/web_gui.log"
echo "   Controller: logs/controller.log"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $WEB_PID 2>/dev/null
    kill $CONTROLLER_PID 2>/dev/null
    echo "✅ Stopped all processes"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

# Keep script running and monitor processes
echo "Monitoring processes... (Ctrl+C to stop)"
while true; do
    # Check if web GUI is still running
    if ! ps -p $WEB_PID > /dev/null; then
        echo "❌ Web GUI stopped unexpectedly!"
        kill $CONTROLLER_PID 2>/dev/null
        exit 1
    fi
    
    # Check if controller is still running
    if ! ps -p $CONTROLLER_PID > /dev/null; then
        echo "❌ Controller stopped unexpectedly!"
        kill $WEB_PID 2>/dev/null
        exit 1
    fi
    
    sleep 5
done

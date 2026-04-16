#!/bin/bash
# Raspberry Pi Car - Stop Script
# Cleanly stops both web GUI and controller

echo "🛑 Stopping Raspberry Pi Car Control System..."

# Kill web GUI
WEB_PIDS=$(pgrep -f web_gui.py)
if [ -n "$WEB_PIDS" ]; then
    echo "   Stopping Web GUI (PIDs: $WEB_PIDS)..."
    pkill -f web_gui.py
    echo "   ✅ Web GUI stopped"
else
    echo "   ℹ️  Web GUI not running"
fi

# Kill controller
CONTROLLER_PIDS=$(pgrep -f picar_controller_integrated.py)
if [ -n "$CONTROLLER_PIDS" ]; then
    echo "   Stopping Controller (PIDs: $CONTROLLER_PIDS)..."
    pkill -f picar_controller_integrated.py
    echo "   ✅ Controller stopped"
else
    echo "   ℹ️  Controller not running"
fi

# Also check for original controller script
ORIGINAL_PIDS=$(pgrep -f "python.*\.py" | grep -v $$ | grep -v grep)
if [ -n "$ORIGINAL_PIDS" ]; then
    echo "   Found other Python processes, not stopping them"
fi

echo ""
echo "✅ All Pi Car processes stopped"

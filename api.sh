#!/bin/bash

# MES Data SQL API Management Script - Robust Version

PID_FILE="api.pid"
LOG_FILE="api.log"
API_DIR="api"
PORT=8000

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Find process using the port
find_port_process() {
    lsof -ti:$PORT 2>/dev/null
}

# Check if a process is our API
is_our_api() {
    local pid=$1
    if ps -p "$pid" -o command= 2>/dev/null | grep -q "python main.py"; then
        return 0
    fi
    return 1
}

# Kill any process on our port
kill_port_process() {
    local port_pid=$(find_port_process)
    if [ -n "$port_pid" ]; then
        echo -e "${YELLOW}Found process $port_pid using port $PORT${NC}"
        if is_our_api "$port_pid"; then
            echo -e "${YELLOW}Stopping our API process...${NC}"
            kill "$port_pid" 2>/dev/null
            sleep 2
            # Force kill if still running
            if kill -0 "$port_pid" 2>/dev/null; then
                echo -e "${YELLOW}Force killing process $port_pid${NC}"
                kill -9 "$port_pid" 2>/dev/null
            fi
        else
            echo -e "${RED}Warning: Port $PORT is used by another process (PID: $port_pid)${NC}"
            echo -e "${RED}You may need to stop it manually or use a different port${NC}"
            return 1
        fi
    fi
    return 0
}

start_api() {
    # Check if PID file exists and process is running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}API is already running with PID $PID${NC}"
            return 0
        else
            echo -e "${YELLOW}Removing stale PID file${NC}"
            rm -f "$PID_FILE"
        fi
    fi
    
    # Check if port is in use
    local port_pid=$(find_port_process)
    if [ -n "$port_pid" ]; then
        echo -e "${YELLOW}Port $PORT is already in use by process $port_pid${NC}"
        if is_our_api "$port_pid"; then
            echo -e "${GREEN}API is running but PID file was missing. Recreating...${NC}"
            echo "$port_pid" > "$PID_FILE"
            echo -e "${GREEN}API is available at http://localhost:$PORT${NC}"
            return 0
        else
            echo -e "${RED}Port is used by another process. Cannot start API.${NC}"
            echo -e "${RED}Try: lsof -i :$PORT to see what's using the port${NC}"
            return 1
        fi
    fi
    
    echo -e "${GREEN}Starting MES Data SQL API...${NC}"
    
    # Start the API
    cd "$API_DIR" && nohup python main.py > "../$LOG_FILE" 2>&1 &
    PID=$!
    cd ..
    
    # Save PID immediately
    echo $PID > "$PID_FILE"
    
    # Wait for startup
    echo -e "${BLUE}Waiting for API to start...${NC}"
    for i in {1..10}; do
        sleep 1
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${RED}API process died during startup${NC}"
            echo -e "${RED}Check $LOG_FILE for errors${NC}"
            tail -20 "$LOG_FILE"
            rm -f "$PID_FILE"
            return 1
        fi
        
        # Check if API is responding
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/" 2>/dev/null | grep -q "200"; then
            echo -e "${GREEN}API started successfully with PID $PID${NC}"
            echo -e "${GREEN}API is available at http://localhost:$PORT${NC}"
            echo -e "${GREEN}API docs available at http://localhost:$PORT/docs${NC}"
            return 0
        fi
    done
    
    echo -e "${YELLOW}API process is running but not responding yet${NC}"
    echo -e "${YELLOW}Check $LOG_FILE for details${NC}"
    return 0
}

stop_api() {
    local stopped=false
    
    # Try to stop using PID file first
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping API with PID $PID...${NC}"
            kill "$PID" 2>/dev/null
            
            # Wait for graceful shutdown
            for i in {1..5}; do
                if ! ps -p "$PID" > /dev/null 2>&1; then
                    echo -e "${GREEN}API stopped successfully${NC}"
                    stopped=true
                    break
                fi
                sleep 1
            done
            
            # Force kill if still running
            if ! $stopped && ps -p "$PID" > /dev/null 2>&1; then
                echo -e "${YELLOW}Force killing API...${NC}"
                kill -9 "$PID" 2>/dev/null
                stopped=true
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    # Also check port
    local port_pid=$(find_port_process)
    if [ -n "$port_pid" ]; then
        if is_our_api "$port_pid"; then
            echo -e "${YELLOW}Found API on port $PORT (PID: $port_pid)${NC}"
            kill_port_process
            stopped=true
        fi
    fi
    
    if $stopped; then
        echo -e "${GREEN}API stopped${NC}"
    else
        echo -e "${YELLOW}No API process found${NC}"
    fi
}

check_status() {
    local running=false
    local pid=""
    
    # Check PID file
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
            running=true
            echo -e "${GREEN}API is running with PID $pid (from PID file)${NC}"
        else
            echo -e "${YELLOW}PID file exists but process $pid is not running${NC}"
            rm -f "$PID_FILE"
        fi
    fi
    
    # Check port
    local port_pid=$(find_port_process)
    if [ -n "$port_pid" ]; then
        if is_our_api "$port_pid"; then
            if [ "$port_pid" != "$pid" ]; then
                echo -e "${YELLOW}API is running on port $PORT with PID $port_pid (not in PID file)${NC}"
                # Update PID file
                echo "$port_pid" > "$PID_FILE"
            fi
            running=true
            pid=$port_pid
        else
            echo -e "${YELLOW}Port $PORT is used by another process (PID: $port_pid)${NC}"
        fi
    fi
    
    if $running; then
        # Check if API is responding
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/" 2>/dev/null | grep -q "200"; then
            echo -e "${GREEN}API is responding at http://localhost:$PORT${NC}"
        else
            echo -e "${YELLOW}API process is running but not responding${NC}"
            echo -e "${YELLOW}Check $LOG_FILE for errors${NC}"
        fi
    else
        echo -e "${RED}API is not running${NC}"
    fi
}

force_cleanup() {
    echo -e "${YELLOW}Force cleanup: stopping all API processes and clearing port${NC}"
    
    # Kill by PID file
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ]; then
            kill -9 "$PID" 2>/dev/null
        fi
        rm -f "$PID_FILE"
    fi
    
    # Kill any process on port
    kill_port_process
    
    # Kill any python main.py processes in api directory
    pkill -f "python main.py" 2>/dev/null
    
    echo -e "${GREEN}Cleanup complete${NC}"
}

case "$1" in
    start)
        start_api
        ;;
    stop)
        stop_api
        ;;
    status)
        check_status
        ;;
    restart)
        stop_api
        sleep 1
        start_api
        ;;
    force-cleanup)
        force_cleanup
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|force-cleanup}"
        echo "  start         - Start the MES Data SQL API"
        echo "  stop          - Stop the API"
        echo "  status        - Check if the API is running"
        echo "  restart       - Restart the API"
        echo "  force-cleanup - Force stop all API processes and clear port"
        exit 1
        ;;
esac
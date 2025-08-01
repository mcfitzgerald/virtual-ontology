#!/bin/bash

# MES Data SQL API Management Script

PID_FILE="api.pid"
LOG_FILE="api.log"
API_DIR="api"
PORT=8000

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

start_api() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}API is already running with PID $PID${NC}"
            return
        fi
    fi
    
    echo -e "${GREEN}Starting MES Data SQL API...${NC}"
    cd "$API_DIR" && nohup python main.py > "../$LOG_FILE" 2>&1 &
    PID=$!
    cd ..
    echo $PID > "$PID_FILE"
    
    # Wait a moment for the server to start
    sleep 2
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}API started successfully with PID $PID${NC}"
        echo -e "${GREEN}API is available at http://localhost:$PORT${NC}"
        echo -e "${GREEN}API docs available at http://localhost:$PORT/docs${NC}"
    else
        echo -e "${RED}Failed to start API${NC}"
        rm -f "$PID_FILE"
        exit 1
    fi
}

stop_api() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping API with PID $PID...${NC}"
            kill "$PID"
            rm -f "$PID_FILE"
            echo -e "${GREEN}API stopped successfully${NC}"
        else
            echo -e "${YELLOW}API process not found, cleaning up PID file${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}API is not running (no PID file found)${NC}"
    fi
}

check_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}API is running with PID $PID${NC}"
            
            # Check if the API is responding
            if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/docs" | grep -q "200"; then
                echo -e "${GREEN}API is responding at http://localhost:$PORT${NC}"
            else
                echo -e "${YELLOW}API process is running but not responding on port $PORT${NC}"
            fi
        else
            echo -e "${RED}API is not running (process not found)${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${RED}API is not running (no PID file)${NC}"
    fi
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
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        echo "  start   - Start the MES Data SQL API"
        echo "  stop    - Stop the API"
        echo "  status  - Check if the API is running"
        echo "  restart - Restart the API"
        exit 1
        ;;
esac
#!/bin/bash

# MES Data SQL API Management Script - Robust Version

PID_FILE="api.pid"
LOG_FILE="logs/api.log"
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
    local cmd=$(ps -p "$pid" -o command= 2>/dev/null)
    # Check for both "python main.py" and full Python path with main.py
    if echo "$cmd" | grep -q "main\.py"; then
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
    
    # Start the API and get the PID directly
    cd "$API_DIR"
    python main.py > "../$LOG_FILE" 2>&1 &
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
    local pid_file_valid=false
    
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}                    MES API STATUS REPORT                      ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Check PID file
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1 && is_our_api "$pid"; then
            running=true
            pid_file_valid=true
            echo -e "${GREEN}✓ Process Status${NC}"
            echo -e "  API is running with PID: $pid"
        else
            echo -e "${YELLOW}⚠ PID file exists but process $pid is not running${NC}"
            rm -f "$PID_FILE"
        fi
    fi
    
    # Check port
    local port_pid=$(find_port_process)
    if [ -n "$port_pid" ]; then
        if is_our_api "$port_pid"; then
            running=true
            if [ "$port_pid" != "$pid" ] || [ "$pid_file_valid" = false ]; then
                if [ "$pid_file_valid" = false ]; then
                    echo -e "${GREEN}✓ Process Status${NC}"
                    echo -e "  API is running on port $PORT with PID: $port_pid"
                    echo "$port_pid" > "$PID_FILE"
                fi
            fi
            pid=$port_pid
        else
            echo -e "${YELLOW}⚠ Port $PORT is used by another process (PID: $port_pid)${NC}"
        fi
    elif [ "$pid_file_valid" = false ]; then
        running=false
    fi
    
    if $running; then
        # Check if API is responding
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/" 2>/dev/null | grep -q "200"; then
            echo -e "  Port: $PORT"
            echo -e "  Status: ${GREEN}ONLINE${NC}"
            echo ""
            
            # Get comprehensive database stats
            echo -e "${BLUE}Database Statistics:${NC}"
            local stats=$(curl -s "http://localhost:$PORT/api/database/stats" 2>/dev/null)
            if [ -n "$stats" ]; then
                # Parse and display database info
                local db_size=$(echo "$stats" | jq -r '.file_size_mb' 2>/dev/null)
                local total_tables=$(echo "$stats" | jq -r '.total_tables' 2>/dev/null)
                local total_records=$(echo "$stats" | jq -r '.total_records' 2>/dev/null)
                
                echo -e "  Database Size: ${YELLOW}${db_size} MB${NC}"
                echo -e "  Total Tables: ${YELLOW}${total_tables}${NC}"
                echo -e "  Total Records: ${YELLOW}${total_records}${NC}"
                echo ""
                
                # Show table breakdown
                echo -e "${BLUE}Table Record Counts:${NC}"
                echo "$stats" | jq -r '.tables | to_entries[] | select(.value > 0) | "  \(.key): \(.value)"' 2>/dev/null | while IFS= read -r line; do
                    table_name=$(echo "$line" | cut -d: -f1 | xargs)
                    count=$(echo "$line" | cut -d: -f2 | xargs)
                    
                    # Highlight important tables
                    case "$table_name" in
                        mes_data)
                            echo -e "  ${GREEN}$table_name: $count (main production data)${NC}"
                            ;;
                        twin_runs)
                            echo -e "  ${YELLOW}$table_name: $count (simulation runs)${NC}"
                            ;;
                        simulation_data)
                            echo -e "  ${YELLOW}$table_name: $count (simulation results)${NC}"
                            ;;
                        *)
                            echo -e "  $table_name: $count"
                            ;;
                    esac
                done
                
                # Empty tables summary
                echo ""
                echo -e "${BLUE}Empty Tables:${NC}"
                local empty_tables=$(echo "$stats" | jq -r '.tables | to_entries[] | select(.value == 0) | .key' 2>/dev/null | tr '\n' ', ' | sed 's/,$//')
                if [ -n "$empty_tables" ]; then
                    echo -e "  ${YELLOW}$empty_tables${NC}"
                else
                    echo -e "  ${GREEN}None - all tables have data${NC}"
                fi
            fi
            
            # Get data freshness
            echo ""
            echo -e "${BLUE}Data Freshness (MES Data):${NC}"
            
            # Create temp file for query
            local temp_file=$(mktemp)
            echo '{"sql": "SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest, julianday(MAX(timestamp)) - julianday(MIN(timestamp)) as days_span FROM mes_data"}' > "$temp_file"
            
            local freshness=$(curl -s -X POST "http://localhost:$PORT/query" \
                -H "Content-Type: application/json" \
                -d @"$temp_file" 2>/dev/null)
            
            if [ -n "$freshness" ] && echo "$freshness" | jq -e '.data[0]' > /dev/null 2>&1; then
                local oldest=$(echo "$freshness" | jq -r '.data[0].oldest' 2>/dev/null)
                local newest=$(echo "$freshness" | jq -r '.data[0].newest' 2>/dev/null)
                local days_span=$(echo "$freshness" | jq -r '.data[0].days_span' 2>/dev/null | cut -d. -f1)
                
                echo -e "  Oldest Record: ${YELLOW}$oldest${NC}"
                echo -e "  Newest Record: ${YELLOW}$newest${NC}"
                echo -e "  Data Span: ${YELLOW}$days_span days${NC}"
            fi
            
            # Get twin runs freshness if any exist
            echo '{"sql": "SELECT COUNT(*) as count, MAX(started_at) as latest FROM twin_runs"}' > "$temp_file"
            local twin_freshness=$(curl -s -X POST "http://localhost:$PORT/query" \
                -H "Content-Type: application/json" \
                -d @"$temp_file" 2>/dev/null)
            
            if [ -n "$twin_freshness" ] && echo "$twin_freshness" | jq -e '.data[0].count' > /dev/null 2>&1; then
                local twin_count=$(echo "$twin_freshness" | jq -r '.data[0].count' 2>/dev/null)
                if [ "$twin_count" -gt 0 ]; then
                    echo ""
                    echo -e "${BLUE}Twin Simulation Activity:${NC}"
                    local latest_run=$(echo "$twin_freshness" | jq -r '.data[0].latest' 2>/dev/null)
                    echo -e "  Total Simulation Runs: ${YELLOW}$twin_count${NC}"
                    echo -e "  Latest Run: ${YELLOW}$latest_run${NC}"
                fi
            fi
            
            rm -f "$temp_file"
            
            # API Endpoints
            echo ""
            echo -e "${BLUE}API Endpoints:${NC}"
            echo -e "  Main: ${GREEN}http://localhost:$PORT/${NC}"
            echo -e "  Docs: ${GREEN}http://localhost:$PORT/docs${NC}"
            echo -e "  Query: ${GREEN}http://localhost:$PORT/query${NC}"
            echo -e "  Stats: ${GREEN}http://localhost:$PORT/api/database/stats${NC}"
            
            # Log file status
            echo ""
            echo -e "${BLUE}Log File:${NC}"
            if [ -f "$LOG_FILE" ]; then
                local log_size=$(ls -lh "$LOG_FILE" 2>/dev/null | awk '{print $5}')
                local log_lines=$(wc -l < "$LOG_FILE" 2>/dev/null)
                echo -e "  Path: $LOG_FILE"
                echo -e "  Size: ${YELLOW}$log_size${NC} (${YELLOW}$log_lines lines${NC})"
                
                # Show last few requests
                echo -e "  Recent Requests:"
                tail -5 "$LOG_FILE" | grep "INFO:" | tail -3 | while IFS= read -r line; do
                    echo "    $(echo "$line" | sed 's/INFO:     //')"
                done
            else
                echo -e "  ${YELLOW}Log file not found${NC}"
            fi
            
        else
            echo -e "  Status: ${YELLOW}RUNNING BUT NOT RESPONDING${NC}"
            echo -e "  ${YELLOW}Check $LOG_FILE for errors${NC}"
        fi
    else
        echo -e "${RED}✗ API is not running${NC}"
        echo ""
        echo -e "To start the API, run: ${GREEN}$0 start${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
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

show_help() {
    echo -e "${BLUE}MES Data SQL API Management Script${NC}"
    echo -e "${BLUE}====================================${NC}"
    echo ""
    echo "This script manages the MES Data SQL API server lifecycle. It provides robust"
    echo "process management with automatic port conflict detection, PID tracking, and"
    echo "graceful shutdown capabilities. The API runs on port $PORT by default and serves"
    echo "data through a FastAPI interface. The script ensures only one instance runs at"
    echo "a time, handles stale processes, and provides color-coded status feedback for"
    echo "easy monitoring. It automatically detects and resolves common issues like zombie"
    echo "processes, port conflicts, and stale PID files."
    echo ""
    echo -e "${GREEN}Usage:${NC} $0 {start|stop|status|restart|force-cleanup|help}"
    echo ""
    echo -e "${GREEN}Commands:${NC}"
    echo "  start         - Start the MES Data SQL API server"
    echo "                  Checks for existing processes and port availability"
    echo "  stop          - Gracefully stop the API server"
    echo "                  Attempts clean shutdown before forcing termination"
    echo "  status        - Comprehensive API and database status report"
    echo "                  Shows process, database stats, table counts, data freshness"
    echo "  restart       - Stop and restart the API server"
    echo "                  Ensures clean restart with brief pause"
    echo "  force-cleanup - Force stop all API processes and clear port"
    echo "                  Use when normal stop fails or system is in bad state"
    echo "  help          - Display this help message"
    echo ""
    echo -e "${GREEN}Files:${NC}"
    echo "  PID File: $PID_FILE (tracks running process ID)"
    echo "  Log File: $LOG_FILE (captures API output and errors)"
    echo "  API Dir:  $API_DIR (location of main.py)"
    echo ""
    echo -e "${GREEN}Access Points:${NC}"
    echo "  API Endpoint: http://localhost:$PORT/"
    echo "  API Docs:     http://localhost:$PORT/docs"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  $0 start      # Start the API server"
    echo "  $0 status     # Check if server is running"
    echo "  $0 restart    # Restart the server"
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
    help)
        show_help
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|force-cleanup|help}"
        echo "  start         - Start the MES Data SQL API"
        echo "  stop          - Stop the API"
        echo "  status        - Comprehensive API and database status report"
        echo "  restart       - Restart the API"
        echo "  force-cleanup - Force stop all API processes and clear port"
        echo "  help          - Display detailed help and documentation"
        exit 1
        ;;
esac
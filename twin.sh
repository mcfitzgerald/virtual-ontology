#!/bin/bash

# Virtual Twin Database Management Script
# Complete replacement for api.sh with enhanced functionality

PID_FILE="twin.pid"
LOG_FILE="logs/twin_api.log"
PORT=8000

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure logs directory exists
mkdir -p logs
mkdir -p backups
mkdir -p data

# Find process using the port
find_port_process() {
    lsof -ti:$PORT 2>/dev/null
}

# Check if our API is running
is_our_api() {
    local pid=$1
    local cmd=$(ps -p "$pid" -o command= 2>/dev/null)
    if echo "$cmd" | grep -q "database\.main\|database\.app"; then
        return 0
    fi
    return 1
}

# Kill process on port
kill_port_process() {
    local port_pid=$(find_port_process)
    if [ -n "$port_pid" ]; then
        echo -e "${YELLOW}Found process $port_pid using port $PORT${NC}"
        if is_our_api "$port_pid"; then
            echo -e "${YELLOW}Stopping Twin API process...${NC}"
            kill "$port_pid" 2>/dev/null
            sleep 2
            if kill -0 "$port_pid" 2>/dev/null; then
                kill -9 "$port_pid" 2>/dev/null
            fi
        else
            echo -e "${RED}Port $PORT is used by another process${NC}"
            return 1
        fi
    fi
    return 0
}

# Start the API
start_api() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}Twin API is already running with PID $PID${NC}"
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    local port_pid=$(find_port_process)
    if [ -n "$port_pid" ]; then
        echo -e "${YELLOW}Port $PORT is already in use by process $port_pid${NC}"
        if is_our_api "$port_pid"; then
            echo "$port_pid" > "$PID_FILE"
            echo -e "${GREEN}Twin API is running${NC}"
            return 0
        else
            echo -e "${RED}Cannot start: Port is used by another process${NC}"
            return 1
        fi
    fi
    
    echo -e "${GREEN}Starting Virtual Twin Database API...${NC}"
    
    # Start the API
    python -m database.main > "$LOG_FILE" 2>&1 &
    PID=$!
    
    echo $PID > "$PID_FILE"
    
    # Wait for startup
    echo -e "${BLUE}Waiting for API to start...${NC}"
    for i in {1..10}; do
        sleep 1
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${RED}API process died during startup${NC}"
            tail -20 "$LOG_FILE"
            rm -f "$PID_FILE"
            return 1
        fi
        
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/health" 2>/dev/null | grep -q "200"; then
            echo -e "${GREEN}✓ Twin API started successfully with PID $PID${NC}"
            echo -e "${GREEN}✓ API available at http://localhost:$PORT${NC}"
            echo -e "${GREEN}✓ Documentation at http://localhost:$PORT/docs${NC}"
            return 0
        fi
    done
    
    echo -e "${YELLOW}API process is running but not responding yet${NC}"
    return 0
}

# Stop the API
stop_api() {
    local stopped=false
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping Twin API with PID $PID...${NC}"
            kill "$PID" 2>/dev/null
            
            for i in {1..5}; do
                if ! ps -p "$PID" > /dev/null 2>&1; then
                    echo -e "${GREEN}✓ Twin API stopped${NC}"
                    stopped=true
                    break
                fi
                sleep 1
            done
            
            if ! $stopped && ps -p "$PID" > /dev/null 2>&1; then
                kill -9 "$PID" 2>/dev/null
                stopped=true
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    local port_pid=$(find_port_process)
    if [ -n "$port_pid" ]; then
        if is_our_api "$port_pid"; then
            kill_port_process
            stopped=true
        fi
    fi
    
    if $stopped; then
        echo -e "${GREEN}✓ Twin API stopped${NC}"
    else
        echo -e "${YELLOW}No Twin API process found${NC}"
    fi
}

# Check status
check_status() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}             VIRTUAL TWIN DATABASE API STATUS                  ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    local running=false
    local pid=""
    
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1 && is_our_api "$pid"; then
            running=true
        fi
    fi
    
    local port_pid=$(find_port_process)
    if [ -n "$port_pid" ] && is_our_api "$port_pid"; then
        running=true
        pid=$port_pid
    fi
    
    if $running; then
        echo -e "${GREEN}✓ API Status: RUNNING${NC}"
        echo -e "  PID: $pid"
        echo -e "  Port: $PORT"
        
        # Check if API is responding
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/health" 2>/dev/null | grep -q "200"; then
            echo -e "  Health: ${GREEN}HEALTHY${NC}"
            
            # Get database stats
            echo ""
            echo -e "${BLUE}Database Statistics:${NC}"
            local stats=$(curl -s "http://localhost:$PORT/database/stats" 2>/dev/null)
            if [ -n "$stats" ]; then
                local file_size=$(echo "$stats" | jq -r '.file_size_mb' 2>/dev/null)
                local total_tables=$(echo "$stats" | jq -r '.total_tables' 2>/dev/null)
                local total_records=$(echo "$stats" | jq -r '.total_records' 2>/dev/null)
                local ontology_version=$(echo "$stats" | jq -r '.ontology_version' 2>/dev/null)
                
                echo -e "  Database Size: ${YELLOW}${file_size} MB${NC}"
                echo -e "  Ontology Version: ${YELLOW}${ontology_version}${NC}"
                echo -e "  Total Tables: ${YELLOW}${total_tables}${NC}"
                echo -e "  Total Records: ${YELLOW}${total_records}${NC}"
            fi
        else
            echo -e "  Health: ${YELLOW}NOT RESPONDING${NC}"
        fi
        
        echo ""
        echo -e "${BLUE}API Endpoints:${NC}"
        echo -e "  Main: ${GREEN}http://localhost:$PORT/${NC}"
        echo -e "  Docs: ${GREEN}http://localhost:$PORT/docs${NC}"
        echo -e "  Query: ${GREEN}http://localhost:$PORT/query${NC}"
        echo -e "  Simulations: ${GREEN}http://localhost:$PORT/simulations${NC}"
        echo -e "  Experiments: ${GREEN}http://localhost:$PORT/experiments${NC}"
        
    else
        echo -e "${RED}✗ API Status: NOT RUNNING${NC}"
        echo ""
        echo -e "To start the API, run: ${GREEN}$0 start${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

# Initialize database
init_database() {
    echo -e "${GREEN}Initializing database...${NC}"
    python -m database.cli init
    python -m database.cli sync-manifests
    echo -e "${GREEN}✓ Database initialized${NC}"
}

# Run simulation
run_simulation() {
    local days=${1:-1}
    local type=${2:-experiment}
    echo -e "${GREEN}Running $type simulation for $days days...${NC}"
    python -m database.cli run-simulation --days $days --type $type
}

# Import historical data
import_data() {
    local csv_file=${1:-"archive/misc/data/mes_data_with_kpis.csv"}
    if [ -f "$csv_file" ]; then
        echo -e "${GREEN}Importing historical data from $csv_file...${NC}"
        python -m database.cli import-historical "$csv_file"
    else
        echo -e "${RED}File not found: $csv_file${NC}"
        return 1
    fi
}

# Backup database
backup_database() {
    echo -e "${GREEN}Creating database backup...${NC}"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="backups/twin_db_backup_${timestamp}.db"
    
    if [ -f "data/twin_database.db" ]; then
        cp "data/twin_database.db" "$backup_file"
        echo -e "${GREEN}✓ Backup created: $backup_file${NC}"
    else
        echo -e "${RED}Database file not found${NC}"
        return 1
    fi
}

# Show help
show_help() {
    echo -e "${BLUE}Virtual Twin Database Management Script${NC}"
    echo -e "${BLUE}=======================================${NC}"
    echo ""
    echo -e "${GREEN}Usage:${NC} $0 <command> [options]"
    echo ""
    echo -e "${GREEN}Service Commands:${NC}"
    echo "  start           - Start the Twin API server"
    echo "  stop            - Stop the API server"
    echo "  restart         - Restart the API server"
    echo "  status          - Show API and database status"
    echo ""
    echo -e "${GREEN}Database Commands:${NC}"
    echo "  init            - Initialize database and sync manifests"
    echo "  import [file]   - Import historical MES data from CSV"
    echo "  backup          - Create database backup"
    echo "  sync            - Sync configurations from manifests"
    echo ""
    echo -e "${GREEN}Simulation Commands:${NC}"
    echo "  simulate [days] [type] - Run simulation (default: 1 day, experiment)"
    echo "  experiment      - Run an experiment"
    echo "  discover        - Discover patterns from experiments"
    echo ""
    echo -e "${GREEN}Utility Commands:${NC}"
    echo "  logs            - Show recent API logs"
    echo "  clean           - Clean simulation data"
    echo "  help            - Show this help message"
    echo ""
    echo -e "${GREEN}Examples:${NC}"
    echo "  $0 start                    # Start the API"
    echo "  $0 simulate 7 baseline      # Run 7-day baseline simulation"
    echo "  $0 import data.csv          # Import CSV data"
    echo "  $0 status                   # Check system status"
}

# Main command handler
case "$1" in
    start)
        start_api
        ;;
    stop)
        stop_api
        ;;
    restart)
        stop_api
        sleep 1
        start_api
        ;;
    status)
        check_status
        ;;
    init)
        init_database
        ;;
    import)
        import_data "$2"
        ;;
    backup)
        backup_database
        ;;
    sync)
        python -m database.cli sync-manifests
        ;;
    simulate)
        run_simulation "$2" "$3"
        ;;
    experiment)
        python -m database.cli run-experiment
        ;;
    discover)
        python -m database.cli discover-patterns
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -50 "$LOG_FILE"
        else
            echo "No log file found"
        fi
        ;;
    clean)
        echo "Cleaning simulation data..."
        python -m database.cli status
        ;;
    help)
        show_help
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|init|import|backup|sync|simulate|experiment|discover|logs|clean|help}"
        echo "Run '$0 help' for detailed information"
        exit 1
        ;;
esac
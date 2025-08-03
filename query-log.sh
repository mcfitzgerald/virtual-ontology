#!/bin/bash

# SQL API Query Logger with Smart Truncation
# Logs all queries and responses, truncates large responses for display
#
# IMPORTANT: JSON Escaping Issue
# Due to shell argument parsing, inline JSON with -d flag often fails.
# Use file reference instead: -d @/path/to/file.json
# See --help for examples and workarounds

# Configuration
API_BASE_URL="http://localhost:8000"
LOG_FILE="query_logs.json"
MAX_DISPLAY_SIZE=5000  # Characters to display before truncation
TRUNCATE_PREVIEW=1000  # Characters to show in truncated preview

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Generate unique ID
generate_id() {
    echo "$(date +%Y%m%d_%H%M%S)_$(openssl rand -hex 2)"
}

# Check if jq is installed
check_jq() {
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}Error: jq is required but not installed${NC}"
        echo "Install with: brew install jq"
        exit 1
    fi
}

# Initialize log file if it doesn't exist or is invalid
init_log_file() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "[]" > "$LOG_FILE"
        echo -e "${GREEN}Created new log file: $LOG_FILE${NC}" >&2
    else
        # Validate existing file is valid JSON array
        if ! jq -e 'type == "array"' "$LOG_FILE" >/dev/null 2>&1; then
            echo -e "${YELLOW}Warning: Invalid log file detected, backing up and creating new${NC}" >&2
            mv "$LOG_FILE" "${LOG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
            echo "[]" > "$LOG_FILE"
        fi
    fi
}

# Show a specific log entry
show_log_entry() {
    local log_id="$1"
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${RED}No log file found${NC}"
        exit 1
    fi
    
    jq -r ".[] | select(.id == \"$log_id\")" "$LOG_FILE"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Log entry with ID $log_id not found${NC}"
        exit 1
    fi
}

# Execute query and log
execute_query() {
    local method="$1"
    local endpoint="$2"
    shift 2
    
    # Check for --intent parameter
    local intent=""
    local new_args=()
    local skip_next=false
    local next_is_intent=false
    
    for arg in "$@"; do
        if [ "$next_is_intent" = true ]; then
            intent="$arg"
            # Validate intent length (140 chars max)
            if [ ${#intent} -gt 140 ]; then
                echo -e "${YELLOW}Warning: Intent truncated to 140 characters${NC}"
                intent="${intent:0:140}"
            fi
            next_is_intent=false
            continue
        fi
        
        if [ "$arg" = "--intent" ]; then
            next_is_intent=true
            continue
        fi
        
        new_args+=("$arg")
    done
    
    local curl_args="${new_args[@]}"
    
    # Generate unique ID and timestamp
    local query_id=$(generate_id)
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Build full URL
    local full_url="${API_BASE_URL}${endpoint}"
    
    # Execute curl and capture response, status code, and headers
    local temp_response=$(mktemp)
    local temp_headers=$(mktemp)
    
    echo -e "${BLUE}Executing query (ID: $query_id)...${NC}"
    
    # Execute curl with all arguments
    # KNOWN ISSUE: $curl_args without quotes causes JSON to be mangled
    # This is intentionally left as-is for backward compatibility
    # Workaround: Use file reference with -d @filename.json
    local http_code=$(curl -s -w "%{http_code}" -o "$temp_response" -D "$temp_headers" \
        -X "$method" "$full_url" \
        -H "Content-Type: application/json" \
        $curl_args)
    
    # Read response
    local response=$(cat "$temp_response")
    local response_size=${#response}
    
    # Extract request body from curl args if present
    local request_body=""
    for arg in $curl_args; do
        if [[ "$arg" == -d* ]]; then
            request_body="${arg#-d}"
        elif [[ "$last_arg" == "-d" ]] || [[ "$last_arg" == "--data" ]]; then
            request_body="$arg"
        fi
        last_arg="$arg"
    done
    
    # Determine if response should be truncated for display
    local truncated=false
    local display_response="$response"
    
    if [ $response_size -gt $MAX_DISPLAY_SIZE ]; then
        truncated=true
        # Get first part of response for preview
        display_response=$(echo "$response" | head -c $TRUNCATE_PREVIEW)
        
        # Try to parse as JSON for better summary
        if echo "$response" | jq -e . >/dev/null 2>&1; then
            local row_count=$(echo "$response" | jq 'if type == "array" then length else 1 end' 2>/dev/null)
            display_response="${display_response}...\n\n[JSON Response Truncated]"
            if [ -n "$row_count" ]; then
                display_response="${display_response}\nTotal items: $row_count"
            fi
        else
            display_response="${display_response}...\n\n[Response Truncated]"
        fi
    fi
    
    # Create log entry
    local log_entry=$(jq -n \
        --arg id "$query_id" \
        --arg ts "$timestamp" \
        --arg method "$method" \
        --arg endpoint "$endpoint" \
        --arg intent "$intent" \
        --arg req_body "$request_body" \
        --arg resp "$response" \
        --arg resp_size "$response_size" \
        --arg truncated "$truncated" \
        --arg status "$http_code" \
        '{
            id: $id,
            timestamp: $ts,
            method: $method,
            endpoint: $endpoint,
            intent: (if $intent != "" then $intent else null end),
            request_body: $req_body,
            response: $resp,
            response_size: ($resp_size | tonumber),
            truncated: ($truncated == "true"),
            status_code: ($status | tonumber)
        }')
    
    # Append to log file with error handling
    local temp_log=$(mktemp)
    if jq ". += [$log_entry]" "$LOG_FILE" > "$temp_log" 2>/dev/null; then
        # Verify the result is valid JSON
        if jq -e '.' "$temp_log" >/dev/null 2>&1; then
            mv "$temp_log" "$LOG_FILE"
        else
            echo -e "${RED}Error: Failed to create valid log entry${NC}" >&2
            echo -e "${YELLOW}Query executed but not logged${NC}" >&2
            rm -f "$temp_log"
        fi
    else
        echo -e "${RED}Error: Failed to append to log file${NC}" >&2
        echo -e "${YELLOW}Attempting to recreate log file...${NC}" >&2
        echo "[$log_entry]" > "$LOG_FILE"
        rm -f "$temp_log"
    fi
    
    # Display response
    echo -e "${GREEN}Query ID: $query_id${NC}"
    echo -e "${GREEN}Status: $http_code${NC}"
    echo -e "${GREEN}Response Size: $response_size bytes${NC}"
    echo ""
    
    if [ "$truncated" = true ]; then
        echo -e "${YELLOW}⚠️  Response truncated ($(($response_size / 1024)) KB). Full data saved to $LOG_FILE${NC}"
        echo -e "${YELLOW}To view full response: $0 --show-log $query_id${NC}"
        echo -e "${YELLOW}For large dataset analysis, use Python to load from $LOG_FILE${NC}"
        echo ""
        echo "--- Truncated Preview ---"
    fi
    
    echo "$display_response"
    
    # Cleanup
    rm -f "$temp_response" "$temp_headers"
}

# Main script logic
main() {
    # Check dependencies
    check_jq
    init_log_file
    
    # Parse arguments
    if [ "$1" == "--show-log" ]; then
        if [ -z "$2" ]; then
            echo -e "${RED}Usage: $0 --show-log <log_id>${NC}"
            exit 1
        fi
        show_log_entry "$2"
        exit 0
    fi
    
    if [ "$1" == "--help" ] || [ -z "$1" ]; then
        echo "SQL API Query Logger"
        echo ""
        echo "Usage:"
        echo "  $0 <METHOD> <ENDPOINT> [--intent \"description\"] [curl options]"
        echo "  $0 --show-log <log_id>"
        echo "  $0 --example-json"
        echo "  $0 --test"
        echo "  $0 --verify-log"
        echo "  $0 --repair-log"
        echo ""
        echo "Examples:"
        echo "  $0 GET /tables"
        echo "  $0 POST /query --intent \"Find bottlenecks\" -d @query.json"
        echo "  $0 --show-log 20250802_143022_a7b3"
        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT: JSON Escaping Issue${NC}"
        echo "Inline JSON often fails due to shell escaping. Use file reference instead:"
        echo ""
        echo -e "${RED}FAILS:${NC}"
        echo "  $0 POST /query -d '{\"sql\": \"SELECT * FROM mes_data\"}'"
        echo ""
        echo -e "${GREEN}WORKS:${NC}"
        echo "  echo '{\"sql\": \"SELECT * FROM mes_data\"}' > /tmp/query.json"
        echo "  $0 POST /query -d @/tmp/query.json"
        echo ""
        echo "SQLite-Specific Notes:"
        echo "  - Use double quotes for strings in SQL: WHERE status = \"Running\""
        echo "  - Date functions: strftime('%H', timestamp), DATE(timestamp)"
        echo "  - No STDDEV function available"
        echo "  - No CTEs (WITH clauses) allowed by API"
        echo ""
        echo "Configuration:"
        echo "  API URL: $API_BASE_URL"
        echo "  Log file: $LOG_FILE"
        echo "  Max display size: $MAX_DISPLAY_SIZE bytes"
        echo ""
        echo "Troubleshooting:"
        echo "  422 error: JSON formatting issue - use file reference"
        echo "  400 error: SQL syntax error or unsupported function"
        echo "  Empty results: Check date ranges (data is from June 2025)"
        exit 0
    fi
    
    if [ "$1" == "--example-json" ]; then
        echo "Example query.json file:"
        echo ""
        echo '{'
        echo '  "sql": "SELECT line_id, AVG(oee_score) as avg_oee FROM mes_data WHERE machine_status = \"Running\" GROUP BY line_id ORDER BY avg_oee DESC"'
        echo '}'
        echo ""
        echo "Save this to a file and use: $0 POST /query -d @query.json"
        exit 0
    fi
    
    if [ "$1" == "--verify-log" ]; then
        echo -e "${BLUE}Verifying log file integrity...${NC}"
        if [ ! -f "$LOG_FILE" ]; then
            echo -e "${RED}✗ Log file not found: $LOG_FILE${NC}"
            echo "Run any query to create it, or use --repair-log"
            exit 1
        fi
        
        if jq -e 'type == "array"' "$LOG_FILE" >/dev/null 2>&1; then
            local count=$(jq 'length' "$LOG_FILE")
            echo -e "${GREEN}✓ Log file is valid JSON array${NC}"
            echo -e "${GREEN}  Contains $count entries${NC}"
            
            # Check if we can read the entries
            if jq -e '.[0] | has("id", "timestamp", "method")' "$LOG_FILE" >/dev/null 2>&1; then
                echo -e "${GREEN}✓ Log entries have correct structure${NC}"
            elif [ "$count" -eq 0 ]; then
                echo -e "${YELLOW}  Log is empty but valid${NC}"
            else
                echo -e "${YELLOW}⚠ Log entries may have incorrect structure${NC}"
            fi
        else
            echo -e "${RED}✗ Log file is not a valid JSON array${NC}"
            echo "Use --repair-log to fix it"
            exit 1
        fi
        exit 0
    fi
    
    if [ "$1" == "--repair-log" ]; then
        echo -e "${BLUE}Attempting to repair log file...${NC}"
        if [ ! -f "$LOG_FILE" ]; then
            echo "[]" > "$LOG_FILE"
            echo -e "${GREEN}✓ Created new empty log file${NC}"
        else
            # Try to parse and fix
            if jq -e '.' "$LOG_FILE" >/dev/null 2>&1; then
                # It's valid JSON, check if it's an array
                if jq -e 'type == "array"' "$LOG_FILE" >/dev/null 2>&1; then
                    echo -e "${GREEN}✓ Log file is already valid${NC}"
                else
                    # Valid JSON but not an array, wrap it
                    echo -e "${YELLOW}Converting to array format...${NC}"
                    local backup="${LOG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
                    mv "$LOG_FILE" "$backup"
                    echo "[$(cat "$backup")]" | jq '.' > "$LOG_FILE"
                    echo -e "${GREEN}✓ Converted to array format (backup: $backup)${NC}"
                fi
            else
                # Not valid JSON at all
                echo -e "${YELLOW}File is corrupted, creating backup and new file...${NC}"
                mv "$LOG_FILE" "${LOG_FILE}.corrupted.$(date +%Y%m%d_%H%M%S)"
                echo "[]" > "$LOG_FILE"
                echo -e "${GREEN}✓ Created new empty log file${NC}"
            fi
        fi
        exit 0
    fi
    
    if [ "$1" == "--test" ]; then
        echo -e "${BLUE}Testing API connectivity...${NC}"
        response=$(curl -s -w "\n%{http_code}" "$API_BASE_URL")
        http_code=$(echo "$response" | tail -n 1)
        body=$(echo "$response" | sed '$d')
        
        if [ "$http_code" == "200" ]; then
            echo -e "${GREEN}✓ API is responding at $API_BASE_URL${NC}"
            echo "Response: $body"
        else
            echo -e "${RED}✗ API not responding (HTTP $http_code)${NC}"
            echo "Check if API is running: ./api.sh status"
        fi
        exit 0
    fi
    
    # Execute query
    execute_query "$@"
}

# Run main function
main "$@"
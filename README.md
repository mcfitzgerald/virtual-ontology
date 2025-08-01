# MES Data SQL API

A simple FastAPI application that exposes Manufacturing Execution System (MES) data from a CSV file through a SQL-based REST API.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
cd api
python main.py
```

**Note:** The `main.py` file is located in the `api/` directory, so you must navigate there first.

The API will be available at `http://localhost:8000`

## Quick Start Script

A convenience script `api.sh` is provided to easily start, check, and stop the API:

```bash
# Start the API
./api.sh start

# Check if API is running
./api.sh status

# Stop the API
./api.sh stop
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Main Endpoints

- `GET /data` - Get all MES data with pagination and filters
- `GET /data/{id}` - Get a single record by ID
- `GET /data/by-order/{order_id}` - Get data by production order
- `GET /data/by-line/{line_id}` - Get data by production line
- `GET /data/by-equipment/{equipment_id}` - Get data by equipment
- `GET /kpis/summary` - Get aggregated KPI summary
- `GET /kpis/by-equipment` - Get KPIs grouped by equipment
- `GET /kpis/by-product` - Get KPIs grouped by product

## Example Usage

```bash
# Get paginated data
curl http://localhost:8000/data?page=1&page_size=10

# Get KPI summary
curl http://localhost:8000/kpis/summary

# Filter by line
curl http://localhost:8000/data?line_id=1
```
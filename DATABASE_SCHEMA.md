# MES Database Schema

## Table: mes_data

| Column | Type | Nullable | Indexed | Description |
|--------|------|----------|---------|-------------|
| **id** | INTEGER | NO | Primary Key | Auto-incrementing unique identifier |
| timestamp | DATETIME | NO | YES | Timestamp of the data point |
| production_order_id | VARCHAR | YES | YES | Production order ID (NULL during changeovers) |
| line_id | VARCHAR | NO | YES | Production line identifier |
| equipment_id | VARCHAR | NO | YES | Equipment identifier |
| equipment_type | VARCHAR | NO | NO | Type of equipment (Filler, Packer, Palletizer) |
| product_id | VARCHAR | YES | YES | Product SKU (NULL during changeovers) |
| product_name | VARCHAR | YES | NO | Product name (NULL during changeovers) |
| machine_status | VARCHAR | NO | NO | Machine status (Running, Stopped) |
| downtime_reason | VARCHAR | YES | NO | Reason for downtime (NULL when running) |
| good_units_produced | INTEGER | NO | NO | Number of good units produced |
| scrap_units_produced | INTEGER | NO | NO | Number of scrap units produced |
| target_rate_units_per_5min | INTEGER | NO | NO | Target production rate per 5 minutes |
| standard_cost_per_unit | FLOAT | NO | NO | Standard cost per unit |
| sale_price_per_unit | FLOAT | NO | NO | Sale price per unit |
| availability_score | FLOAT | NO | NO | Availability KPI score (0-100) |
| performance_score | FLOAT | NO | NO | Performance KPI score (0-100) |
| quality_score | FLOAT | NO | NO | Quality KPI score (0-100) |
| oee_score | FLOAT | NO | YES | Overall Equipment Effectiveness score (0-100) |

## Indexes

- **Primary Key**: id
- **ix_mes_data_timestamp**: On timestamp column
- **ix_mes_data_production_order_id**: On production_order_id column
- **ix_mes_data_line_id**: On line_id column
- **ix_mes_data_equipment_id**: On equipment_id column
- **ix_mes_data_product_id**: On product_id column
- **ix_mes_data_oee_score**: On oee_score column

## Downtime Reason Codes

### Planned Downtime (PLN-*)
- **PLN-CO**: Planned Changeover
- **PLN-CLN**: Planned Cleaning
- **PLN-PM**: Planned Preventive Maintenance

### Unplanned Downtime (UNP-*)
- **UNP-JAM**: Unplanned Jam
- **UNP-ELEC**: Unplanned Electrical Issue
- **UNP-MAT**: Unplanned Material Issue
- **UNP-SENS**: Unplanned Sensor Issue
- **UNP-QC**: Unplanned Quality Control
- **UNP-OPR**: Unplanned Operator Issue
- **UNP-MECH**: Unplanned Mechanical Issue

## Data Characteristics

- **Total Records**: 36,288
- **Production Records**: 33,288 (with product/order data)
- **Changeover Records**: 3,000 (NULL product/order data)
- **Date Range**: June 1-14, 2025
- **Equipment Types**: 3 (Filler, Packer, Palletizer)
- **Production Lines**: 3 (Line 1, 2, 3)
- **Products**: 2 (12oz Soda, 16oz Energy Drink)
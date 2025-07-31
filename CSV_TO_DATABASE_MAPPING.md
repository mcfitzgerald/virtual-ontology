# CSV to Database Schema Mapping

## Column Mapping

| CSV Column Name | Database Column Name | Data Type | Transformation | Notes |
|-----------------|---------------------|-----------|----------------|--------|
| Timestamp | timestamp | DATETIME | `datetime.strptime(value, '%Y-%m-%d %H:%M:%S')` | Converted from string to datetime |
| ProductionOrderID | production_order_id | VARCHAR | Direct mapping, NULL handling | Can be NULL during changeovers |
| LineID | line_id | VARCHAR | `str(value)` | Converted to string |
| EquipmentID | equipment_id | VARCHAR | Direct mapping | |
| EquipmentType | equipment_type | VARCHAR | Direct mapping | |
| ProductID | product_id | VARCHAR | Direct mapping, NULL handling | Can be NULL during changeovers |
| ProductName | product_name | VARCHAR | Direct mapping, NULL handling | Can be NULL during changeovers |
| MachineStatus | machine_status | VARCHAR | Direct mapping | |
| DowntimeReason | downtime_reason | VARCHAR | Direct mapping, NULL handling | Can be NULL when machine is running |
| GoodUnitsProduced | good_units_produced | INTEGER | `int(value)` | |
| ScrapUnitsProduced | scrap_units_produced | INTEGER | `int(value)` | |
| TargetRate_units_per_5min | target_rate_units_per_5min | INTEGER | `int(value)` | |
| StandardCost_per_unit | standard_cost_per_unit | FLOAT | `float(value)` | |
| SalePrice_per_unit | sale_price_per_unit | FLOAT | `float(value)` | |
| Availability_Score | availability_score | FLOAT | `float(value)` | |
| Performance_Score | performance_score | FLOAT | `float(value)` | |
| Quality_Score | quality_score | FLOAT | `float(value)` | |
| OEE_Score | oee_score | FLOAT | `float(value)` | |
| (none) | id | INTEGER | Auto-generated | Primary key added by database |

## Naming Convention Changes

The transformation from CSV to database follows these patterns:

1. **CamelCase to snake_case**: 
   - `ProductionOrderID` → `production_order_id`
   - `EquipmentType` → `equipment_type`

2. **Abbreviation expansion**:
   - `TargetRate_units_per_5min` → `target_rate_units_per_5min` (kept as-is)
   - `StandardCost_per_unit` → `standard_cost_per_unit` (kept as-is)

3. **Score suffix standardization**:
   - `Availability_Score` → `availability_score`
   - `OEE_Score` → `oee_score`

## Data Type Conversions

### String to Datetime
```python
# CSV: "2025-06-01 00:00:00" (string)
# Database: datetime object
timestamp = datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S')
```

### Numeric Type Casting
```python
# Integers
good_units_produced = int(row['GoodUnitsProduced'])

# Floats
oee_score = float(row['OEE_Score'])
```

### NULL/NaN Handling
```python
# CSV: NaN (pandas) or empty string
# Database: NULL

# Example for ProductionOrderID
production_order_id = row['ProductionOrderID'] if pd.notna(row['ProductionOrderID']) else None
```

## Import Code Reference

The actual transformation happens in `database.py`:

```python
mes_data = MESData(
    timestamp=datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S'),
    production_order_id=row['ProductionOrderID'] if pd.notna(row['ProductionOrderID']) else None,
    line_id=str(row['LineID']),
    equipment_id=row['EquipmentID'],
    equipment_type=row['EquipmentType'],
    product_id=row['ProductID'] if pd.notna(row['ProductID']) else None,
    product_name=row['ProductName'] if pd.notna(row['ProductName']) else None,
    machine_status=row['MachineStatus'],
    downtime_reason=row['DowntimeReason'] if pd.notna(row['DowntimeReason']) else None,
    good_units_produced=int(row['GoodUnitsProduced']),
    scrap_units_produced=int(row['ScrapUnitsProduced']),
    target_rate_units_per_5min=int(row['TargetRate_units_per_5min']),
    standard_cost_per_unit=float(row['StandardCost_per_unit']),
    sale_price_per_unit=float(row['SalePrice_per_unit']),
    availability_score=float(row['Availability_Score']),
    performance_score=float(row['Performance_Score']),
    quality_score=float(row['Quality_Score']),
    oee_score=float(row['OEE_Score'])
)
```

## Special Cases

1. **Added Fields**: The database adds an `id` field as an auto-incrementing primary key that doesn't exist in the CSV.

2. **NULL Values**: Three fields can be NULL in the database:
   - `production_order_id`: NULL during changeovers (PLN-CO)
   - `product_id`: NULL during changeovers
   - `product_name`: NULL during changeovers
   - `downtime_reason`: NULL when machine is running

3. **Indexed Fields**: The database adds indexes on frequently queried fields for performance:
   - timestamp, production_order_id, line_id, equipment_id, product_id, oee_score
# MES Data Analysis - Missing Product/Order Information

## Summary
The CSV file contains **36,288 total rows**, of which **3,000 rows (8.3%)** have missing ProductionOrderID, ProductID, and ProductName.

## Root Cause: Planned Changeovers (PLN-CO)
All 3,000 rows with missing product/order data represent **planned changeover** periods where:
- **DowntimeReason** = "PLN-CO" (Planned Changeover)
- **MachineStatus** = "Stopped"
- **TargetRate_units_per_5min** = 0
- **GoodUnitsProduced** = 0
- **ScrapUnitsProduced** = 0
- All KPI scores = 0

This is **completely normal and expected** in manufacturing operations. During changeovers:
- Equipment is stopped to switch from one product to another
- No production order is active
- No product is being manufactured
- All production metrics are zero

## Downtime Reason Categories
The data uses a consistent coding system for downtime:
- **PLN-*** = Planned downtime (5,220 occurrences)
  - PLN-CO: Planned Changeover (3,000)
  - PLN-CLN: Planned Cleaning (2,136)
  - PLN-PM: Planned Preventive Maintenance (84)
- **UNP-*** = Unplanned downtime (6,745 occurrences)
  - UNP-JAM: Unplanned Jam (2,706)
  - UNP-ELEC: Unplanned Electrical Issue (1,170)
  - UNP-MAT: Unplanned Material Issue (1,106)
  - UNP-SENS: Unplanned Sensor Issue (855)
  - UNP-QC: Unplanned Quality Control (555)
  - UNP-OPR: Unplanned Operator Issue (296)
  - UNP-MECH: Unplanned Mechanical Issue (57)

## Data Integrity
The missing data is **intentional and meaningful**, not a data quality issue. The API correctly:
- Skips these 3,000 changeover records during import
- Imports the remaining 33,288 production records
- Maintains data integrity by not forcing fake product IDs on non-production periods

## Recommendation
No action needed. The data structure accurately reflects real manufacturing operations where equipment has both production periods (with products) and non-production periods (changeovers, cleaning, maintenance).
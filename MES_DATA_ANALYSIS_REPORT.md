# MES Data Analysis Report

## Dataset Overview
- **Size**: 7,776 records (3 days of data, 5-minute intervals)
- **Structure**: 19 columns, one row per equipment per timestamp
- **Date Range**: 2025-06-01 00:00:00 to 2025-06-03 23:55:00

## Key Findings

### 1. Production Lines & Equipment
- **3 Production Lines**: LINE1, LINE2, LINE3 (equally represented)
- **9 Equipment Total**: 3 equipment per line
  - Filler (FIL)
  - Packer (PCK)
  - Palletizer (PAL)
- **Equipment IDs**: Format is "LINE{X}-{TYPE}" (e.g., LINE1-FIL)

### 2. Products
**6 Unique Products**:
| Product ID | Product Name | Target Rate | Cost | Price | % of Production |
|------------|-------------|-------------|------|-------|-----------------|
| SKU-1001 | 12oz Sparkling Water | 500 | $0.20 | $0.65 | 23.5% |
| SKU-1002 | 32oz Premium Juice | 350 | $0.55 | $1.75 | 33.9% |
| SKU-2001 | 12oz Soda | 475 | $0.20 | $0.65 | 10.3% |
| SKU-2002 | 16oz Energy Drink | 450 | $0.55 | $1.75 | 12.9% |
| SKU-3001 | 8oz Kids Drink | 550 | $0.15 | $0.45 | 10.6% |
| (null) | (changeovers) | 0 | $0.00 | $0.00 | 8.7% |

### 3. Machine States
- **Running**: 69.4% of records
- **Stopped**: 30.6% of records
- No "Idle" state observed in this dataset

### 4. Downtime Reasons
**8 Unique Downtime Codes**:

**Planned Downtime (PLN-)**:
- PLN-CO: Changeover (8.7% of all records, always with null ProductionOrderID)
- PLN-CLN: Cleaning (5.3%)

**Unplanned Downtime (UNP-)**:
- UNP-JAM: Material Jam (7.2%)
- UNP-ELEC: Electrical issue (2.5%, only on Palletizers)
- UNP-SENS: Sensor issue (2.2%, only on Fillers)
- UNP-QC: Quality Control (1.9%, only on Packers)
- UNP-MAT: Material Starvation (1.9%)
- UNP-OPR: Operator issue (0.8%, only on Fillers)

### 5. Equipment-Specific Patterns

| Equipment Type | Uptime % | Avg Good Units | Avg Scrap | Avg OEE |
|---------------|----------|---------------|-----------|---------|
| Filler | 72.0% | 302.4 | 29.0 | 49.1% |
| Packer | 62.4% | 280.9 | 28.0 | 40.2% |
| Palletizer | 73.8% | 312.8 | 30.4 | 52.2% |

**Equipment-Specific Downtime**:
- **Fillers**: Experience sensor issues (UNP-SENS) and operator issues (UNP-OPR)
- **Packers**: Experience quality control stops (UNP-QC)
- **Palletizers**: Experience electrical issues (UNP-ELEC)

### 6. Production Orders
- **28 unique orders** (ORD-1001 to ORD-1027)
- Orders are null during changeovers (PLN-CO)
- Order distribution varies from 0.04% to 5.4% of records

### 7. KPI Ranges
- **Availability Score**: 0-100% (binary: 100% when running, 0% when stopped)
- **Performance Score**: 0-100% (actual vs target rate)
- **Quality Score**: 0-98.9% (good units / total units)
- **OEE Score**: 0-94.2% (product of all three)
- **Energy Consumption**: 0.083-1.706 kWh per 5-minute interval

### 8. Special Patterns
- **Changeovers**: Always have null ProductionOrderID, ProductID, and ProductName
- **Zero Production**: All stopped records have 0 good and scrap units
- **Product-Line Assignment**: Products can run on multiple lines (not line-specific)

## What Our Simulation Must Capture

### Required Features
1. ✅ **Equipment States**: Running, Stopped (we have these)
2. ⚠️ **Missing**: "Idle" state (not in data but might be needed)
3. ✅ **Downtime Reasons**: 8 specific codes with equipment-specific patterns
4. ⚠️ **Changeover Logic**: Need to null out order/product during PLN-CO
5. ⚠️ **Multiple Products**: Need product scheduling/assignment logic
6. ⚠️ **Equipment-Specific Failures**: Different equipment types have unique failure modes
7. ⚠️ **Energy Consumption**: Variable based on state and production

### Current Gaps in Our Simulation
1. **Product Variety**: Currently only simulating one product
2. **Changeover Handling**: Not nulling order/product fields
3. **Equipment-Specific Failures**: All equipment use same failure patterns
4. **Energy Consumption**: Not tracked
5. **Product Scheduling**: No logic for which product runs when
6. **Line-Product Flexibility**: Products can run on any line

### Recommendations
1. Add product scheduling logic to simulation
2. Implement equipment-specific failure patterns
3. Add changeover events with proper null handling
4. Include energy consumption calculation
5. Consider adding "Idle" state for completeness
6. Implement product-line assignment logic
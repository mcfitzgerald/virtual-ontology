# Next Steps: Fix Order Cycling Logic

## Issue 6: Order Cycling Interleaves Products Incorrectly

### Problem Description

The current order cycling logic generates cycles one order at a time, causing products to interleave incorrectly:

**Current behavior:**
```
LINE1 queue: ORD-LINE1-001, ORD-LINE1-002, ORD-LINE1-001-C1, ORD-LINE1-002-C1, ...
                ↑ SKU-1001      ↑ SKU-1002      ↑ SKU-1001      ↑ SKU-1002
```

**Problem:** When ORD-LINE1-001 completes (~48 min), the source moves to ORD-LINE1-002 (SKU-1002). But in long simulations, the queue length causes ORD-LINE1-001-C1 to start before ORD-LINE1-002 finishes, forcing a premature product changeover.

**Evidence:**
- 24-hour simulation shows LINE1 only produced SKU-1001 (864 records, 0 SKU-1002)
- 24-hour simulation shows LINE2 only produced SKU-2001 (864 records, 0 SKU-3001)
- LINE3 correctly produced both SKU-2001 (387 records) and SKU-3001 (477 records)

### Root Cause

**File:** `run_twin_simulation.py:142-156`

The cycling loop iterates through `original_orders` and immediately appends cycled versions:

```python
while last_due_time < simulation_duration:
    for original_order in original_orders:  # ← Cycles ONE order at a time
        new_order = ProductionOrder(
            order_id=f"{original_order.order_id}-C{cycle}",
            product_id=original_order.product_id,
            target_volume=original_order.target_volume,
            due_time=original_order.due_time + (cycle * max(o.due_time for o in original_orders)),
            priority=original_order.priority
        )
        orders.append(new_order)  # ← Appends to existing list immediately
        last_due_time = new_order.due_time

        if last_due_time >= simulation_duration:
            break

    cycle += 1
```

This creates: [001, 002, 001-C1, 002-C1, 001-C2, ...]

### Expected Behavior

Orders should cycle in complete sets, maintaining the original sequence:

```
LINE1 queue:
  Cycle 0: ORD-LINE1-001, ORD-LINE1-002
  Cycle 1: ORD-LINE1-001-C1, ORD-LINE1-002-C1
  Cycle 2: ORD-LINE1-001-C2, ORD-LINE1-002-C2
  ...
```

Each cycle should complete ALL products before moving to the next cycle.

## Implementation Plan

### Step 1: Fix Cycling Algorithm

**Location:** `run_twin_simulation.py:138-163`

Replace the current cycling logic with:

```python
if last_due_time < simulation_duration:
    original_orders = orders.copy()
    cycle = 1

    # Calculate the cycle duration (time for all orders in one cycle)
    cycle_duration = max(o.due_time for o in original_orders)

    while last_due_time < simulation_duration:
        # Add ALL orders for this cycle before moving to next cycle
        cycle_orders = []
        for original_order in original_orders:
            new_order = ProductionOrder(
                order_id=f"{original_order.order_id}-C{cycle}",
                product_id=original_order.product_id,
                target_volume=original_order.target_volume,
                due_time=original_order.due_time + (cycle * cycle_duration),
                priority=original_order.priority
            )
            cycle_orders.append(new_order)
            last_due_time = new_order.due_time

        # Append entire cycle at once
        orders.extend(cycle_orders)

        cycle += 1

        if cycle > 100:
            logger.warning(f"Order cycling limit reached for {line_id}")
            break

    logger.info(f"{line_id}: Cycled to {len(orders)} orders (from {len(original_orders)} original)")
```

### Step 2: Test Short Simulation

Run a 2.5 hour (150 minute) simulation to verify order sequencing:

```bash
poetry run python run_twin_simulation.py --duration 150 --mes-output test_cycling_fix.csv
```

**Verify:**
1. Check order sequence in logs:
   ```bash
   grep "Added order.*LINE1" <output> | head -10
   ```
   Should show: 001, 002, 001-C1, 002-C1, 001-C2 (not 001, 002, 001-C1)

2. Check products produced on LINE1:
   ```bash
   grep "LINE1" test_cycling_fix.csv | cut -d, -f6 | sort | uniq -c
   ```
   Should show both SKU-1001 AND SKU-1002

### Step 3: Test Long Simulation

Run full 24-hour simulation:

```bash
poetry run python run_twin_simulation.py --days 1 --mes-output test_full_day.csv
```

**Verify:**
1. All three lines produce both products:
   ```bash
   for line in LINE1 LINE2 LINE3; do
     echo "=== $line ==="
     grep "$line" test_full_day.csv | cut -d, -f6 | sort | uniq -c
   done
   ```

2. Order IDs follow expected pattern:
   ```bash
   cut -d, -f2 test_full_day.csv | sort | uniq | grep "LINE1"
   ```
   Should show: ORD-LINE1-001, ORD-LINE1-002, ORD-LINE1-001-C1, ORD-LINE1-002-C1, ...

3. Continuous production (no extended idle periods):
   ```bash
   grep "Total Production" <output> | tail -1
   ```
   Should show ~45,000+ units

### Step 4: Edge Case Testing

Test with `--no-cycle-orders` flag:

```bash
poetry run python run_twin_simulation.py --duration 150 --no-cycle-orders --mes-output test_no_cycle.csv
```

**Verify:**
- Only 6 original orders are queued
- Lines go IDLE after ~120 minutes
- Both products still appear on each line

## Success Criteria

- ✅ LINE1 produces both SKU-1001 and SKU-1002 in 24-hour simulation
- ✅ LINE2 produces both SKU-2001 and SKU-3001 in 24-hour simulation
- ✅ LINE3 continues producing both SKU-2001 and SKU-3001
- ✅ Order IDs in MES data follow pattern: original orders, then C1 cycle, then C2 cycle, etc.
- ✅ Cycling can be disabled with `--no-cycle-orders` flag
- ✅ Short simulations (< 2 hours) work correctly

## Notes

- The current due_time calculation `original_order.due_time + (cycle * max(...))` is correct
- The issue is purely about WHEN orders are appended to the queue
- LINE3 works correctly in current implementation by coincidence (timing causes both orders to complete before cycles interfere)
- This fix maintains backward compatibility - no changes to function signatures or manifest format

## Related Files

- `run_twin_simulation.py:61-165` - Order loading and cycling logic
- `twin_model/primitives/source_flow.py` - Source order processing
- `manifests/production_orders_manifest.yaml` - Order definitions
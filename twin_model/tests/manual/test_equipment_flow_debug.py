"""Debug equipment flow processing."""

import simpy
from twin_model.primitives import (
    SourceFlow, EquipmentFlow, SinkFlow,
    FlowCapacity, ProcessingParameters, FailureParameters
)

class DebugEquipmentFlow(EquipmentFlow):
    """Equipment flow with debug logging."""
    
    def process_flow(self):
        """Process material in continuous batches with debug logging."""
        iteration = 0
        while True:
            iteration += 1
            print(f"\n[{self.env.now:.2f}] Equipment iteration {iteration}:")
            
            try:
                # Check if equipment is failed
                if self.is_failed:
                    print(f"  Equipment is failed, waiting...")
                    self.change_state(FlowState.FAILED)
                    yield self.env.timeout(self.processing.processing_interval)
                    continue

                # Calculate batch volume based on rate and interval
                target_volume = (
                    self.processing.nominal_rate *
                    self.processing.processing_interval *
                    self.processing.performance_factor
                )
                print(f"  Target volume: {target_volume:.2f}")

                # Check material availability
                print(f"  Input buffer exists: {self.input_buffer is not None}")
                if self.input_buffer:
                    print(f"  Input buffer level: {self.input_buffer.level:.2f}")
                    print(f"  Batch size: {self.processing.batch_size:.2f}")
                    print(f"  Level >= batch_size: {self.input_buffer.level >= self.processing.batch_size}")
                
                if self.input_buffer and self.input_buffer.level >= self.processing.batch_size:
                    print(f"  ✅ Material available, processing...")
                    
                    # Calculate actual volume to process
                    actual_volume = min(
                        target_volume,
                        self.input_buffer.level,
                        self.internal_buffer.capacity - self.internal_buffer.level
                    )
                    print(f"  Actual volume to process: {actual_volume:.2f}")

                    if actual_volume >= self.processing.batch_size:
                        print(f"  Processing batch...")
                        # Pull from input
                        yield self.input_buffer.get(actual_volume)

                        # Add to internal buffer
                        yield self.internal_buffer.put(actual_volume)

                        # Process (with time delay)
                        self.change_state(FlowState.FLOWING)
                        self.is_processing = True
                        yield self.env.timeout(self.processing.processing_interval)

                        # Get from internal buffer
                        processed = min(actual_volume, self.internal_buffer.level)
                        yield self.internal_buffer.get(processed)

                        # Apply quality split
                        good_output = processed * self.processing.quality_rate
                        scrap = processed * (1 - self.processing.quality_rate)

                        # Push to output
                        if self.output_buffer:
                            available_space = self.output_buffer.capacity - self.output_buffer.level
                            if available_space >= good_output:
                                yield self.output_buffer.put(good_output)

                                # Track metrics
                                self.flow_metrics.total_input += actual_volume
                                self.flow_metrics.total_output += good_output
                                self.flow_metrics.total_scrap += scrap
                                
                                print(f"  ✅ Processed {actual_volume:.2f} -> {good_output:.2f} (scrap: {scrap:.2f})")
                            else:
                                # Blocked downstream
                                print(f"  ❌ Blocked downstream")
                                self.change_state(FlowState.BLOCKED_DOWNSTREAM)
                                # Return material to internal buffer
                                yield self.internal_buffer.put(processed)
                                yield self.env.timeout(self.processing.processing_interval)
                        else:
                            # No output buffer configured
                            self.flow_metrics.total_input += actual_volume
                            self.flow_metrics.total_output += good_output
                            self.flow_metrics.total_scrap += scrap
                    else:
                        # Not enough material for minimum batch
                        print(f"  ❌ Not enough for minimum batch")
                        self.change_state(FlowState.STARVED_UPSTREAM)
                        yield self.env.timeout(self.processing.processing_interval)
                else:
                    # Starved - no material to process
                    print(f"  ❌ Starved - no material")
                    self.change_state(FlowState.STARVED_UPSTREAM)
                    yield self.env.timeout(self.processing.processing_interval)

                self.is_processing = False

            except simpy.Interrupt:
                # Handle interruptions (failures, maintenance, etc.)
                print(f"  Interrupted")
                self.is_processing = False


def test_debug_flow():
    """Test with debug equipment."""
    env = simpy.Environment()
    
    # Import FlowState here to avoid circular import
    from twin_model.primitives.base_flow import FlowState
    
    # Make FlowState available to DebugEquipmentFlow
    globals()['FlowState'] = FlowState
    
    # Create source
    source_capacity = FlowCapacity(100, 60, 1000, 0)
    source_config = {'name': 'SOURCE', 'continuous_mode': True, 'default_product': 'TEST'}
    source = SourceFlow(env, source_config, source_capacity, 60.0, 0.1)
    source.output_buffer = simpy.Container(env, 1000, init=0)
    
    # Create equipment with debug version
    eq_capacity = FlowCapacity(60, 50, 500, 0)
    eq_config = {'name': 'EQUIPMENT'}
    processing = ProcessingParameters(50.0, 0.95, 1.0, 10.0, 0.1)
    failures = FailureParameters(1000.0, 10.0, 0, 0)  # No failures for test
    equipment = DebugEquipmentFlow(env, eq_config, eq_capacity, processing, failures)
    
    # Wire: share buffer between source and equipment
    equipment.input_buffer = source.output_buffer  # Share the buffer!
    equipment.output_buffer = simpy.Container(env, 500, init=0)
    
    # Start processes
    source.start()
    equipment.start()
    
    print("Starting simulation...")
    print(f"Initial source output buffer: {source.output_buffer.level:.1f}")
    print(f"Initial equipment input buffer: {equipment.input_buffer.level:.1f}")
    
    # Run for a short time
    env.run(until=0.5)
    
    print(f"\n=== Final State at t={env.now:.2f} ===")
    print(f"Source output buffer: {source.output_buffer.level:.1f}")
    print(f"Equipment total processed: {equipment.flow_metrics.total_output:.1f}")

if __name__ == "__main__":
    test_debug_flow()
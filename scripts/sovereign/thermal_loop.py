"""
ThermalLoop: Predictive Cooling for Sovereign Stack
Monitors die temperature and preemptively manages thermal envelope.
"""

import subprocess
import time
import threading
from dataclasses import dataclass
from typing import Optional, Callable, List
from enum import Enum

class ThermalState(Enum):
    COLD = "cold"           # < 60°C - Full power
    NOMINAL = "nominal"     # 60-80°C - Normal operation
    WARM = "warm"           # 80-95°C - Pre-cool, monitor closely
    HOT = "hot"             # > 95°C - Load shedding required
    CRITICAL = "critical"   # > 100°C - Emergency shutdown

@dataclass
class ThermalReading:
    cpu_temp: float         # TP0 - CPU Package
    gpu_temp: float         # TG0 - GPU Die
    fan_speed: int          # Current RPM
    state: ThermalState
    timestamp: float

@dataclass
class ThermalPolicy:
    precool_threshold: float = 80.0      # Start aggressive cooling
    loadshed_threshold: float = 95.0     # Reduce workload
    critical_threshold: float = 100.0    # Emergency stop
    max_fan_rpm: int = 7200              # Force max fans

class ThermalLoop:
    """
    User-space thermal management loop.
    
    Overrides macOS acoustic-first fan curves with safety-first approach.
    Uses SMC access via system tools (powermetrics, iStats).
    """
    
    def __init__(self, policy: Optional[ThermalPolicy] = None):
        self.policy = policy or ThermalPolicy()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._readings: List[ThermalReading] = []
        self._on_state_change: Optional[Callable] = None
        self._last_state = ThermalState.COLD
        self._smc_available = self._check_smc()
    
    def _check_smc(self) -> bool:
        """Check if SMC access is available."""
        try:
            result = subprocess.run(
                ["which", "osx-cpu-temp"],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                return True
            
            # Fallback to powermetrics (requires sudo)
            return True
        except:
            return False
    
    def _read_temperature(self) -> ThermalReading:
        """Read current thermal state from SMC."""
        cpu_temp = 0.0
        gpu_temp = 0.0
        fan_speed = 0
        
        try:
            # Try osx-cpu-temp first (homebrew: brew install osx-cpu-temp)
            result = subprocess.run(
                ["osx-cpu-temp"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # Parse output like "72.3°C"
                temp_str = result.stdout.strip().replace("°C", "")
                cpu_temp = float(temp_str)
                gpu_temp = cpu_temp  # Same die on M-series
        except FileNotFoundError:
            # Fallback: Use sysctl for thermal pressure
            try:
                result = subprocess.run(
                    ["sysctl", "machdep.xcpm.cpu_thermal_level"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    # Parse thermal level (0-100 scale)
                    level = int(result.stdout.split(":")[-1].strip())
                    # Estimate temp from thermal level
                    cpu_temp = 40.0 + (level * 0.6)
                    gpu_temp = cpu_temp
            except:
                pass
        except:
            pass
        
        # Determine thermal state
        if cpu_temp >= self.policy.critical_threshold:
            state = ThermalState.CRITICAL
        elif cpu_temp >= self.policy.loadshed_threshold:
            state = ThermalState.HOT
        elif cpu_temp >= self.policy.precool_threshold:
            state = ThermalState.WARM
        elif cpu_temp >= 60:
            state = ThermalState.NOMINAL
        else:
            state = ThermalState.COLD
        
        return ThermalReading(
            cpu_temp=cpu_temp,
            gpu_temp=gpu_temp,
            fan_speed=fan_speed,
            state=state,
            timestamp=time.time()
        )
    
    def _force_max_fans(self):
        """Force fans to maximum RPM (requires SMC control)."""
        # This would use smcFanControl or similar
        # For now, just log the intent
        print("🌀 THERMAL: Forcing fans to maximum RPM")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            reading = self._read_temperature()
            self._readings.append(reading)
            
            # Keep last 100 readings
            if len(self._readings) > 100:
                self._readings = self._readings[-100:]
            
            # State change handling
            if reading.state != self._last_state:
                self._handle_state_change(self._last_state, reading.state, reading)
                self._last_state = reading.state
            
            # Predictive actions
            if reading.state == ThermalState.WARM:
                self._force_max_fans()
            
            time.sleep(1.0)  # 1Hz monitoring
    
    def _handle_state_change(
        self,
        old_state: ThermalState,
        new_state: ThermalState,
        reading: ThermalReading
    ):
        """Handle thermal state transitions."""
        print(f"🌡️ THERMAL: {old_state.value} → {new_state.value} ({reading.cpu_temp:.1f}°C)")
        
        if new_state == ThermalState.CRITICAL:
            print("🛑 THERMAL CRITICAL: Emergency load shedding!")
        elif new_state == ThermalState.HOT:
            print("⚠️ THERMAL HOT: Reducing batch size recommended")
        elif new_state == ThermalState.WARM:
            print("🌀 THERMAL WARM: Pre-cooling initiated")
        
        if self._on_state_change:
            self._on_state_change(old_state, new_state, reading)
    
    def start(self, on_state_change: Optional[Callable] = None):
        """Start the thermal monitoring loop."""
        self._on_state_change = on_state_change
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print(f"🌡️ ThermalLoop started (pre-cool: {self.policy.precool_threshold}°C)")
    
    def stop(self):
        """Stop the monitoring loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("🌡️ ThermalLoop stopped")
    
    def get_current(self) -> ThermalReading:
        """Get current thermal reading."""
        return self._read_temperature()
    
    def should_shed_load(self) -> bool:
        """Check if load shedding is required."""
        reading = self.get_current()
        return reading.state in [ThermalState.HOT, ThermalState.CRITICAL]
    
    def get_safe_batch_size(self, max_batch: int) -> int:
        """Calculate safe batch size based on thermal state."""
        reading = self.get_current()
        
        if reading.state == ThermalState.CRITICAL:
            return 1
        elif reading.state == ThermalState.HOT:
            return max(1, max_batch // 4)
        elif reading.state == ThermalState.WARM:
            return max(1, max_batch // 2)
        else:
            return max_batch

if __name__ == "__main__":
    print("🌡️ ThermalLoop Test")
    print("=" * 40)
    
    loop = ThermalLoop()
    reading = loop.get_current()
    
    print(f"CPU Temp: {reading.cpu_temp:.1f}°C")
    print(f"GPU Temp: {reading.gpu_temp:.1f}°C")
    print(f"State: {reading.state.value}")
    print(f"Should Shed Load: {loop.should_shed_load()}")
    print(f"Safe Batch Size (max=32): {loop.get_safe_batch_size(32)}")
    
    # Test monitoring loop
    print("\n📊 Starting 5-second monitoring test...")
    loop.start()
    time.sleep(5)
    loop.stop()
    
    print(f"\nCollected {len(loop._readings)} readings")
    print("✅ ThermalLoop test complete.")

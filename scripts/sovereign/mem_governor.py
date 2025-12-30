"""
MemGovernor: Wired Memory Tracking for Sovereign Stack
Prevents UMA exhaustion and kernel panics on Apple Silicon.
"""

import ctypes
import ctypes.util
from dataclasses import dataclass
from typing import Optional
import subprocess

# Load libc for mach calls
libc = ctypes.CDLL(ctypes.util.find_library('c'))

# Mach host statistics structures
HOST_VM_INFO64 = 4
HOST_VM_INFO64_COUNT = 38

class VMStatistics64(ctypes.Structure):
    """vm_statistics64 structure from mach/vm_statistics.h"""
    _fields_ = [
        ("free_count", ctypes.c_uint64),
        ("active_count", ctypes.c_uint64),
        ("inactive_count", ctypes.c_uint64),
        ("wire_count", ctypes.c_uint64),
        ("zero_fill_count", ctypes.c_uint64),
        ("reactivations", ctypes.c_uint64),
        ("pageins", ctypes.c_uint64),
        ("pageouts", ctypes.c_uint64),
        ("faults", ctypes.c_uint64),
        ("cow_faults", ctypes.c_uint64),
        ("lookups", ctypes.c_uint64),
        ("hits", ctypes.c_uint64),
        ("purges", ctypes.c_uint64),
        ("purgeable_count", ctypes.c_uint64),
        ("speculative_count", ctypes.c_uint64),
        ("decompressions", ctypes.c_uint64),
        ("compressions", ctypes.c_uint64),
        ("swapins", ctypes.c_uint64),
        ("swapouts", ctypes.c_uint64),
        ("compressor_page_count", ctypes.c_uint64),
        ("throttled_count", ctypes.c_uint64),
        ("external_page_count", ctypes.c_uint64),
        ("internal_page_count", ctypes.c_uint64),
        ("total_uncompressed_pages_in_compressor", ctypes.c_uint64),
    ]

@dataclass
class MemoryStatus:
    """Current memory status."""
    physical_gb: float
    wired_gb: float
    active_gb: float
    inactive_gb: float
    free_gb: float
    compressed_gb: float
    safe_headroom_gb: float
    can_allocate_gb: float
    warning: Optional[str]

class MemGovernor:
    """
    Wired Memory Governor for Apple Silicon.
    
    Key insight from blueprint:
    - macOS caps wired memory at ~70-75% of physical RAM
    - Exceeding this causes kernel panic, not graceful OOM
    - GPU allocations (MTLStorageModeShared) often become wired
    
    Formula: M_safe = M_physical - M_wired - M_reserve (4GB)
    """
    
    # Critical reserve that macOS needs (empirically determined)
    CRITICAL_RESERVE_GB = 4.0
    
    # Safe wired memory ceiling (75% of physical)
    WIRED_CEILING_RATIO = 0.75
    
    def __init__(self):
        self.page_size = self._get_page_size()
        self.physical_memory = self._get_physical_memory()
    
    def _get_page_size(self) -> int:
        """Get system page size."""
        try:
            result = subprocess.run(
                ["pagesize"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return int(result.stdout.strip())
        except:
            return 16384  # Default for Apple Silicon
    
    def _get_physical_memory(self) -> int:
        """Get total physical memory in bytes."""
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return int(result.stdout.strip())
        except:
            return 0
    
    def _get_vm_stats(self) -> Optional[VMStatistics64]:
        """Get VM statistics via mach_host_statistics64."""
        try:
            # Use vm_stat command as fallback (easier than raw mach calls)
            result = subprocess.run(
                ["vm_stat"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode != 0:
                return None
            
            # Parse vm_stat output
            stats = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':')
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip().rstrip('.').replace(',', '')
                    try:
                        stats[key] = int(value)
                    except:
                        pass
            
            # Create pseudo VMStatistics64
            vm = VMStatistics64()
            vm.free_count = stats.get('pages_free', 0)
            vm.active_count = stats.get('pages_active', 0)
            vm.inactive_count = stats.get('pages_inactive', 0)
            vm.wire_count = stats.get('pages_wired_down', 0)
            vm.compressor_page_count = stats.get('pages_stored_in_compressor', 0)
            vm.speculative_count = stats.get('pages_speculative', 0)
            
            return vm
        except Exception as e:
            print(f"⚠️ MemGovernor: Failed to get VM stats: {e}")
            return None
    
    def get_status(self) -> MemoryStatus:
        """Get current memory status."""
        vm = self._get_vm_stats()
        
        physical_gb = self.physical_memory / (1024**3)
        
        if vm is None:
            return MemoryStatus(
                physical_gb=physical_gb,
                wired_gb=0,
                active_gb=0,
                inactive_gb=0,
                free_gb=0,
                compressed_gb=0,
                safe_headroom_gb=0,
                can_allocate_gb=0,
                warning="Unable to read VM statistics"
            )
        
        # Convert pages to GB
        page_to_gb = self.page_size / (1024**3)
        
        wired_gb = vm.wire_count * page_to_gb
        active_gb = vm.active_count * page_to_gb
        inactive_gb = vm.inactive_count * page_to_gb
        free_gb = vm.free_count * page_to_gb
        compressed_gb = vm.compressor_page_count * page_to_gb
        
        # Calculate safe headroom
        # M_safe = M_physical - M_wired - M_reserve
        safe_headroom_gb = physical_gb - wired_gb - self.CRITICAL_RESERVE_GB
        
        # What can we safely allocate for GPU/wired use?
        max_wired = physical_gb * self.WIRED_CEILING_RATIO
        can_allocate_gb = max(0, max_wired - wired_gb)
        
        # Generate warning if needed
        warning = None
        wired_ratio = wired_gb / physical_gb
        
        if wired_ratio > 0.70:
            warning = f"CRITICAL: Wired memory at {wired_ratio:.0%} - risk of kernel panic!"
        elif wired_ratio > 0.60:
            warning = f"WARNING: Wired memory at {wired_ratio:.0%} - approaching danger zone"
        elif wired_ratio > 0.50:
            warning = f"CAUTION: Wired memory at {wired_ratio:.0%}"
        
        return MemoryStatus(
            physical_gb=physical_gb,
            wired_gb=wired_gb,
            active_gb=active_gb,
            inactive_gb=inactive_gb,
            free_gb=free_gb,
            compressed_gb=compressed_gb,
            safe_headroom_gb=safe_headroom_gb,
            can_allocate_gb=can_allocate_gb,
            warning=warning
        )
    
    def can_load_model(self, model_size_gb: float) -> tuple[bool, str]:
        """
        Check if a model of given size can be safely loaded.
        
        Returns (can_load, reason)
        """
        status = self.get_status()
        
        if model_size_gb > status.can_allocate_gb:
            return False, (
                f"Model ({model_size_gb:.1f}GB) exceeds safe allocation limit "
                f"({status.can_allocate_gb:.1f}GB available)"
            )
        
        if model_size_gb > status.safe_headroom_gb:
            return False, (
                f"Model ({model_size_gb:.1f}GB) would breach safe headroom "
                f"({status.safe_headroom_gb:.1f}GB remaining)"
            )
        
        return True, f"Safe to load: {status.can_allocate_gb:.1f}GB available"
    
    def recommend_model_size(self) -> float:
        """Recommend maximum safe model size in GB."""
        status = self.get_status()
        # Use 80% of available space as recommendation
        return status.can_allocate_gb * 0.8

if __name__ == "__main__":
    print("💾 MemGovernor Test")
    print("=" * 40)
    
    gov = MemGovernor()
    status = gov.get_status()
    
    print(f"Physical RAM: {status.physical_gb:.1f} GB")
    print(f"Wired Memory: {status.wired_gb:.1f} GB ({status.wired_gb/status.physical_gb:.0%})")
    print(f"Active Memory: {status.active_gb:.1f} GB")
    print(f"Free Memory: {status.free_gb:.1f} GB")
    print(f"Compressed: {status.compressed_gb:.1f} GB")
    print(f"\n📊 Safety Analysis:")
    print(f"  Safe Headroom: {status.safe_headroom_gb:.1f} GB")
    print(f"  Can Allocate: {status.can_allocate_gb:.1f} GB")
    print(f"  Recommended Model Size: {gov.recommend_model_size():.1f} GB")
    
    if status.warning:
        print(f"\n⚠️ {status.warning}")
    
    # Test model loading check
    print("\n🧪 Model Load Tests:")
    for size in [8, 16, 32, 64, 128]:
        can_load, reason = gov.can_load_model(size)
        icon = "✅" if can_load else "❌"
        print(f"  {icon} {size}GB model: {reason}")
    
    print("\n✅ MemGovernor test complete.")

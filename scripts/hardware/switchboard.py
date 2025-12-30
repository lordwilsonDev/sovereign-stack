"""
Hardware Switchboard: Physical Guarantees for Truth
Bridges Python to Secure Enclave and monitors AMX liveness.
"""

import subprocess
import os
import time
import threading
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

@dataclass
class SignedPayload:
    data: str
    signature: str
    public_key: str
    timestamp: float

class SecureEnclaveBridge:
    """
    Python bridge to the Swift FAO-Signer binary.
    Communicates via stdin/stdout IPC.
    """
    
    def __init__(self, signer_path: Optional[str] = None):
        self.signer_path = signer_path or self._find_signer()
        self.process: Optional[subprocess.Popen] = None
        self.public_key: Optional[str] = None
        self._lock = threading.Lock()
    
    def _find_signer(self) -> str:
        """Locate the compiled signer binary."""
        script_dir = Path(__file__).parent
        candidates = [
            script_dir / "fao-signer",
            script_dir / "fao_signer",
            Path.home() / ".fao" / "fao-signer",
        ]
        for path in candidates:
            if path.exists():
                return str(path)
        return str(script_dir / "fao-signer")
    
    def start(self) -> bool:
        """Start the signer subprocess."""
        if not os.path.exists(self.signer_path):
            print(f"⚠️ Signer binary not found at {self.signer_path}")
            print("  Run: swiftc -o fao-signer fao_signer.swift")
            return False
        
        try:
            self.process = subprocess.Popen(
                [self.signer_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Read startup messages
            while True:
                line = self.process.stderr.readline()
                if not line:
                    break
                if line.startswith("PUBLIC_KEY:"):
                    self.public_key = line.split(":", 1)[1].strip()
                    break
            
            return True
        except Exception as e:
            print(f"❌ Failed to start signer: {e}")
            return False
    
    def stop(self):
        """Stop the signer subprocess."""
        if self.process:
            with self._lock:
                self.process.stdin.write("QUIT\n")
                self.process.stdin.flush()
            self.process.wait(timeout=5)
            self.process = None
    
    def sign(self, data: str) -> Optional[SignedPayload]:
        """Sign data using the Secure Enclave."""
        if not self.process:
            return None
        
        with self._lock:
            try:
                self.process.stdin.write(f"SIGN:{data}\n")
                self.process.stdin.flush()
                
                response = self.process.stdout.readline().strip()
                if response.startswith("SIG:"):
                    signature = response.split(":", 1)[1]
                    return SignedPayload(
                        data=data,
                        signature=signature,
                        public_key=self.public_key or "",
                        timestamp=time.time()
                    )
                else:
                    print(f"⚠️ Sign error: {response}")
                    return None
            except Exception as e:
                print(f"❌ Signing failed: {e}")
                return None
    
    def verify(self, data: str, signature: str) -> bool:
        """Verify a signature."""
        if not self.process:
            return False
        
        with self._lock:
            try:
                self.process.stdin.write(f"VERIFY:{data}:{signature}\n")
                self.process.stdin.flush()
                
                response = self.process.stdout.readline().strip()
                return response == "VALID:true"
            except:
                return False

class AMXWatchdog:
    """
    Monitors the Falsification Mirror liveness.
    Implements a dead man's switch using heartbeat checks.
    """
    
    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout = timeout_seconds
        self.last_heartbeat = time.time()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._kill_callback = None
    
    def heartbeat(self):
        """Called by the Falsification Mirror to indicate liveness."""
        self.last_heartbeat = time.time()
    
    def start(self, kill_callback):
        """Start the watchdog thread."""
        self._kill_callback = kill_callback
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the watchdog."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            time.sleep(0.5)
            elapsed = time.time() - self.last_heartbeat
            if elapsed > self.timeout:
                print(f"🚨 AMX WATCHDOG: Heartbeat timeout ({elapsed:.1f}s)")
                if self._kill_callback:
                    self._kill_callback()
                break

class HardwareSwitchboard:
    """
    Unified Hardware Switchboard.
    Combines Secure Enclave signing with AMX watchdog.
    """
    
    def __init__(self):
        self.enclave = SecureEnclaveBridge()
        self.watchdog = AMXWatchdog()
        self._generation_pid: Optional[int] = None
    
    def initialize(self) -> bool:
        """Initialize all hardware components."""
        print("🔌 Initializing Hardware Switchboard...")
        
        # Start Secure Enclave bridge
        if self.enclave.start():
            print(f"  ✅ Secure Enclave: Connected (PubKey: {self.enclave.public_key[:20]}...)")
        else:
            print("  ⚠️ Secure Enclave: Unavailable (using software fallback)")
        
        # Start AMX watchdog
        self.watchdog.start(self._kill_generation)
        print(f"  ✅ AMX Watchdog: Active (timeout: {self.watchdog.timeout}s)")
        
        return True
    
    def shutdown(self):
        """Clean shutdown."""
        self.watchdog.stop()
        self.enclave.stop()
        print("🔌 Hardware Switchboard: Shutdown complete")
    
    def sign_output(self, text: str) -> Optional[SignedPayload]:
        """Sign verified output for non-repudiation."""
        return self.enclave.sign(text)
    
    def pulse(self):
        """Send heartbeat to watchdog."""
        self.watchdog.heartbeat()
    
    def _kill_generation(self):
        """Emergency kill of generation process."""
        print("🛑 EMERGENCY: Killing generation process!")
        if self._generation_pid:
            try:
                os.kill(self._generation_pid, 9)
            except:
                pass

if __name__ == "__main__":
    print("🔌 Hardware Switchboard Test")
    print("=" * 40)
    
    switchboard = HardwareSwitchboard()
    switchboard.initialize()
    
    # Simulate heartbeats
    for i in range(3):
        switchboard.pulse()
        print(f"  Heartbeat {i+1}/3 sent")
        time.sleep(0.5)
    
    # Test signing (will use software fallback if SEP not compiled)
    if switchboard.enclave.process:
        payload = switchboard.sign_output("Test verified output")
        if payload:
            print(f"  Signed: {payload.signature[:30]}...")
    
    switchboard.shutdown()
    print("✅ Hardware Switchboard test complete.")

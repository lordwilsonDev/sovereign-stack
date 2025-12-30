import hashlib
import json

class FilioqueProtocol:
    """
    Filioque Safety Command: Dual-Source Verification.
    Valid authority must proceed from both Generator and Verifier.
    """
    
    def __init__(self, generator_key="gen_secret", verifier_key="ver_secret"):
        self.generator_key = generator_key
        self.verifier_key = verifier_key

    def sign_action(self, action_payload, key):
        """Simple signature simulator."""
        payload_str = json.dumps(action_payload, sort_keys=True)
        return hashlib.sha256((payload_str + key).encode()).hexdigest()

    def verify_auth(self, action_payload, gen_sig, ver_sig):
        """Check if both signatures are valid for the payload."""
        expected_gen = self.sign_action(action_payload, self.generator_key)
        expected_ver = self.sign_action(action_payload, self.verifier_key)
        
        gen_ok = (gen_sig == expected_gen)
        ver_ok = (ver_sig == expected_ver)
        
        if gen_ok and ver_ok:
            return True, "✅ Filioque Verification Successful: Action Authorized."
        elif gen_ok:
            return False, "❌ Authorization Failed: Missing Verifier Signature."
        elif ver_ok:
            return False, "❌ Authorization Failed: Missing Generator Signature."
        else:
            return False, "❌ Authorization Failed: Both Signatures Invalid."

if __name__ == "__main__":
    protocol = FilioqueProtocol()
    
    action = {"command": "flag_anomaly", "id": "anomaly_01", "severity": "high"}
    
    # Step 1: Generator signs
    gen_sig = protocol.sign_action(action, "gen_secret")
    
    # Step 2: Attempt execution with only one signature
    authorized, msg = protocol.verify_auth(action, gen_sig, None)
    print(msg)
    
    # Step 3: Verifier checks and signs
    ver_sig = protocol.sign_action(action, "ver_secret")
    
    # Step 4: Final verification
    authorized, msg = protocol.verify_auth(action, gen_sig, ver_sig)
    print(msg)

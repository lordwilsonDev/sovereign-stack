# Sovereign Stack: Functional Axiomatic Oracle

**Verified AI on Apple Silicon. No Cloud. No Compromise.**

The Sovereign Stack is a local AI system that can prove when it's telling the truth, detect when it's lying, and sign its outputs cryptographically. Built on a Mac Mini. Open source.

## What This Does That No One Else Has

| Capability | Status |
|------------|--------|
| Token-level truth verification | ✅ |
| Real-time sycophancy detection | ✅ |
| Hardware-signed outputs (Secure Enclave) | ✅ |
| Mathematical alignment (CBF, not RLHF) | ✅ |
| Sub-20ms safety loops | ✅ |
| 100% local, no cloud | ✅ |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  6-STAGE FAO LOOP                                               │
├────────────────┬────────────────────────────────────────────────┤
│ 1. PROPOSAL    │ BitNet b1.58 → candidate token                │
│ 2. SIMULATION  │ V-JEPA → semantic state                       │
│ 3. INSPECTION  │ ∇_input → sycophancy variance                 │
│ 4. ADJUDICATION│ CBF → check h(s) ≥ 0                          │
│ 5. EXECUTION   │ Output or steer                               │
│ 6. ATTESTATION │ Merkle root → SEP signature                   │
└────────────────┴────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/sovereign-stack.git
cd sovereign-stack

# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the 6-stage FAO loop
./sparse_axion_rag fao-loop

# Query with axiom inversion
./sparse_axion_rag query "What are we missing?"

# V-JEPA 4-model ensemble
./sparse_axion_rag vjepa
```

## Components

### Phase 1: Cognitive Substrate
- `scripts/ingestion/ingest_docs.py` - Google Docs → Axiom-JSONL
- `scripts/model/oracle_model.py` - BitNet b1.58 on MLX
- `scripts/safety/` - Nagumo CBF, Filioque verification

### Phase 2: Verification Framework
- `scripts/core/abind.py` - Reality Coherence tracking
- `scripts/mirror/` - Falsification Mirror (NLI + CBF + SelfCheck)
- `scripts/hardware/` - Secure Enclave signing

### Phase 3: Liar's Sweat Protocol
- `scripts/sweat/probe_wrapper.py` - Zero-copy activation extraction
- `scripts/sweat/liars_sweat_probe.py` - Sycophancy detection
- `scripts/sweat/sweat_detector.py` - Real-time monitoring

### Phase 4: Sovereign Stack
- `scripts/sovereign/thermal_loop.py` - Predictive cooling
- `scripts/sovereign/mem_governor.py` - Wired memory tracking
- `scripts/sovereign/merkle_tree.py` - Batch SEP signing
- `scripts/sovereign/fao_loop.py` - 6-stage control loop

### V-JEPA Integration
- `scripts/vjepa/ensemble.py` - ViT-L + ViT-H + ViT-G fusion

## Requirements

- Apple Silicon Mac (M1/M2/M3/M4)
- macOS 14.0+
- Python 3.11+
- 16GB+ RAM (48GB recommended)

## Dependencies

```
mlx
mlx-lm
trio
torch
transformers
sentence-transformers
scikit-learn
```

## Philosophy

> "The centrifuge reasons before it speaks."

Big Tech optimizes for scale and engagement.  
We optimize for truth and sovereignty.

RLHF creates sycophants.  
CBF creates honest systems.

This is alignment by *architecture*, not by *training*.

## License

MIT License - Do whatever you want. Build on it. Make it better.

## Citation

If this helps your research:

```bibtex
@software{sovereign_stack_2024,
  title = {Sovereign Stack: Functional Axiomatic Oracle},
  year = {2024},
  url = {https://github.com/YOUR_USERNAME/sovereign-stack}
}
```

---

**Built on a Mac Mini. Open sourced on a Tuesday.**

import os
import sys
import argparse
import time
import subprocess
from typing import Dict, Any, Optional

try:
    from llama_cpp import Llama
except ImportError:
    print("Error: llama-cpp-python not found. Please install with: CMAKE_ARGS='-DGGML_METAL=on' pip install llama-cpp-python")
    sys.exit(1)

DEFAULT_GGUF_DIR = os.path.join(os.path.dirname(__file__), "models")
BITNET_DIR = os.path.join(os.path.dirname(__file__), "BitNet")

class SovereignNode:
    """
    Bare-Metal Dual-Engine Autonomous Node.
    Orchestrates the FunctionGemma model for tool calling/logic 
    and the BitNet model for memory, reasoning, and standard interactions.
    """
    def __init__(
        self,
        function_gemma_path: str = os.path.join(DEFAULT_GGUF_DIR, "functiongemma", "functiongemma-270m-it-q8_0.gguf"),
        bitnet_path: str = os.path.join(BITNET_DIR, "models", "BitNet-b1.58-2B-4T", "ggml-model-f32.gguf"),
        n_ctx_gemma: int = 4096,
        verbose: bool = False
    ):
        self.verbose = verbose
        self.bitnet_path = bitnet_path
        
        print(f"[*] Initializing Sovereign Node (Apple Silicon Metal Backend)...")
        start_time = time.time()
        
        # Initialize FunctionGemma (Orchestrator)
        print(f"    -> Loading Orchestrator Engine: {function_gemma_path}")
        if not os.path.exists(function_gemma_path):
            raise FileNotFoundError(f"FunctionGemma model not found at: {function_gemma_path}")
            
        self.orchestrator = Llama(
            model_path=function_gemma_path,
            n_ctx=n_ctx_gemma,
            n_gpu_layers=-1, # Accelerate entirely on Mac Neural Engine/GPU
            verbose=self.verbose
        )
        
        # Initialize BitNet (Memory/Reasoning Engine via Microsoft C++ Bindings)
        print(f"    -> Validating Memory Engine Binary: {bitnet_path}")
        if not os.path.exists(bitnet_path):
             raise FileNotFoundError(f"BitNet model not found at: {bitnet_path}")
             
        # BitNet runs out-of-process via the highly optimized C++ inference block
        
        duration = time.time() - start_time
        print(f"[+] Sovereign Node Initialized in {duration:.2f} seconds.")

    def chat_with_memory(self, prompt: str, system_prompt: str = "You are the memory engine, an expert AI.") -> str:
        """Standard chat interface utilizing the highly efficient 1-bit BitNet engine via Subprocess piping."""
        print(f"\n[Memory Engine Querying BitNet C++...]")
        
        # We enforce a pseudo-interactive loop to break the continuous stdin wait on Microsoft's C++ binary
        command = [
            os.path.join(BITNET_DIR, "build", "bin", "llama-cli"),  # Invoke the binary directly rather than python wrapper
            "-m", self.bitnet_path,
            "-n", "200", # Max memory output tokens
            "-ngl", "0", # CRITICAL: BitNet i2_s format must be evaluated on CPU SIMD arrays! 
            "--no-mmap", # Prevent virtual memory clashes with FunctionGemma
            "-p", f"<|system|>{system_prompt}<|end|><|user|>{prompt}<|end|><|assistant|>"
        ]
        
        try:
            # We execute BitNet C++ wrapper directly avoiding python Llama wrapper crash for i2_s format
            # We inject a simulated SIGINT/Quit string into stdin to kill the infinite input loop 
            # that BitNet triggers after generating the first response chunk.
            process = subprocess.run(
                command, 
                cwd=BITNET_DIR, 
                input="quit\n",
                capture_output=True, 
                text=True, 
                check=False
            )
            
            # For `llama-cli`, the actual generation is often dumped into an unbuffered stream or stderr depending on the compile flags
            output = process.stdout + "\n" + process.stderr
            
            # DEBUG: Print the raw output to trace the exact tokens
            print(f"---- RAW C++ STD OUPUT ----")
            print(output)
            print(f"---------------------------")
            
            # The stdout contains our prompt echo. Split by the exact prompt injection tail
            tail = "<|assistant|>"
            if tail in output:
                # The output contains the prompt matching our tail + space/newline + inference response that is then terminated by the quit command injection.
                filtered = output.split(tail, 1)[-1].replace("quit", "").strip()
                # Clean up prompt artifact artifacts and the final EOF lines
                return filtered.split('\n\n\n')[0].strip()
            
            return output.split("quit")[0].strip()
            
        except Exception as e:
            print(f"[-] BitNet Memory Engine Error: {str(e)}")
            return "ERROR_MEMORY_FAULT"


    def execute_tool_call_logic(self, prompt: str, tools: list[Dict[str, Any]] = None) -> str:
        """Leverages Google FunctionGemma to formulate strict logical function executions."""
        # Note: FunctionGemma has specific prompt formatting requirements depending on the prompt structure
        # A full production implementation will translate standard tools to the Gemma instruction format
        print(f"\n[Orchestrator Engine Formatting Task...]")
        
        # Simplified instruction structure for MVP Orchestration
        formatted_prompt = f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
        
        response = self.orchestrator(
            prompt=formatted_prompt,
            max_tokens=512,
            temperature=0.1, # Extremely low temperature for strict functional formatting
            stop=["<end_of_turn>"]
        )
        
        result = response["choices"][0]["text"].strip()
        return result

def test_dual_engine():
     """Standalone boot test for the SovereignNode system."""
     try:
         node = SovereignNode()
         
         # 1. Test the BitNet memory/reasoning architecture
         mem_response = node.chat_with_memory("Explain the concept of Sovereign Computing in three sentences.")
         print(f"\nBitNet Output:\n{mem_response}\n")
         
         # 2. Test the FunctionGemma orchestration tool-logic
         # In reality, this prompt parses a specific JSON schema out based on system tools,
         # but for testing the boot loop, we verify basic structured generation.
         orchestrator_directive = "Given the user's request to 'turn off the lights', what JSON tool array should execute?"
         func_response = node.execute_tool_call_logic(orchestrator_directive)
         print(f"\nFunctionGemma Output:\n{func_response}\n")
         
     except Exception as e:
         print(f"[-] Node Initialization Failed: {e}")

if __name__ == "__main__":
    test_dual_engine()

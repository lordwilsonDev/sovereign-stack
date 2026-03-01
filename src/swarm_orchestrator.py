import os
import torch
import controlflow as cf
from pydantic import BaseModel
from controlflow.orchestration.turn_strategies import Moderated
from twelvelabs import TwelveLabs
from transformers import AutoModelForCausalLM
from janus.models import MultiModalityCausalLM, VLChatProcessor

print("========== BOOTING SOVEREIGN COGNITIVE ENGINE ==========")

# ---------------------------------------------------------
# COMPONENT 1: LOCAL DEEPSEEK JANUS-PRO INITIALIZATION
# ---------------------------------------------------------
device = torch.device(os.getenv("DEVICE_BACKEND", "mps"))
print(f"[*] Hardware Execution Target: {device}")

# NOTE: Instantiating the 1.5B model to fit within the 16GB Apple Silicon Unified Memory constraints.
model_path = "deepseek-ai/Janus-Pro-1B" 
try:
    processor = VLChatProcessor.from_pretrained(model_path)
    # Enforcing bfloat16 for Apple Silicon memory stability
    model = AutoModelForCausalLM.from_pretrained(
        model_path, trust_remote_code=True
    ).to(torch.bfloat16).to(device).eval()
    print("[*] Janus-Pro-1B Successfully Loaded into Unified Memory.")
except Exception as e:
    print(f"[!] Local Model Load Deferred: {e}")

# ---------------------------------------------------------
# COMPONENT 2: TWELVE LABS TEMPORAL VIDEO INTEGRATION
# ---------------------------------------------------------
twelvelabs_client = TwelveLabs(api_key=os.getenv('TWELVE_LABS_API_KEY', 'default_key'))

@cf.tool
def analyze_local_tactical_image(image_path: str, query: str) -> str:
    """Tool for agents to extract tactical insights from a local image file using offline Janus-Pro."""
    try:
        from PIL import Image
        print(f"  [Janus-Pro-1B] Analyzing {image_path}...")
        image = Image.open(image_path).convert("RGB")
        conversation = [
            {
                "role": "<|User|>",
                "content": f"<image_placeholder>\n{query}",
                "images": [image],
            },
            {"role": "<|Assistant|>", "content": ""},
        ]
        
        prepare_inputs = processor(
            conversations=conversation, images=[image], force_batchify=True
        ).to(device, dtype=torch.bfloat16)
        
        inputs_embeds = model.prepare_inputs_embeds(**prepare_inputs)
        
        outputs = model.language_model.generate(
            inputs_embeds=inputs_embeds,
            attention_mask=prepare_inputs.attention_mask,
            pad_token_id=processor.tokenizer.eos_token_id,
            bos_token_id=processor.tokenizer.bos_token_id,
            eos_token_id=processor.tokenizer.eos_token_id,
            max_new_tokens=256,
            do_sample=False,
            use_cache=True,
        )
        
        answer = processor.tokenizer.decode(outputs[0].cpu().tolist(), skip_special_tokens=True)
        return answer
    except Exception as e:
        return f"Image Analysis Failed: {str(e)}"

# ---------------------------------------------------------
# COMPONENT 3: CONTROLFLOW MULTI-AGENT ORCHESTRATION
# ---------------------------------------------------------
class IntelligenceReport(BaseModel):
    threat_assessment: str
    semantic_vectors_identified: bool
    recommended_action: str

# Define Specialized Autonomous Entities
analyst_agent = cf.Agent(
    name="VisionAnalyst", 
    instructions="Analyze provided visual data through the analyze_local_tactical_image tool. Maintain absolute precision.",
    tools=[analyze_local_tactical_image]
)

supervisor_agent = cf.Agent(
    name="StackSupervisor", 
    instructions="Review the Analyst's work. Ensure the final report strictly adheres to type-safe schema and operational protocol. Reject hallucinations."
)

@cf.flow
def autonomous_intelligence_pipeline(target_image: str):
    print(f"[*] Initiating Multi-Agent Workflow for: {target_image}\n")
    
    # Task 1: Extraction
    extraction_context = cf.run(
        f"Analyze the tactical image at {target_image}. Ask the vision model to describe precisely what is in the scene, identifying any aerial vehicles.", 
        agents=[analyst_agent]
    )
    
    # Task 2: Moderated Synthesis
    report = cf.run(
        "Compile final actionable intelligence report based on the extraction.",
        result_type=IntelligenceReport,
        agents=[analyst_agent],
        turn_strategy=Moderated(moderator=supervisor_agent),
        context={"extraction_data": extraction_context}
    )
    return report

if __name__ == "__main__":
    print("[*] System Online. Triggering Test Workflow on sample_tactical.jpg...")
    # Demo Execution
    result = autonomous_intelligence_pipeline("./src/sample_tactical.jpg")
    print("\n========== FINAL ACTIONABLE INTELLIGENCE REPORT ==========\n")
    print(result.model_dump_json(indent=2))

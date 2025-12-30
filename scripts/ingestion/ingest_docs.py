import os
import json
import re
from docx import Document
from pathlib import Path

def get_structural_weight(paragraph):
    """Assign importance score based on heading level/boldness."""
    style = paragraph.style.name.lower()
    if 'heading 1' in style:
        return 5.0
    elif 'heading 2' in style:
        return 4.0
    elif 'heading 3' in style or 'heading 4' in style:
        return 3.0
    
    # Check for boldness in the first few runs
    is_bold = any(run.bold for run in paragraph.runs[:3])
    if is_bold:
        return 2.0
    
    return 1.0

def extract_axiom_candidates(text):
    """Identify sentences with high-modality keywords."""
    keywords = ["must", "always", "never", "critical", "essential", "crucial", "fundamental", "axiom", "rule"]
    sentences = re.split(r'(?<=[.!?]) +', text)
    candidates = []
    for sentence in sentences:
        if any(word in sentence.lower() for word in keywords):
            candidates.append(sentence.strip())
    return candidates

def parse_docx(file_path):
    """Extract structural elements and axioms from a .docx file."""
    doc = Document(file_path)
    units_of_thought = []
    current_context = ""
    
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text:
            continue
            
        weight = get_structural_weight(para)
        
        # Heading 1 acts as a Context Frame
        if weight >= 4.0:
            current_context = text
            
        axiom_candidates = extract_axiom_candidates(text)
        
        for candidate in axiom_candidates:
            # Simple causal link detector
            causal_link = "Because/Therefore" if any(kw in text.lower() for kw in ["because", "therefore", "leads to", "since"]) else "Independent"
            
            unit = {
                "doc_id": os.path.basename(file_path),
                "context_window": text,
                "axiom_candidate": candidate,
                "structural_weight": weight,
                "causal_link": causal_link,
                "context_frame": current_context
            }
            units_of_thought.append(unit)
            
    return units_of_thought

def main():
    source_dir = Path("/Users/lordwilson/model training data set 1/unzipped")
    output_path = Path("/Users/lordwilson/sparse_axion_rag/output/axiom_dataset.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    all_units = []
    docx_files = list(source_dir.glob("*.docx"))
    
    print(f"🔄 Processing {len(docx_files)} files...")
    
    for docx_file in docx_files:
        try:
            units = parse_docx(str(docx_file))
            all_units.extend(units)
        except Exception as e:
            print(f"❌ Error parsing {docx_file.name}: {e}")
            
    with open(output_path, 'w') as f:
        for unit in all_units:
            f.write(json.dumps(unit) + '\n')
            
    print(f"✅ Ingestion complete. Extracted {len(all_units)} units of thought.")
    print(f"📁 Dataset saved to {output_path}")

if __name__ == "__main__":
    main()

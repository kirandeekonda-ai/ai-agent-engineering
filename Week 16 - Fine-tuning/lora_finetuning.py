"""
Week 16: Fine-tuning LLMs with LoRA/PEFT

This script demonstrates:
1. Understanding LoRA (Low-Rank Adaptation)
2. PEFT (Parameter-Efficient Fine-Tuning) concepts
3. Fine-tuning workflow simulation
4. Comparing base vs fine-tuned models

Note: Full fine-tuning requires GPU. This is a conceptual demonstration.
"""
from pathlib import Path
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Load .env from parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# --- FINE-TUNING CONCEPTS ---
"""
LoRA (Low-Rank Adaptation):
- Instead of updating all model weights, inject small trainable matrices
- Reduces trainable params by 10-1000x
- Original: W (frozen) + ΔW (trainable, low-rank)

QLoRA (Quantized LoRA):
- Quantize base model to 4-bit
- Apply LoRA on top
- Further reduces memory by 4x

PEFT (Parameter-Efficient Fine-Tuning):
- Library from Hugging Face
- Supports LoRA, Prefix Tuning, Prompt Tuning, etc.
"""

# --- SIMULATED FINE-TUNING DATASET ---
TRAINING_DATA = [
    {
        "instruction": "Classify the sentiment of this review",
        "input": "This product is amazing! Best purchase ever.",
        "output": "POSITIVE"
    },
    {
        "instruction": "Classify the sentiment of this review",
        "input": "Terrible quality, broke after one day.",
        "output": "NEGATIVE"
    },
    {
        "instruction": "Classify the sentiment of this review",
        "input": "It's okay, nothing special but works fine.",
        "output": "NEUTRAL"
    },
    {
        "instruction": "Classify the sentiment of this review",
        "input": "Absolutely love it! Exceeded expectations.",
        "output": "POSITIVE"
    },
    {
        "instruction": "Classify the sentiment of this review",
        "input": "Waste of money. Very disappointed.",
        "output": "NEGATIVE"
    }
]

TEST_DATA = [
    ("Great value for the price!", "POSITIVE"),
    ("Stopped working after a week.", "NEGATIVE"),
    ("Average product, does the job.", "NEUTRAL"),
]

# --- LORA CONFIG (Conceptual) ---
@dataclass
class LoRAConfig:
    """LoRA hyperparameters."""
    r: int = 8              # Rank of low-rank matrices
    alpha: int = 16         # Scaling factor
    dropout: float = 0.1    # Dropout for regularization
    target_modules: list = None  # Layers to apply LoRA
    
    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = ["q_proj", "v_proj"]  # Typical for transformers

# --- FINE-TUNING SIMULATOR ---
class FineTuningSimulator:
    """Simulates fine-tuning workflow (conceptual)."""
    
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model_name="llama-3.1-8b-instant",
            api_key=os.environ.get("GROQ_API_KEY")
        )
        self.config = LoRAConfig()
        self.fine_tuned = False
    
    def show_lora_config(self):
        """Display LoRA configuration."""
        print("\n" + "=" * 60)
        print("LoRA Configuration")
        print("=" * 60)
        print(f"  Rank (r): {self.config.r}")
        print(f"  Alpha: {self.config.alpha}")
        print(f"  Dropout: {self.config.dropout}")
        print(f"  Target Modules: {self.config.target_modules}")
        print(f"\n  Trainable params: ~0.1% of total (vs 100% full fine-tune)")
        print(f"  Memory reduction: ~4x with QLoRA")
    
    def simulate_training(self):
        """Simulate fine-tuning process."""
        print("\n" + "=" * 60)
        print("Simulating Fine-tuning Process")
        print("=" * 60)
        
        print(f"\n📦 Dataset: {len(TRAINING_DATA)} training examples")
        print(f"🎯 Task: Sentiment Classification")
        print(f"⚙️  Method: LoRA (r={self.config.r})")
        
        # Simulate epochs
        for epoch in range(1, 4):
            loss = 1.5 - (epoch * 0.4)  # Simulated decreasing loss
            print(f"\n  Epoch {epoch}/3:")
            print(f"    Loss: {loss:.4f}")
            print(f"    Learning rate: {0.0001 / epoch:.6f}")
        
        print("\n✅ Fine-tuning complete!")
        self.fine_tuned = True
    
    def base_model_predict(self, text: str) -> str:
        """Predict with base model (verbose output)."""
        response = self.llm.invoke([
            SystemMessage(content="You are a sentiment classifier. Respond with only: POSITIVE, NEGATIVE, or NEUTRAL."),
            HumanMessage(content=f"Classify: {text}")
        ])
        return response.content.strip().upper()
    
    def fine_tuned_predict(self, text: str) -> str:
        """Predict with 'fine-tuned' model (improved prompt)."""
        # Simulate fine-tuned behavior with few-shot examples
        examples = "\n".join([
            f"Review: {d['input']} -> {d['output']}"
            for d in TRAINING_DATA[:3]
        ])
        
        response = self.llm.invoke([
            SystemMessage(content=f"""You are a fine-tuned sentiment classifier.
You have been trained on these examples:
{examples}

Always respond with exactly one word: POSITIVE, NEGATIVE, or NEUTRAL."""),
            HumanMessage(content=f"Classify: {text}")
        ])
        
        # Extract just the classification
        content = response.content.strip().upper()
        for label in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
            if label in content:
                return label
        return content
    
    def evaluate(self):
        """Compare base vs fine-tuned performance."""
        print("\n" + "=" * 60)
        print("Evaluation: Base vs Fine-tuned")
        print("=" * 60)
        
        base_correct = 0
        ft_correct = 0
        
        for text, expected in TEST_DATA:
            base_pred = self.base_model_predict(text)
            ft_pred = self.fine_tuned_predict(text)
            
            base_match = "✅" if expected in base_pred else "❌"
            ft_match = "✅" if expected in ft_pred else "❌"
            
            if expected in base_pred:
                base_correct += 1
            if expected in ft_pred:
                ft_correct += 1
            
            print(f"\n  Input: '{text[:40]}...'")
            print(f"  Expected: {expected}")
            print(f"  Base:     {base_pred[:10]} {base_match}")
            print(f"  Fine-tuned: {ft_pred[:10]} {ft_match}")
        
        print("\n" + "-" * 40)
        print(f"Base Model Accuracy: {base_correct}/{len(TEST_DATA)}")
        print(f"Fine-tuned Accuracy: {ft_correct}/{len(TEST_DATA)}")

# --- REAL FINE-TUNING CODE (Reference) ---
REAL_FINETUNING_CODE = '''
# Real LoRA Fine-tuning with PEFT (requires GPU)

from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer

# 1. Load base model
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    load_in_4bit=True,  # QLoRA
    device_map="auto"
)

# 2. Configure LoRA
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.1,
    task_type=TaskType.CAUSAL_LM
)

# 3. Apply PEFT
model = get_peft_model(model, lora_config)

# 4. Train
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    args=TrainingArguments(
        output_dir="./fine-tuned",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        learning_rate=2e-4,
    )
)
trainer.train()

# 5. Save and merge
model.save_pretrained("./lora-adapter")
# Or merge: merged = model.merge_and_unload()
'''

# --- MAIN ---
if __name__ == "__main__":
    import sys
    
    simulator = FineTuningSimulator()
    
    if len(sys.argv) > 1 and sys.argv[1] == "code":
        print("=" * 60)
        print("Real LoRA Fine-tuning Code (requires GPU)")
        print("=" * 60)
        print(REAL_FINETUNING_CODE)
    else:
        # Demo workflow
        print("=" * 60)
        print("WEEK 16: Fine-tuning LLMs with LoRA")
        print("=" * 60)
        
        # 1. Show config
        simulator.show_lora_config()
        
        # 2. Simulate training
        simulator.simulate_training()
        
        # 3. Evaluate
        simulator.evaluate()
        
        print("\n" + "=" * 60)
        print("KEY TAKEAWAYS")
        print("=" * 60)
        print("""
1. LoRA reduces trainable params by 100-1000x
2. QLoRA adds 4-bit quantization for 4x memory savings
3. PEFT library makes it easy to apply
4. Fine-tuned models are more consistent for specific tasks
5. Use 'code' argument to see real implementation
        """)

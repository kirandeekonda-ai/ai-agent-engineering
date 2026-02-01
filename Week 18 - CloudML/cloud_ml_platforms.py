"""
Week 18: Cloud ML Platforms & MLflow

This script demonstrates:
1. Cloud ML platform comparison
2. MLflow experiment tracking (simulated)
3. Model registry concepts
4. CI/CD for ML models
"""
from pathlib import Path
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
import random

# Load .env from parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# --- CLOUD ML PLATFORM COMPARISON ---
CLOUD_PLATFORMS = {
    "AWS SageMaker": {
        "provider": "Amazon",
        "features": ["Built-in algorithms", "AutoML", "Endpoints", "Pipelines"],
        "best_for": "AWS-native teams",
        "pricing": "Pay-per-use (instances + storage)",
        "llm_support": "Bedrock integration"
    },
    "Azure ML": {
        "provider": "Microsoft",
        "features": ["Designer UI", "AutoML", "MLOps", "Responsible AI"],
        "best_for": "Enterprise, Microsoft ecosystem",
        "pricing": "Pay-per-use + workspace fee",
        "llm_support": "Azure OpenAI integration"
    },
    "GCP Vertex AI": {
        "provider": "Google",
        "features": ["AutoML", "Feature Store", "Model Garden", "Pipelines"],
        "best_for": "Data-heavy workloads",
        "pricing": "Pay-per-use (training + prediction)",
        "llm_support": "PaLM, Gemini native"
    },
    "MLflow": {
        "provider": "Open Source (Databricks)",
        "features": ["Tracking", "Registry", "Projects", "Serving"],
        "best_for": "Platform-agnostic, portability",
        "pricing": "Free (self-hosted) or Databricks",
        "llm_support": "Any LLM via logging"
    }
}

# --- MLFLOW SIMULATOR ---
@dataclass
class Experiment:
    name: str
    experiment_id: str
    runs: list = None
    
    def __post_init__(self):
        self.runs = self.runs or []

@dataclass
class Run:
    run_id: str
    experiment_id: str
    start_time: str
    params: dict
    metrics: dict
    model_path: Optional[str] = None
    status: str = "FINISHED"

class MLflowSimulator:
    """Simulates MLflow experiment tracking."""
    
    def __init__(self, tracking_dir: str = "mlflow_tracking"):
        self.tracking_path = Path(__file__).parent / tracking_dir
        self.tracking_path.mkdir(exist_ok=True)
        self.experiments: dict[str, Experiment] = {}
        self.active_run: Optional[Run] = None
        self._load()
    
    def _load(self):
        """Load existing experiments."""
        exp_file = self.tracking_path / "experiments.json"
        if exp_file.exists():
            with open(exp_file) as f:
                data = json.load(f)
                for exp_data in data:
                    exp = Experiment(**exp_data)
                    self.experiments[exp.name] = exp
    
    def _save(self):
        """Save experiments."""
        exp_file = self.tracking_path / "experiments.json"
        with open(exp_file, "w") as f:
            json.dump([asdict(e) for e in self.experiments.values()], f, indent=2)
    
    def create_experiment(self, name: str) -> str:
        """Create new experiment."""
        exp_id = f"exp_{len(self.experiments)}"
        self.experiments[name] = Experiment(name=name, experiment_id=exp_id)
        self._save()
        print(f"  [MLFLOW] Created experiment '{name}' (ID: {exp_id})")
        return exp_id
    
    def start_run(self, experiment_name: str) -> str:
        """Start a new run."""
        if experiment_name not in self.experiments:
            self.create_experiment(experiment_name)
        
        exp = self.experiments[experiment_name]
        run_id = f"run_{len(exp.runs)}"
        
        self.active_run = Run(
            run_id=run_id,
            experiment_id=exp.experiment_id,
            start_time=datetime.now().isoformat(),
            params={},
            metrics={}
        )
        
        print(f"  [MLFLOW] Started run '{run_id}'")
        return run_id
    
    def log_param(self, key: str, value):
        """Log a parameter."""
        if self.active_run:
            self.active_run.params[key] = str(value)
            print(f"    Param: {key}={value}")
    
    def log_metric(self, key: str, value: float):
        """Log a metric."""
        if self.active_run:
            self.active_run.metrics[key] = value
            print(f"    Metric: {key}={value:.4f}")
    
    def log_model(self, model_path: str):
        """Log model artifact."""
        if self.active_run:
            self.active_run.model_path = model_path
            print(f"    Model: {model_path}")
    
    def end_run(self):
        """End the current run."""
        if self.active_run:
            exp_name = None
            for name, exp in self.experiments.items():
                if exp.experiment_id == self.active_run.experiment_id:
                    exp.runs.append(asdict(self.active_run))
                    exp_name = name
                    break
            
            print(f"  [MLFLOW] Ended run '{self.active_run.run_id}'")
            self.active_run = None
            self._save()
    
    def list_experiments(self):
        """List all experiments."""
        print("\n" + "=" * 60)
        print("MLFLOW EXPERIMENTS")
        print("=" * 60)
        
        for name, exp in self.experiments.items():
            print(f"\n📊 {name} (ID: {exp.experiment_id})")
            print(f"   Runs: {len(exp.runs)}")
            
            for run in exp.runs[-3:]:  # Show last 3 runs
                print(f"   └─ {run['run_id']}: {run['metrics']}")

# --- CI/CD CONCEPTS ---
CICD_PIPELINE = """
# ML CI/CD Pipeline Example (GitHub Actions)

name: ML Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  train:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run training
        run: python train.py
        env:
          MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_URI }}
      
      - name: Evaluate model
        run: python evaluate.py
      
      - name: Register model (if metrics pass)
        run: python register_model.py
        if: success()

  deploy:
    needs: train
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: python deploy.py
"""

# --- MAIN ---
def demo_platform_comparison():
    """Show cloud platform comparison."""
    print("=" * 60)
    print("CLOUD ML PLATFORM COMPARISON")
    print("=" * 60)
    
    for name, info in CLOUD_PLATFORMS.items():
        print(f"\n☁️  {name}")
        print(f"   Provider: {info['provider']}")
        print(f"   Features: {', '.join(info['features'])}")
        print(f"   Best for: {info['best_for']}")
        print(f"   LLM Support: {info['llm_support']}")

def demo_mlflow():
    """Demo MLflow tracking."""
    print("\n" + "=" * 60)
    print("MLFLOW EXPERIMENT TRACKING")
    print("=" * 60)
    
    mlflow = MLflowSimulator()
    
    # Simulate training runs
    for i in range(3):
        mlflow.start_run("sentiment-classifier")
        
        # Log params
        lr = 0.001 * (i + 1)
        epochs = 3 + i
        mlflow.log_param("learning_rate", lr)
        mlflow.log_param("epochs", epochs)
        mlflow.log_param("model", "bert-base")
        
        # Log metrics (simulated)
        accuracy = 0.85 + (random.random() * 0.1)
        loss = 0.5 - (i * 0.1) + random.random() * 0.1
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("loss", max(0.1, loss))
        
        # Log model
        mlflow.log_model(f"models/sentiment_v{i+1}")
        
        mlflow.end_run()
    
    # List all experiments
    mlflow.list_experiments()

def demo_cicd():
    """Show CI/CD pipeline."""
    print("\n" + "=" * 60)
    print("ML CI/CD PIPELINE")
    print("=" * 60)
    print(CICD_PIPELINE)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "compare":
            demo_platform_comparison()
        elif mode == "mlflow":
            demo_mlflow()
        elif mode == "cicd":
            demo_cicd()
    else:
        demo_platform_comparison()
        demo_mlflow()
        
        print("\n" + "=" * 60)
        print("KEY TAKEAWAYS")
        print("=" * 60)
        print("""
1. Choose cloud platform based on existing ecosystem
2. MLflow provides platform-agnostic tracking
3. Track params, metrics, and models for reproducibility
4. CI/CD automates training → evaluation → deployment
5. Model registry enables versioning and rollback
        """)

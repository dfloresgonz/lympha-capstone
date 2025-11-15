from experiments.registry import MODEL_REGISTRY
import time


def run_experiments(datasets, horizons, models):
  batch_id = str(int(time.time()))
  for model_name in models:
    # safely get registry entry to avoid KeyError when a model isn't registered
    entry = MODEL_REGISTRY.get(model_name)
    if entry is None:
      print(f"⚠️ Model {model_name} not found in registry, skipping...")
      continue
    train_fn = entry["train_fn"]
    for dataset in datasets:
      for horizon in horizons:
        params = {
            "dataset": dataset,
            "input_len": 96,
            "output_len": horizon,
            "d_model": 64,
            "n_layers": 2,
            "scales": [12, 24, 48],
            "batch_size": 64,
            "epochs": 10,
            "learning_rate": 1e-3,
            "weight_decay": 1e-4,
        }
        print(f"\n🚀 Training {model_name} on {dataset} (H={horizon})")
        train_fn(params, batch_id)

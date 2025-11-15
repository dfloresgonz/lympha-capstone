import os
import mlflow
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from models.micn import MICNModel
from models.micn.utils.windowing import create_windows, split_data, make_dataloaders
from models.micn.utils.metrics import mse, mae

mlflow.set_tracking_uri("http://127.0.0.1:5000")


def get_device():
  if torch.backends.mps.is_available():
    return torch.device("mps")
  return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_and_prepare_data(params):
  df = pd.read_csv(os.path.join("../data", f"{params['dataset']}.csv"))
  features = df.drop(columns=["date", "site_id"]).values.astype("float32")

  target_col = "pH"
  target_idx = df.drop(columns=["date", "site_id"]).columns.get_loc(target_col)

  X, Y_all = create_windows(features, input_len=params["input_len"], output_len=params["output_len"])
  Y = Y_all[:, :, [target_idx]]
  (X_train, Y_train), (X_val, Y_val), (X_test, Y_test) = split_data(X, Y)

  train_loader, val_loader, test_loader, mean, std = make_dataloaders(
      X_train, Y_train, X_val, Y_val, X_test, Y_test,
      batch_size=params["batch_size"]
  )

  num_features = features.shape[1]
  return train_loader, val_loader, test_loader, mean, std, num_features


def build_model(params, device, num_features):
  model = MICNModel(
      input_len=params["input_len"],
      output_len=params["output_len"],
      d_model=params["d_model"],
      n_layers=params["n_layers"],
      scales=tuple(params["scales"]),
      num_features=num_features
  ).to(device)
  return model


def setup_optimizer_and_loss(model, params):
  optimizer = torch.optim.Adam(
      model.parameters(),
      lr=params["learning_rate"],
      weight_decay=params.get("weight_decay", 0.0)
  )
  loss_fn = nn.MSELoss()
  return optimizer, loss_fn


def train_one_epoch(model, train_loader, loss_fn, optimizer, device):
  model.train()
  train_losses, train_maes = [], []

  for xb, yb in train_loader:
    xb, yb = xb.to(device), yb.to(device)
    optimizer.zero_grad()
    yhat, _, _ = model(xb)
    loss = loss_fn(yhat, yb)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()

    train_losses.append(loss.item())
    train_maes.append(mae(yb, yhat).item())

  return train_losses, train_maes


def validate_one_epoch(model, val_loader, loss_fn, device):
  model.eval()
  val_losses, val_maes = [], []

  with torch.no_grad():
    for xb, yb in val_loader:
      xb, yb = xb.to(device), yb.to(device)
      yhat, _, _ = model(xb)
      loss = loss_fn(yhat, yb)
      val_losses.append(loss.item())
      val_maes.append(mae(yb, yhat).item())

  return val_losses, val_maes


def train_model(model, train_loader, val_loader, test_loader, loss_fn, optimizer, device, params, batch_id, mean, std):
  best_val = float("inf")

  with mlflow.start_run(run_name=f"{params['dataset']}_H{params['output_len']}", tags={"batch_id": batch_id}):
    mlflow.log_params(params)
    mlflow.log_param("norm_mean", np.round(mean.flatten(), 4).tolist())
    mlflow.log_param("norm_std", np.round(std.flatten(), 4).tolist())

    for epoch in range(params["epochs"]):
      train_losses, train_maes = train_one_epoch(model, train_loader, loss_fn, optimizer, device)
      val_losses, val_maes = validate_one_epoch(model, val_loader, loss_fn, device)

      tr_mse = sum(train_losses) / len(train_losses) if train_losses else float("nan")
      va_mse = sum(val_losses) / len(val_losses) if val_losses else float("nan")
      tr_mae = sum(train_maes) / len(train_maes) if train_maes else float("nan")
      va_mae = sum(val_maes) / len(val_maes) if val_maes else float("nan")

      mlflow.log_metric("train_mse", tr_mse, step=epoch)
      mlflow.log_metric("val_mse", va_mse, step=epoch)
      mlflow.log_metric("train_mae", tr_mae, step=epoch)
      mlflow.log_metric("val_mae", va_mae, step=epoch)

      print(
          f"[{params['dataset']} | H={params['output_len']}] "
          f"Epoch {epoch+1}/{params['epochs']}  Train MSE={tr_mse:.4f}  Val MSE={va_mse:.4f} "
          f"Train MAE={tr_mae:.4f}  Val MAE={va_mae:.4f}"
      )

    # Evaluación final
    test_mse, test_mae_ = evaluate_on_test(model, test_loader, device)
    mlflow.log_metric("test_mse", test_mse)
    mlflow.log_metric("test_mae", test_mae_)
    print(f"TEST  MSE={test_mse:.4f}  MAE={test_mae_:.4f}")

    if va_mse < best_val:
      best_val = va_mse
      torch.save(model.state_dict(), "best.pt")
      mlflow.log_artifact("best.pt")

  return best_val


def evaluate_on_test(model, test_loader, device):
  model.eval()
  test_losses_mse, test_losses_mae = [], []

  with torch.no_grad():
    for xb, yb in test_loader:
      xb, yb = xb.to(device), yb.to(device)
      yhat, _, _ = model(xb)
      test_losses_mse.append(mse(yb, yhat).item())
      test_losses_mae.append(mae(yb, yhat).item())

  test_mse = sum(test_losses_mse) / max(1, len(test_losses_mse))
  test_mae = sum(test_losses_mae) / max(1, len(test_losses_mae))
  return test_mse, test_mae


def train_and_eval_model(params, batch_id):
  # device setup
  device = get_device()
  print("Using device:", device)
  print("batch_id:", batch_id)

  # mlflow inicializar
  experiment_sufix = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
  experiment_name = f"MICN_H{params['output_len']}_{experiment_sufix}_multifeature"
  mlflow.set_experiment(experiment_name)

  # 1) Carga y ventanas
  train_loader, val_loader, test_loader, mean, std, num_features = load_and_prepare_data(params)

  # 2) Modelo
  model = build_model(params, device, num_features)

  # 3) Optimizador y pérdida
  optimizer, loss_fn = setup_optimizer_and_loss(model, params)

  # 4) Entrenamiento y registro de metricas en mlflow
  best_val = train_model(model, train_loader, val_loader, test_loader, loss_fn,
                         optimizer, device, params, batch_id, mean, std)
  return best_val

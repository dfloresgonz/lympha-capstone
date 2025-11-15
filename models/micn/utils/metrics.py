import torch


def mse(y_true, y_pred):
  return torch.mean((y_true - y_pred) ** 2)


def mae(y_true, y_pred):
  return torch.mean(torch.abs(y_true - y_pred))

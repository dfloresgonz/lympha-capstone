import torch
import torch.nn as nn


class TrendRegression(nn.Module):
  """
  Predice la tendencia Xt hacia el futuro con una proyección lineal temporal:
  - Entrada: Xt [B, C, L]  (C = num_features)
  - Salida:  Ytrend [B, C, O]
  Implementa MICN-regre con nn.Linear(L, O) aplicada por canal.
  """

  def __init__(self, input_len: int, output_len: int):
    super().__init__()
    self.input_len = input_len
    self.output_len = output_len
    self.head = nn.Linear(input_len, output_len, bias=True)

  def forward(self, Xt):
    B, C, L = Xt.shape
    assert L == self.input_len, f"Expected input_len={self.input_len}, got {L}"

    y = self.head(Xt)
    return y

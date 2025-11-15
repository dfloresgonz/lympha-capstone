import torch.nn as nn
from .decomposition import MHDecomp
from .regression import TrendRegression
from .mic_layers import MICLayers


class MICNModel(nn.Module):
  """
  Ensamble:
  - MHDecomp → Xt, Xs
  - TrendRegression(Xt) → Ytrend
  - MICLayers(Xs) → Yseasonal
  - Ypred = Ytrend + Yseasonal
  """

  def __init__(self, input_len=96, output_len=24,
               d_model=64, n_layers=1, scales=(12, 24, 48), num_features=1):
    super().__init__()
    self.input_len = input_len
    self.output_len = output_len

    self.decomp = MHDecomp(kernel_sizes=scales)
    self.trend = TrendRegression(input_len=input_len, output_len=output_len)
    self.mic = MICLayers(input_len=input_len, output_len=output_len,
                         d_model=d_model, n_layers=n_layers, scales=scales, num_features=num_features)

  def forward(self, X):
    Xt, Xs = self.decomp(X)
    Ytrend = self.trend(Xt)
    Yseasonal = self.mic(Xs)
    return Ytrend + Yseasonal, Ytrend, Yseasonal

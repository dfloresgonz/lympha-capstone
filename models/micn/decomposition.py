import torch
import torch.nn as nn


class MHDecomp(nn.Module):
  def __init__(self, kernel_sizes=(12, 24, 48)):
    super().__init__()
    self.kernel_sizes = kernel_sizes
    self.pools = nn.ModuleList([nn.AvgPool1d(k, stride=1, ceil_mode=False) for k in kernel_sizes])

  def _pad_reflect(self, x, k):
    p = (k - 1) // 2
    if k % 2 == 0:
      return nn.functional.pad(x, (p, p+1), mode="reflect")
    return nn.functional.pad(x, (p, p), mode="reflect")

  def forward(self, X):
    smoothed = []
    for k, pool in zip(self.kernel_sizes, self.pools):
      z = self._pad_reflect(X, k)
      z = pool(z)
      smoothed.append(z)
    Xt = torch.stack(smoothed, dim=0).mean(dim=0)  # promedio de escalas → tendencia
    Xs = X - Xt  # residuo → estacionalidad
    return Xt, Xs

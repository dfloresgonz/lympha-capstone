import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class _MICBranch(nn.Module):
  """
  Una rama MIC para una escala 's':
    - Local: AvgPool1d(scale, stride=scale) + Conv1d(d,d,3)
    - Global (isometric): Conv1d(d,d, kernel=reduced_len) a nivel global
    - Upsampling: ConvTranspose1d(d,d, kernel=scale, stride=scale)
  """

  def __init__(self, d_model: int, input_len: int, output_len: int, scale: int):
    super().__init__()
    self.scale = scale
    self.ext_len = input_len + output_len

    # Local downsample
    self.pool = nn.AvgPool1d(kernel_size=scale, stride=scale, ceil_mode=False)
    self.local_conv = nn.Conv1d(d_model, d_model, kernel_size=3, padding=1)

    # El largo reducido tras pool:
    self.reduced_len = math.floor((self.ext_len - scale)/scale + 1) if self.ext_len >= scale else 1
    self.reduced_len = max(1, self.reduced_len)

    # Global isometric conv: kernel abarca toda la secuencia reducida
    self.global_conv = nn.Conv1d(d_model, d_model, kernel_size=self.reduced_len, padding=0)

    # Upsampling para volver a longitud extendida
    self.up = nn.ConvTranspose1d(d_model, d_model, kernel_size=scale, stride=scale)

    self.norm = nn.LayerNorm(d_model)
    self.act = nn.GELU()

  def forward(self, Xext):  # Xext: [B, d, Lext]
    B, D, Lext = Xext.shape

    # Local module
    loc = self.pool(Xext)
    loc = self.local_conv(loc)
    loc = self.act(loc)

    # Global isometric: conv con kernel = Lr
    # produce [B, d, 1], repetimos a Lr para continuidad residual
    glob = self.global_conv(loc)
    glob = glob.repeat(1, 1, loc.shape[-1])

    # Fusión simple local+global (suma)
    fused = self.act(loc + glob)

    # Upsampling a longitud extendida aproximada
    up = self.up(fused)
    if up.shape[-1] < Lext:
      up = F.pad(up, (0, Lext - up.shape[-1]))
    elif up.shape[-1] > Lext:
      up = up[..., :Lext]

    # LayerNorm por canal (permuta para LN)
    y = self.norm(up.transpose(1, 2)).transpose(1, 2)  # LN sobre d_model
    return y


class MICLayers(nn.Module):
  """
  Seasonal Prediction Block
  - Embedding (1→d_model)
  - Concat Xs con ceros para cubrir futuro
  - Ramas multi-escala (local+global)
  - Merge (promedio) + proyección a 1 canal
  - Recorte a los últimos O pasos
  """

  def __init__(self, input_len: int, output_len: int, d_model=64, n_layers=1, scales=(12, 24, 48), num_features=1):
    super().__init__()
    self.input_len = input_len
    self.output_len = output_len
    self.d_model = d_model
    self.n_layers = n_layers
    self.scales = scales
    self.num_features = num_features

    # Value embedding 1→d_model
    self.value_emb = nn.Conv1d(num_features, d_model, kernel_size=1)

    # Construimos ramas por escala (en cada capa MIC)
    self.layers = nn.ModuleList([nn.ModuleList([_MICBranch(d_model, input_len, output_len, s) for s in scales])
                                 for _ in range(n_layers)
                                 ])

    # Proyección final d_model→1
    self.head = nn.Conv1d(d_model, 1, kernel_size=1)

  def forward(self, Xs):
    B, C, L = Xs.shape
    assert C == self.num_features and L == self.input_len, \
        f"Expected Xs shape [B, {self.num_features}, {self.input_len}], got {Xs.shape}"

    # Extender con ceros para cubrir el futuro
    zeros = torch.zeros(B, self.num_features, self.output_len,
                        device=Xs.device, dtype=Xs.dtype)
    Xext = torch.cat([Xs, zeros], dim=-1)

    # Embedding
    Z = self.value_emb(Xext)

    # Capas MIC
    for branches in self.layers:
      outs = [br(Z) for br in branches]
      Z = torch.stack(outs, dim=0).mean(dim=0)

    # Proyección y recorte
    Yfull = self.head(Z)
    Yseasonal = Yfull[:, :, -self.output_len:]
    return Yseasonal

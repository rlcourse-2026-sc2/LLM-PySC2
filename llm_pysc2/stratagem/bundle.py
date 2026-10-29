# Copyright 2024, LLM-PySC2 Contributors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The task bundle `strat llm-pysc2` writes (format stratagemdsl.llm-pysc2-task.v1)."""

import json
import math
import os
from pathlib import Path

FORMAT = "stratagemdsl.llm-pysc2-task.v1"


class TaskBundle:

  def __init__(self, data: dict, path=None):
    if data.get("format") != FORMAT:
      raise ValueError(f"not a StratagemDSL LLM-PySC2 bundle (format {data.get('format')!r}, expected {FORMAT})")
    self.data = data
    self.path = Path(path).resolve() if path else None
    self.name = data["strategy"]
    self.map = data["map"]
    self.interface = data["interface"]
    self.races = data["races"]
    self.players = data["players"]
    self.objective = data.get("objective", {})
    self.forces = {f["name"]: f for f in data["forces"]}
    self.regions = {r["name"]: r for r in data["regions"]}
    self.plan = data["plan"]
    self.terrain = data.get("terrain", {})
    self.width, self.height = int(self.map["width"]), int(self.map["height"])
    self.minimap = int(self.interface["minimap"])
    self.screen = int(self.interface["screen"])
    self.camera_width = int(self.interface["camera_width"])
    self.raw_resolution = int(self.interface.get("raw_resolution", max(self.width, self.height)))
    self.scale = self.minimap / max(self.width, self.height)

  @classmethod
  def load(cls, path):
    with open(path, encoding="utf-8") as f:
      return cls(json.load(f), path)

  # ------------------------------------------------------------- files
  @property
  def map_path(self) -> Path:
    p = Path(self.map["path"])
    if not p.is_file() and self.path is not None:   # bundle moved together with its map
      q = self.path.parent / p.name
      if q.is_file():
        return q
    return p

  @property
  def source_path(self):
    src = self.data.get("source")
    if not src:
      return None
    p = Path(src)
    if not p.is_file() and self.path is not None and (self.path.parent / p.name).is_file():
      return self.path.parent / p.name
    return p

  # ------------------------------------------------------------- sides
  @property
  def controlled(self) -> list:
    return [n for n, f in self.forces.items() if f.get("controlled")]

  def side_forces(self, side: str) -> list:
    return [f for f in self.forces.values() if f.get("side") == side]

  # ------------------------------------------------------- coordinates
  # raw_units use raw_resolution = max(width, height), i.e. 1 raw pixel = 1 cell, y flipped and floored.
  def raw_to_world(self, rx, ry):
    return float(rx) + 0.5, self.height - float(ry) - 0.5

  def world_to_minimap(self, x, y):
    mx = min(self.minimap - 1, max(0, int(math.floor(x * self.scale))))
    my = min(self.minimap - 1, max(0, int(math.floor((self.height - y) * self.scale))))
    return [mx, my]

  def minimap_to_world(self, mx, my):
    return (mx + 0.5) / self.scale, self.height - (my + 0.5) / self.scale

  def region_of_world(self, x, y):
    out = []
    for name, r in self.regions.items():
      cx, cy = r["world"]
      if r.get("radius", 0) and math.hypot(x - cx, y - cy) <= r["radius"]:
        out.append(name)
    return out

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

"""What the bridge knows during an episode: forces, regions, events and plan progress.

StratagemDSL already has the pieces (it is a dependency of this package):

  stratagemdsl.play.observe.ForceTracker   which unit belongs to which force (owner, type, nearest spawn,
                                           capacity), region enter/leave events, the calibration check
  stratagemdsl.play.plantracker            the plan's Petri net replayed on what we observe

`StratagemRuntime.update(obs)` feeds them the pysc2 raw units of every step. The main agent asks it which
force (hence which LLM agent) a new unit belongs to; the stratagem observation translator asks it for the
situation and plan text.
"""

import math
import time

import numpy as np
from loguru import logger
from pysc2.lib import features, units

from llm_pysc2.stratagem.bundle import TaskBundle


def _unit_name(unit_type):
  try:
    return units.get_unit_type(int(unit_type)).name
  except Exception:
    return str(int(unit_type))


def _base_type(name):
  """Burrowed/sieged/morphed variants count as the unit the binding spawned."""
  for suffix in ("Burrowed", "Sieged", "Phasing", "SurveillanceMode", "OversightMode", "AG"):
    if name.endswith(suffix) and len(name) > len(suffix):
      return name[: -len(suffix)]
  return {"HellionTank": "Hellion", "VikingAssault": "VikingFighter", "SwarmHostBurrowedMP": "SwarmHostMP",
          "SupplyDepotLowered": "SupplyDepot", "WarpPrismPhasing": "WarpPrism", "ThorHighImpactMode": "Thor"}.get(name, name)


class StratagemRuntime:

  def __init__(self, bundle: TaskBundle, *, with_plan_tracker=True):
    from stratagemdsl.frontend import parse_file
    from stratagemdsl.packaging.terrain import load_profile
    from stratagemdsl.play.observe import ForceTracker
    from stratagemdsl.play.scenario import build_scenario
    self.bundle = bundle
    if bundle.source_path is None or not bundle.source_path.is_file():
      raise FileNotFoundError(f"the bundle's .strat source is missing: {bundle.source_path}")
    self.strategy = parse_file(bundle.source_path)
    base = bundle.map_path    # the packed map keeps the base map's terrain
    self.profile = load_profile(base)
    self.scenario = build_scenario(self.strategy, self.profile)
    self.ForceTracker = ForceTracker
    self.with_plan_tracker = with_plan_tracker
    self.reset()

  def reset(self):
    self.tracker = self.ForceTracker(self.scenario, self.bundle.players["ally"])
    self.plan = None
    if self.with_plan_tracker:
      from stratagemdsl.play.plantracker import PlanTracker
      self.plan = PlanTracker(self.strategy, self.scenario, self.tracker)
    self.game_loop = 0
    self.frames = 0
    self.minimap_checks = []
    self.started = time.monotonic()

  # --------------------------------------------------------------- update
  def frame_of(self, obs):
    from stratagemdsl.play.game import Frame, Unit
    out = []
    for u in obs.observation.raw_units:
      if u.alliance not in (features.PlayerRelative.SELF, features.PlayerRelative.ALLY, features.PlayerRelative.ENEMY):
        continue
      name = _base_type(_unit_name(u.unit_type))
      x, y = self.bundle.raw_to_world(u.x, u.y)
      health_ratio = float(u.health_ratio) / 255.0
      out.append(Unit(int(u.tag), name, int(u.owner), x, y, float(u.health), float(u.shield), health_ratio,
                      structure=False))
    player_id = int(obs.observation.player.player_id)
    return Frame(int(obs.observation.game_loop[0]) if np.ndim(obs.observation.game_loop) else
                 int(obs.observation.game_loop), out, player_id)

  def update(self, obs):
    frame = self.frame_of(obs)
    self.game_loop = frame.game_loop
    self.tracker.update(frame)
    if self.plan is not None:
      try:
        self.plan.update(frame)
      except Exception as e:  # the tracker is advisory: never stop the game for it
        logger.warning(f"plan tracker: {type(e).__name__}: {e}")
    self.frames += 1
    if self.frames <= 3:
      self._check_minimap(obs, frame)

  def _check_minimap(self, obs, frame):
    """Own units projected to minimap pixels vs the minimap's own player_relative layer."""
    try:
      pr = obs.observation.feature_minimap.player_relative
      ys, xs = np.nonzero(pr == features.PlayerRelative.SELF)
      own = [u for u in frame.units if u.owner == frame.player_id]
      if len(xs) == 0 or not own:
        return
      px = [self.bundle.world_to_minimap(u.x, u.y) for u in own]
      dx = float(np.mean([p[0] for p in px]) - xs.mean())
      dy = float(np.mean([p[1] for p in px]) - ys.mean())
      self.minimap_checks.append(round(math.hypot(dx, dy), 2))
      if math.hypot(dx, dy) > 3:
        logger.warning(f"stratagem: minimap projection is off by ({dx:.1f}, {dy:.1f}) px; "
                       f"the bundle's coordinates may not match this game")
    except Exception:
      pass

  # ----------------------------------------------------------- membership
  def force_of(self, tag):
    return self.tracker.force_of.get(int(tag))

  # ---------------------------------------------------------------- text
  def force_line(self, name, perspective_owner):
    f = self.scenario.forces[name]
    st = self.tracker.states[name]
    own = f.owner == perspective_owner
    if not st.alive:
      if not st.seen:
        return f"{name}: not seen yet" + (f" (expected near minimap {self.bundle.world_to_minimap(*f.spawn)})"
                                         if f.spawn else "")
      if own:
        return f"{name}: destroyed"
      secs = (self.game_loop - st.last_seen_loop) / 22.4
      return f"{name}: not visible; last seen at minimap {self.bundle.world_to_minimap(*st.last_seen)} {secs:.0f} s ago"
    counts = {}
    for u in st.alive:
      counts[u.unit_type] = counts.get(u.unit_type, 0) + 1
    kinds = ", ".join(f"{n} {t}" for t, n in sorted(counts.items()))
    x, y = st.centroid
    size = f"{len(st.alive)}/{st.initial_units} alive" if own else f"{len(st.alive)} visible"
    hp = f", HP+shields {100 * st.hp / st.initial_hp:.0f}%" if st.initial_hp else ""
    regions = ", ".join(sorted(st.regions)) or "none"
    plateau = self.profile.region_at(x, y) or "-"
    return (f"{name}: {size} ({kinds}){hp}, at minimap {self.bundle.world_to_minimap(x, y)} on {plateau}; "
            f"in regions: {regions}")

  def situation(self, perspective_owner=None):
    owner = perspective_owner or self.bundle.players["ally"]
    mm, ss = divmod(int(self.game_loop / 22.4), 60)
    lines = [f"Situation at {mm:02d}:{ss:02d} (all forces of the scenario, minimap coordinates):"]
    for title, side in (("Our forces and structures", "ally"), ("Enemy (only what we can see)", "enemy")):
      lines.append(f"  {title}:")
      for name, f in self.scenario.forces.items():
        if f.side == side:
          lines.append("    - " + self.force_line(name, owner))
    recent = self.tracker.events[-6:]
    if recent:
      lines.append("  Recent events:")
      for e in recent:
        mm, ss = divmod(int(e["loop"] / 22.4), 60)
        lines.append(f"    - {mm:02d}:{ss:02d} {e['force']} {e['event']} {e.get('region', '')}".rstrip())
    return "\n".join(lines)

  def plan_progress(self):
    return self.plan.describe() if self.plan is not None else ""

  def current_orders(self, force):
    if self.plan is None:
      return []
    return self.plan.orders_for(force)

  def expected_events(self, force):
    if self.plan is None:
      return []
    return self.plan.expected_events(force)

  # -------------------------------------------------------------- report
  def record(self):
    rec = {"events": self.tracker.events, "calibration": self.tracker.calibration,
           "calibration_warning": self.tracker.calibration_problem(), "minimap_check_px": self.minimap_checks,
           "final_state": self.tracker.summary()}
    if self.plan is not None:
      rec["plan_tracker"] = {"history": self.plan.history, "active": self.plan.active_phases()}
    return rec

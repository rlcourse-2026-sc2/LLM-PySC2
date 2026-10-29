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

"""A stand-in for the StarCraft II binary, at the s2client-protocol level.

`pysc2.env.sc2_env.SC2Env` talks to the game through a RunConfig (start the process) and a
RemoteController (create/join a game, observe, act, step). `FakeRunConfig` returns a `FakeController`
that answers those requests from `stratagemdsl.play.plansim.PlanSim`, so everything above the controller
is the real code path: SC2Env, pysc2 Features (feature layers, feature_units, raw_units, available
actions, transform_action), LLM-PySC2's MainAgent/LLMAgent (camera calibration, unit selection, control
groups, LLM queries, action translation).

The "game" behind it:
  * the map is the packed .SC2Map SC2Env sends (its terrain gives heights and ground paths);
  * the enemy is the plan's Petri net (the map script's token game) acting through PlanSim;
  * feature-layer actions are interpreted like the game does: screen/minimap points through the same
    camera transform pysc2 uses, point/rect selection, control groups, camera moves (minimap and the
    LLM-PySC2 world-space camera move), unit commands by ability id (attack a unit under the cursor or
    attack-move, move, hold, stop, burrow, siege/unsiege and other morphs, blink);
  * the observation has the feature layers LLM-PySC2 reads (height, visibility, camera, player_relative,
    unit_type, selected, hit points), raw units with fog of war, the UI panels and available abilities.

It is a test harness for the integration, not a game: combat, pathing and vision are simplified
(see PlanSim). Results on it say nothing about how an agent plays StarCraft II.
"""

import math

import numpy as np
from loguru import logger
from s2clientprotocol import common_pb2 as common
from s2clientprotocol import raw_pb2 as raw
from s2clientprotocol import sc2api_pb2 as sc
from s2clientprotocol import spatial_pb2
from s2clientprotocol import ui_pb2

from pysc2.lib import actions as pysc2_actions
from pysc2.lib import features, point, units

from llm_pysc2.lib.unit_actions import actions_for_unit, unit_type_id

SELF, ALLY, NEUTRAL, ENEMY = 1, 2, 3, 4
BASIC_ABILITIES = [(3674, True), (3794, True), (3793, False), (3665, False), (3795, True)]  # attack move hold stop patrol


def _type_id(name):
  for enum in (units.Protoss, units.Terran, units.Zerg, units.Neutral):
    try:
      return int(enum[name])
    except KeyError:
      continue
  return 0


def _race_of_type(type_id):
  name = str(units.get_unit_type(type_id)) if type_id else ""
  return name.split(".")[0].lower() if "." in name else ""


def _image(arr, bits):
  dtype = {8: np.uint8, 32: np.int32}[bits]
  img = common.ImageData(bits_per_pixel=bits, data=np.ascontiguousarray(arr.astype(dtype)).tobytes())
  img.size.x, img.size.y = arr.shape[1], arr.shape[0]
  return img


class FakeController:
  """The subset of pysc2.lib.remote_controller.RemoteController that SC2Env uses."""

  def __init__(self, runtime_factory):
    self._factory = runtime_factory
    self.sim = None
    self.status = sc.Status.launched
    self.options = None
    self.player_id = 1
    self.selected = []
    self.groups = {}
    self.camera = (0.0, 0.0)
    self.last_actions = []
    self.action_log = []
    self.ability_cache = {}

  # ------------------------------------------------------------ lifecycle
  @property
  def status_ended(self):
    return self.status == sc.Status.ended

  def ping(self):
    return sc.ResponsePing(game_version="fake-stratagem", data_version="", data_build=0, base_build=0)

  def available_maps(self):
    return sc.ResponseAvailableMaps()

  def save_map(self, map_path, map_data):
    return sc.ResponseSaveMap()

  def create_game(self, req_create_game):
    self.create = req_create_game
    self.status = sc.Status.init_game
    return sc.ResponseCreateGame()

  def join_game(self, req_join_game):
    self.options = req_join_game.options
    self.race = req_join_game.race
    self._new_game()
    return sc.ResponseJoinGame(player_id=self.player_id)

  def _new_game(self):
    self.sim, self.bundle = self._factory()
    if int(self.bundle.players["ally"]) != self.player_id:
      raise ValueError("the fake engine plays the bundle's allied side as player 1")
    W, H = self.bundle.width, self.bundle.height
    fl = self.options.feature_layer
    self.screen = (fl.resolution.x, fl.resolution.y)
    self.minimap = (fl.minimap_resolution.x, fl.minimap_resolution.y)
    self.cam_width = fl.width or 24
    aif = features.AgentInterfaceFormat(feature_dimensions=features.Dimensions(self.screen, self.minimap),
                                        camera_width_world_units=self.cam_width, use_feature_units=True,
                                        raw_resolution=point.Point(self.minimap[0], self.minimap[1]))
    self.tf = features.Features(agent_interface_format=aif, map_size=point.Point(W, H))
    self.sim.reset()
    own = [u for u in self.sim.units if u.owner == self.player_id]
    anchor = next((u for u in own if u.structure), own[0] if own else None)
    self.camera = (anchor.x, anchor.y) if anchor else (W / 2, H / 2)
    self.selected, self.groups, self.last_actions, self.action_log = [], {}, [], []
    self.status = sc.Status.in_game
    self._levels = np.array(self.sim.profile.level, dtype=np.int32)       # [y][x], y up
    logger.info(f"fake SC2: {self.bundle.name} on {self.bundle.map['name']} ({W}x{H}), "
                f"{len(self.sim.units)} units, camera at {self.camera}")

  def restart(self):
    self._new_game()
    return sc.ResponseRestartGame()

  def leave(self):
    return None

  def quit(self):
    self.status = sc.Status.quit

  def close(self):
    self.quit()

  def save_replay(self):
    return b""

  def data(self):
    return sc.ResponseData()

  def chat(self, message, channel=None):
    return None

  def game_info(self):
    W, H = self.bundle.width, self.bundle.height
    info = sc.ResponseGameInfo(map_name=self.bundle.map["name"], local_map_path=self.bundle.map["path"])
    info.options.CopyFrom(self.options)
    info.start_raw.map_size.x, info.start_raw.map_size.y = W, H
    l, b, r, t = self.bundle.map.get("bounds", [0, 0, W, H])
    info.start_raw.playable_area.p0.x, info.start_raw.playable_area.p0.y = int(l), int(b)
    info.start_raw.playable_area.p1.x, info.start_raw.playable_area.p1.y = int(r), int(t)
    height = np.flipud(np.clip((self._levels + 1) * 40, 0, 255))
    info.start_raw.terrain_height.CopyFrom(_image(height, 8))
    races = {"protoss": common.Protoss, "terran": common.Terran, "zerg": common.Zerg}
    p1 = info.player_info.add(player_id=1, type=sc.Participant, race_requested=self.race or
                              races[self.bundle.races["ally"]])
    p1.race_actual = p1.race_requested
    p2 = info.player_info.add(player_id=2, type=sc.Computer,
                              race_requested=races.get(self.bundle.races["enemy"], common.Random))
    p2.race_actual = p2.race_requested
    return info

  # ----------------------------------------------------------- transforms
  def _update_camera(self):
    self.tf._update_camera(point.Point(*self.camera))

  def _world_to_screen(self, x, y):
    p = self.tf._world_to_feature_screen_px.fwd_pt(point.Point(x, y))
    return p.x, p.y

  def _screen_to_world(self, sx, sy):
    p = self.tf._world_to_feature_screen_px.back_pt(point.Point(sx + 0.5, sy + 0.5))
    return p.x, p.y

  def _world_to_minimap(self, x, y):
    p = self.tf._world_to_minimap_px.fwd_pt(point.Point(x, y))
    return int(p.x), int(p.y)

  def _minimap_to_world(self, mx, my):
    p = self.tf._world_to_minimap_px.back_pt(point.Point(mx + 0.5, my + 0.5))
    return p.x, p.y

  def _px_per_cell(self):
    return self.screen[0] / self.cam_width

  def _on_screen(self, u):
    sx, sy = self._world_to_screen(u.x, u.y)
    return 0 <= sx < self.screen[0] and 0 <= sy < self.screen[1]

  def _clamp_camera(self):
    W, H = self.bundle.width, self.bundle.height
    half = self.cam_width / 2
    self.camera = (min(max(self.camera[0], half), W - half), min(max(self.camera[1], half), H - half))

  # -------------------------------------------------------------- actions
  def actions(self, req_action):
    for a in req_action.actions:
      self.act(a)
    return sc.ResponseAction(result=[1] * len(req_action.actions))

  def act(self, action):
    if action is None or self.sim is None:
      return
    self._update_camera()
    self.last_actions.append(action)
    if action.HasField("action_raw") and action.action_raw.HasField("camera_move"):
      c = action.action_raw.camera_move.center_world_space
      self.camera = (c.x, c.y)
      self._clamp_camera()
    if action.HasField("action_feature_layer"):
      fl = action.action_feature_layer
      if fl.HasField("camera_move"):
        m = fl.camera_move.center_minimap
        self.camera = self._minimap_to_world(m.x, m.y)
        self._clamp_camera()
      if fl.HasField("unit_selection_point"):
        self._select_point(fl.unit_selection_point)
      if fl.HasField("unit_selection_rect"):
        self._select_rect(fl.unit_selection_rect)
      if fl.HasField("unit_command"):
        self._command(fl.unit_command)
    if action.HasField("action_ui"):
      ui = action.action_ui
      if ui.HasField("control_group"):
        self._control_group(ui.control_group)
      if ui.HasField("select_army"):
        army = [u.tag for u in self._own() if not u.structure]
        self.selected = sorted(set(self.selected) | set(army)) if ui.select_army.selection_add else army

  def _own(self):
    return [u for u in self.sim.units if u.alive and u.owner == self.player_id]

  def _unit_at(self, sx, sy, candidates):
    best, bd = None, None
    for u in candidates:
      ux, uy = self._world_to_screen(u.x, u.y)
      d = math.hypot(ux - sx, uy - sy)
      if d <= u.radius * self._px_per_cell() + 3 and (bd is None or d < bd):
        best, bd = u, d
    return best

  def _select_point(self, sel):
    sx, sy = sel.selection_screen_coord.x, sel.selection_screen_coord.y
    vis = self.sim.visible_tags(self.player_id)
    on = [u for u in self.sim.units if u.alive and u.tag in vis and self._on_screen(u)]
    u = self._unit_at(sx, sy, [v for v in on if v.owner == self.player_id]) or self._unit_at(sx, sy, on)
    t = sel.type
    if u is None:
      if t == spatial_pb2.ActionSpatialUnitSelectionPoint.Select:
        self.selected = []
      return
    if t == spatial_pb2.ActionSpatialUnitSelectionPoint.Select:
      self.selected = [u.tag]
    elif t == spatial_pb2.ActionSpatialUnitSelectionPoint.Toggle:
      self.selected = [x for x in self.selected if x != u.tag] if u.tag in self.selected else self.selected + [u.tag]
    else:
      same = [v.tag for v in on if v.owner == u.owner and v.unit_type == u.unit_type]
      if t == spatial_pb2.ActionSpatialUnitSelectionPoint.AllType:
        self.selected = same
      else:
        self.selected = sorted(set(self.selected) | set(same))

  def _select_rect(self, sel):
    picked = []
    own_on = [u for u in self._own() if self._on_screen(u)]
    for r in sel.selection_screen_coord:
      x0, x1 = sorted((r.p0.x, r.p1.x))
      y0, y1 = sorted((r.p0.y, r.p1.y))
      for u in own_on:
        sx, sy = self._world_to_screen(u.x, u.y)
        pad = u.radius * self._px_per_cell()
        if x0 - pad <= sx <= x1 + pad and y0 - pad <= sy <= y1 + pad:
          picked.append(u)
    if any(not u.structure for u in picked):        # a box selects units before structures
      picked = [u for u in picked if not u.structure]
    tags = [u.tag for u in picked]
    self.selected = sorted(set(self.selected) | set(tags)) if sel.selection_add else tags

  def _control_group(self, cg):
    idx, act = cg.control_group_index, cg.action
    alive = {u.tag for u in self._own()}
    group = [t for t in self.groups.get(idx, []) if t in alive]
    A = ui_pb2.ActionControlGroup
    if act == A.Recall:
      if group:
        self.selected = list(group)
      return
    if act in (A.SetAndSteal, A.AppendAndSteal):
      for k in self.groups:
        self.groups[k] = [t for t in self.groups[k] if t not in self.selected]
    if act in (A.Set, A.SetAndSteal):
      self.groups[idx] = list(self.selected)
    elif act in (A.Append, A.AppendAndSteal):
      self.groups[idx] = group + [t for t in self.selected if t not in group]

  def _command(self, cmd):
    from stratagemdsl.play.game import Order
    tags = [t for t in self.selected if t in self.sim.by_tag and self.sim.by_tag[t].owner == self.player_id]
    if not tags:
      return
    ability = cmd.ability_id
    queued = bool(cmd.queue_command)
    pt, target = None, None
    if cmd.HasField("target_screen_coord"):
      sx, sy = cmd.target_screen_coord.x, cmd.target_screen_coord.y
      pt = self._screen_to_world(sx, sy)
      vis = self.sim.visible_tags(self.player_id)
      target = self._unit_at(sx, sy, [u for u in self.sim.units if u.alive and u.tag in vis
                                       and u.owner not in (self.player_id, 0) and self._on_screen(u)])
    elif cmd.HasField("target_minimap_coord"):
      pt = self._minimap_to_world(cmd.target_minimap_coord.x, cmd.target_minimap_coord.y)
    meta = {"queued": queued, "ability_id": ability}
    if ability in (3674, 1, 3795):                       # attack, smart, patrol
      if target is not None:
        order = Order("attack_unit", tags, target_tag=target.tag, meta=meta)
      elif ability == 1 and pt is not None:
        order = Order("move", tags, point=pt, meta=meta)
      else:
        order = Order("attack_pt", tags, point=pt, meta=meta)
    elif ability == 3794:
      order = Order("move", tags, point=pt, meta=meta)
    elif ability == 3793:
      order = Order("hold", tags, meta=meta)
    elif ability in (3665, 2057):
      order = Order("stop", tags, meta=meta)
    else:
      funcs = pysc2_actions.ABILITY_IDS.get(ability, [])
      name = funcs and sorted(funcs, key=lambda f: int(f.id))[0].name or str(ability)
      meta["ability"] = name
      order = Order("ability", tags, point=pt, target_tag=target.tag if target else None, meta=meta)
    self.sim.issue([order], self.player_id)
    self.action_log.append({"loop": self.sim.loop, "order": order.kind, "ability": ability, "units": len(tags),
                            "point": [round(v, 1) for v in pt] if pt else None,
                            "target": hex(target.tag) if target else None})

  # ----------------------------------------------------------------- time
  def step(self, count=1):
    if self.sim is None or self.status_ended:
      return sc.ResponseStep()
    left = int(count)
    while left > 0 and not self.sim.done:
      n = min(8, left)
      self.sim.advance(n)
      left -= n
    if left > 0:
      self.sim.loop += left
    if self.sim.outcome:
      self.status = sc.Status.ended
    return sc.ResponseStep()

  # ---------------------------------------------------------- observation
  def _abilities(self):
    out = {}
    for tag in self.selected:
      u = self.sim.by_tag.get(tag)
      if u is None or u.owner != self.player_id:
        continue
      key = u.unit_type
      if key not in self.ability_cache:
        abil = {}
        race = _race_of_type(_type_id(u.unit_type))
        tid = unit_type_id(race, u.unit_type) if race else None
        acts = actions_for_unit(race, tid) if tid is not None else []
        for a in acts:
          for fid, func, _args in a['func']:
            f = pysc2_actions.FUNCTIONS[fid]
            if f.ability_id:
              ft = f.function_type.__name__
              abil.setdefault(f.ability_id, ft in ("cmd_screen", "cmd_minimap"))
        if not u.structure and u.stats.speed > 0:
          for aid, needs_point in BASIC_ABILITIES:
            abil.setdefault(aid, needs_point)
        self.ability_cache[key] = abil
      for aid, needs_point in self.ability_cache[key].items():
        out[aid] = needs_point
    return out

  def _unit_proto(self, u, alliance, display, selected, on_screen):
    p = raw.Unit(display_type=display, alliance=alliance, tag=u.tag, unit_type=_type_id(u.unit_type),
                 owner=u.owner, facing=u.facing, radius=u.radius, build_progress=1.0,
                 cloak=raw.NotCloaked, is_selected=selected, is_on_screen=on_screen, is_powered=True,
                 health=max(0.0, u.hp), health_max=u.stats.hp, shield=max(0.0, u.shield),
                 shield_max=u.stats.shield, energy=u.energy, energy_max=200.0 if u.stats.energy else 0.0,
                 is_flying=u.air, is_burrowed=u.burrowed, weapon_cooldown=u.weapon_cooldown * 22.4)
    p.pos.x, p.pos.y, p.pos.z = u.x, u.y, 10.0 + (3.0 if u.air else 0.0)
    if alliance == SELF and u.order is not None:
      aid = {"move": 3794, "attack_pt": 3674, "attack_unit": 3674, "attack_group": 3674, "hold": 3793}.get(u.order.kind)
      if aid:
        o = p.orders.add(ability_id=aid)
        if u.order.point:
          o.target_world_space_pos.x, o.target_world_space_pos.y = u.order.point
    if u.target is not None:
      p.engaged_target_tag = u.target
    return p

  def _disc(self, layer, cx, cy, r, value):
    h, w = layer.shape
    x0, x1 = max(0, int(cx - r)), min(w, int(cx + r) + 1)
    y0, y1 = max(0, int(cy - r)), min(h, int(cy + r) + 1)
    if x0 >= x1 or y0 >= y1:
      return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    m = (xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2 <= max(r, 0.6) ** 2
    layer[y0:y1, x0:x1][m] = value

  def observe(self, target_game_loop=0, disable_fog=False):
    sim = self.sim
    self._update_camera()
    obs = sc.ResponseObservation()
    o = obs.observation
    o.game_loop = sim.loop
    alive = [u for u in sim.units if u.alive]
    own = [u for u in alive if u.owner == self.player_id]
    vis = sim.visible_tags(self.player_id)
    seen = sim.seen_structures.setdefault(self.player_id, set())
    self.selected = [t for t in self.selected if t in sim.by_tag]
    selected = set(self.selected)

    # player
    pc = o.player_common
    pc.player_id = self.player_id
    army = [u for u in own if not u.structure]
    pc.food_used = pc.food_army = len(army)
    pc.food_cap = 200
    pc.army_count = len(army)
    pc.larva_count = sum(1 for u in own if u.unit_type == "Larva")
    pc.warp_gate_count = sum(1 for u in own if u.unit_type == "WarpGate")

    # raw units (fog: visible enemies; enemy structures once seen stay as snapshots)
    shown = []
    for u in alive:
      if u.owner == self.player_id:
        shown.append((u, SELF, raw.Visible))
      elif u.tag in vis:
        if u.structure:
          seen.add(u.tag)
        shown.append((u, ENEMY if u.owner in (1, 2) else NEUTRAL, raw.Visible))
      elif u.structure and u.tag in seen:
        shown.append((u, ENEMY, raw.Snapshot))
    for u, alliance, display in shown:
      on = self._on_screen(u)
      o.raw_data.units.append(self._unit_proto(u, alliance, display, u.tag in selected, on))
    o.raw_data.player.camera.x, o.raw_data.player.camera.y = self.camera

    # abilities of the selection
    for aid, needs_point in sorted(self._abilities().items()):
      o.abilities.add(ability_id=aid, requires_point=needs_point)

    # ui
    for idx, tags in sorted(self.groups.items()):
      members = [sim.by_tag[t] for t in tags if t in sim.by_tag]
      if members:
        o.ui_data.groups.add(control_group_index=idx, leader_unit_type=_type_id(members[0].unit_type),
                             count=len(members))
    sel_units = [sim.by_tag[t] for t in self.selected if t in sim.by_tag]

    def info(u):
      return ui_pb2.UnitInfo(unit_type=_type_id(u.unit_type), player_relative=SELF if u.owner == self.player_id
                             else ENEMY, health=int(max(0, u.hp)), shields=int(max(0, u.shield)),
                             energy=int(u.energy), build_progress=1.0, max_health=int(u.stats.hp),
                             max_shields=int(u.stats.shield))
    if len(sel_units) == 1:
      o.ui_data.single.unit.CopyFrom(info(sel_units[0]))
    elif len(sel_units) > 1:
      for u in sel_units:
        o.ui_data.multi.units.add().CopyFrom(info(u))

    # feature layers
    sw, sh = self.screen
    mw, mh = self.minimap
    W, H = self.bundle.width, self.bundle.height
    # minimap
    m_height = np.zeros((mh, mw), np.int32)
    lv = self._levels
    for my in range(mh):
      for mx in range(mw):
        wx, wy = self._minimap_to_world(mx, my)
        i, j = int(wx), int(wy)
        if 0 <= i < W and 0 <= j < H:
          m_height[my, mx] = max(0, lv[j, i] + 1) * 40
    m_vis = np.zeros((mh, mw), np.int32)
    m_pr = np.zeros((mh, mw), np.int32)
    m_pid = np.zeros((mh, mw), np.int32)
    m_sel = np.zeros((mh, mw), np.int32)
    m_type = np.zeros((mh, mw), np.int32)
    m_cam = np.zeros((mh, mw), np.int32)
    scale = mw / max(W, H)
    for u in own:
      mx, my = self._world_to_minimap(u.x, u.y)
      self._disc(m_vis, mx + 0.5, my + 0.5, u.stats.sight * scale, 2)
    for u, alliance, display in shown:
      mx, my = self._world_to_minimap(u.x, u.y)
      if 0 <= mx < mw and 0 <= my < mh:
        m_pr[my, mx] = alliance
        m_pid[my, mx] = u.owner
        m_type[my, mx] = _type_id(u.unit_type)
        if u.tag in selected:
          m_sel[my, mx] = 1
    half = self.cam_width / 2
    c0 = self._world_to_minimap(self.camera[0] - half, self.camera[1] + half)
    c1 = self._world_to_minimap(self.camera[0] + half, self.camera[1] - half)
    m_cam[max(0, c0[1]):min(mh, c1[1] + 1), max(0, c0[0]):min(mw, c1[0] + 1)] = 1
    mm = o.feature_layer_data.minimap_renders
    mm.height_map.CopyFrom(_image(m_height, 8))
    mm.visibility_map.CopyFrom(_image(m_vis, 8))
    mm.camera.CopyFrom(_image(m_cam, 8))
    mm.player_id.CopyFrom(_image(m_pid, 8))
    mm.player_relative.CopyFrom(_image(m_pr, 8))
    mm.selected.CopyFrom(_image(m_sel, 8))
    mm.unit_type.CopyFrom(_image(m_type, 32))
    # screen
    s_height = np.zeros((sh, sw), np.int32)
    ppc = self._px_per_cell()
    cx0, cy1 = self.camera[0] - half, self.camera[1] + half
    for sy in range(0, sh, 4):
      for sx in range(0, sw, 4):
        i, j = int(cx0 + (sx + 2) / ppc), int(cy1 - (sy + 2) / ppc)
        v = (lv[j, i] + 1) * 40 if 0 <= i < W and 0 <= j < H else 0
        s_height[sy:sy + 4, sx:sx + 4] = max(0, v)
    s_vis = np.full((sh, sw), 1, np.int32)
    s_pr = np.zeros((sh, sw), np.int32)
    s_pid = np.zeros((sh, sw), np.int32)
    s_type = np.zeros((sh, sw), np.int32)
    s_sel = np.zeros((sh, sw), np.int32)
    s_hp = np.zeros((sh, sw), np.int32)
    for u in own:
      sx, sy = self._world_to_screen(u.x, u.y)
      self._disc(s_vis, sx, sy, u.stats.sight * ppc, 2)
    for u, alliance, display in shown:
      if not self._on_screen(u):
        continue
      sx, sy = self._world_to_screen(u.x, u.y)
      r = u.radius * ppc
      self._disc(s_pr, sx, sy, r, alliance)
      self._disc(s_pid, sx, sy, r, u.owner)
      self._disc(s_type, sx, sy, r, _type_id(u.unit_type))
      self._disc(s_hp, sx, sy, r, int(max(0, u.hp)))
      if u.tag in selected:
        self._disc(s_sel, sx, sy, r, 1)
    sr = o.feature_layer_data.renders
    sr.height_map.CopyFrom(_image(s_height, 8))
    sr.visibility_map.CopyFrom(_image(s_vis, 8))
    sr.player_relative.CopyFrom(_image(s_pr, 8))
    sr.player_id.CopyFrom(_image(s_pid, 8))
    sr.unit_type.CopyFrom(_image(s_type, 32))
    sr.selected.CopyFrom(_image(s_sel, 8))
    sr.unit_hit_points.CopyFrom(_image(s_hp, 32))

    # result
    if sim.outcome:
      self.status = sc.Status.ended
      mine = sc.Victory if sim.outcome == "victory" else sc.Defeat
      other = sc.Defeat if mine == sc.Victory else sc.Victory
      obs.player_result.add(player_id=1, result=mine)
      obs.player_result.add(player_id=2, result=other)
    for a in self.last_actions:   # the game echoes interface actions; raw camera moves are not reported
      if a.HasField("action_feature_layer") or a.HasField("action_ui"):
        echo = obs.actions.add()
        if a.HasField("action_feature_layer"):
          echo.action_feature_layer.CopyFrom(a.action_feature_layer)
        if a.HasField("action_ui"):
          echo.action_ui.CopyFrom(a.action_ui)
    self.last_actions = []
    return obs


class FakeProcess:

  def __init__(self, controller):
    self.controller = controller

  def close(self):
    self.controller.quit()


class FakeRunConfig:
  """Stands in for pysc2.run_configs.get(): start() returns a FakeProcess."""

  def __init__(self, runtime_factory):
    self._factory = runtime_factory
    self.version = None
    self.data_dir = ""
    self.replay_dir = ""
    self.controllers = []

  def start(self, want_rgb=False, **kwargs):
    c = FakeController(self._factory)
    self.controllers.append(c)
    return FakeProcess(c)

  def map_data(self, map_name, players=None):
    with open(map_name, "rb") as f:
      return f.read()

  def save_replay(self, replay_data, replay_dir, prefix=None):
    return ""

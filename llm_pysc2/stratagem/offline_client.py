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

"""model_name='offline': a scripted stand-in for the LLM that follows the plan.

It answers the same prompt an LLM gets, in the same text format, so the whole LLM-PySC2 path (observation
text, action parsing, unit selection, camera, pysc2 calls) runs without an API key. Its policy: take the
plan's current order for the team's force (from the bridge's plan tracker; the first order of the force
before anything is known), attack a visible unit of the target if there is one, otherwise move there by
minimap. It is a test double and a "follow the plan literally" baseline, not a language model.
"""

import re
import time

from loguru import logger

from llm_pysc2.lib import llm_client
from llm_pysc2.lib.llm_client import GptClient

ORDER = re.compile(r"^\s*(\w+)\(\s*(\w+)\s*(?:,\s*(\w+))?")
TEAM = re.compile(r"^Team (\S+) Info:")
MOVEMENT = {"move", "retreat", "attack", "retarget", "hold"}
UNIT = re.compile(r"Unit: (\w+)\s+Tag: (0x[0-9a-fA-F]+)(?:.*?Distance: (\d+))?")


def parse_blocks(text):
  """{team name: [(unit type, tag, distance)] of nearby enemy units}"""
  blocks, team, section = {}, None, None
  for line in text.splitlines():
    s = line.strip()
    m = TEAM.match(s)
    if m:
      team, section = m.group(1), None
      blocks[team] = []
      continue
    if s.startswith("Valid Actions") or s.startswith("Relevant Knowledge"):
      team = None
    if team is None:
      continue
    if s.startswith("Nearby Enemy Units"):
      section = "enemy"
    elif s.startswith("Controlled Team Units") or s.startswith("Nearby Ally Units"):
      section = "other"
    elif section == "enemy":
      u = UNIT.search(s)
      if u:
        blocks[team].append((u.group(1), u.group(2), int(u.group(3)) if u.group(3) else 99))
  return blocks


class OfflinePlanClient(GptClient):

  def __init__(self, name, log_id, config):
    super(OfflinePlanClient, self).__init__(name, log_id, config)
    self.last = {}
    logger.info(f"[ID {self.log_id}] {self.agent_name} offline plan client initialized (no LLM)")

  def _force_of_team(self, team):
    for force in self.config.force_of_agent.get(self.agent_name, []):
      if team.startswith(force + "-"):
        return force
    return None

  def _order(self, force):
    """The latest movement order of the plan for this force (cast/tag/... are not movement)."""
    rt = self.config.stratagem_runtime
    now = [o for o in (rt.current_orders(force) if rt is not None else []) if o.split("(")[0] in MOVEMENT]
    if now:
      return now[-1]
    # no order: do what the plan waits for, e.g. on enter(force, zone) -> go to zone
    for event in (rt.expected_events(force) if rt is not None else []):
      m = ORDER.match(event)
      if m and m.group(1) == "enter" and m.group(3):
        return f"move({force}, {m.group(3)})"
    if rt is not None and rt.plan is not None and rt.plan.history[1:]:
      return None          # the plan has moved on and has nothing for this force
    steps = [s for s in self.config.bundle.plan.get("force_plans", {}).get(force, []) if s["action"] in MOVEMENT]
    return steps[0]["order"] if steps else None

  def _target_minimap(self, target):
    b = self.config.bundle
    if target in b.regions:
      return b.regions[target]["minimap"]
    rt = self.config.stratagem_runtime
    if rt is not None and target in rt.scenario.forces:
      pos = rt.tracker.position(target)
      if pos is not None:
        return b.world_to_minimap(*pos)
    f = b.forces.get(target)
    if f and f.get("spawn"):
      return f["spawn"]["minimap"]
    return None

  def decide(self, team, enemies):
    force = self._force_of_team(team)
    order = self._order(force) if force else None
    if not order:
      return ["<No_Operation()>"], "no order in the plan"
    m = ORDER.match(order)
    if not m:
      return ["<No_Operation()>"], f"cannot read {order}"
    action, _actor, target = m.groups()
    if action == "hold":
      return ["<Hold_Position()>"], order
    want = set()
    if target and target in self.config.bundle.forces:
      want = set(self.config.bundle.forces[target].get("unit_types", []))
    if action in ("attack", "retarget") and enemies:
      preferred = [e for e in enemies if e[0] in want] or enemies
      kind, tag, _ = min(preferred, key=lambda e: e[2])
      return [f"<Attack_Unit({tag})>"], f"{order}: attack the {kind} in sight"
    mm = self._target_minimap(target) if target else None
    if mm is None:
      return ["<No_Operation()>"], f"{order}: no position for {target}"
    return [f"<Move_Minimap([{mm[0]}, {mm[1]}])>"], f"{order}: go to minimap {mm}"

  def query(self, obs_prompt, base64_image=None):
    t0 = time.time()
    self.wrap_message(obs_prompt, base64_image)
    blocks = parse_blocks(obs_prompt)
    analysis, actions = [], []
    for team, enemies in blocks.items():
      acts, why = self.decide(team, enemies)
      analysis.append(f"{team}: {why}")
      actions.append(f"  Team {team}:\n" + "\n".join(f"    {a}" for a in acts))
    answer = "Analysis:\n  " + "\n  ".join(analysis or ["no team observed"]) + "\nActions:\n" + "\n".join(actions)
    self.num_query += 1
    self.query_time = time.time() - t0
    self.query_token_in = len(obs_prompt) // 4
    self.query_token_out = len(answer) // 4
    self.total_query_time += self.query_time
    self.total_query_token_in += self.query_token_in
    self.total_query_token_out += self.query_token_out
    self.ave_query_time = self.total_query_time / self.num_query
    self.ave_query_token_in = self.total_query_token_in / self.num_query
    self.ave_query_token_out = self.total_query_token_out / self.num_query
    return answer


llm_client.FACTORY['offline'] = OfflinePlanClient
llm_client.FACTORY['stratagem-offline'] = OfflinePlanClient

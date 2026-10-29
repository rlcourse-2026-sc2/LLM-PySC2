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

"""An AgentConfig generated from a StratagemDSL task bundle, for any race.

Layouts
  per-force (default)  one LLM agent per allied force the plan commands ("CombatGroup-<force>"), so a
                       bait and a strike force are separate commanders, as in the stratagem
  single               one LLM agent commanding every allied force (one team per force and unit type)

Each agent gets one team per unit type of its force (with burrowed/sieged/morphed variants), held in its own
control group, and the action space of that unit type for the bundle's race (llm_pysc2.lib.unit_actions,
which includes the Terran/Zerg actions of llm_action.py).

Conditions (as in `strat play`)
  llm       the agent knows the objective, the map, the named regions and the situation
  intents   additionally the plan: its own orders per phase, and the phases the bridge believes active
"""

from loguru import logger

from llm_pysc2.agents.configs.config import AgentConfig
from llm_pysc2.lib.unit_actions import actions_for_unit, morph_family, unit_type_id
from llm_pysc2.stratagem.bundle import TaskBundle

CONDITIONS = ("llm", "intents")
LAYOUTS = ("per-force", "single")
MAX_CONTROL_GROUPS = 10


def _composition_text(force):
  comp = force.get("composition") or [[t, None] for t in force.get("unit_types", [])]
  return ", ".join(f"{n} {t}" if n else t for t, n in comp)


def force_mission(bundle: TaskBundle, force_name: str, condition: str) -> str:
  """The standing task of one allied force, in LLM-PySC2's team['task'] 'info' text."""
  f = bundle.forces[force_name]
  lines = [f"You command '{force_name}' ({_composition_text(f)}), role '{f.get('role') or '-'}', in the "
           f"stratagem '{bundle.name}'. Win: {bundle.objective.get('success', '?')}. "
           f"Lose: {bundle.objective.get('failure', '?')}."]
  if condition == "intents":
    steps = bundle.plan.get("force_plans", {}).get(force_name, [])
    if steps:
      lines.append("Your orders in the plan:")
      for s in steps:
        where = f" (minimap {s['target_minimap']})" if s.get("target_minimap") else ""
        lines.append(f"  - phase {s['phase']}: {s['order']}{where}; starts {s['starts']}")
  return "\n".join(lines)


class StratagemAgentConfig(AgentConfig):

  def __init__(self, bundle: TaskBundle, *, condition="intents", layout="per-force", model_name=None,
               api_base=None, api_key=None, temperature=None, communication=False):
    super(StratagemAgentConfig, self).__init__()
    if condition not in CONDITIONS:
      raise ValueError(f"condition must be one of {CONDITIONS}")
    if layout not in LAYOUTS:
      raise ValueError(f"layout must be one of {LAYOUTS}")
    self.bundle = bundle
    self.condition = condition
    self.layout = layout
    self.race = bundle.races["ally"]
    if self.race not in ("protoss", "terran", "zerg"):
      raise ValueError(f"the allied race of {bundle.name} is {self.race!r}; LLM-PySC2 needs a concrete race")
    if model_name:
      self.model_name = model_name
    if api_base:
      self.api_base = api_base
    if api_key:
      self.api_key = api_key
    if temperature is not None:
      self.temperature = temperature
    self.basic_prompt = 'stratagem'
    self.translator_o = 'stratagem'
    self.translator_a = 'default'
    self.communicator = 'default'

    self.ENABLE_INIT_STEPS = False
    self.ENABLE_AUTO_WORKER_MANAGE = False
    self.ENABLE_AUTO_WORKER_TRAINING = False
    self.ENABLE_COMMUNICATION = bool(communication)
    self.MAX_LLM_DECISION_FREQUENCY = 1
    self.MAX_NUM_ACTIONS = 3
    self.stratagem_runtime = None       # set by StratagemMainAgent

    self.AGENTS_ALWAYS_DISABLE = []
    self.AGENTS = {}
    groups = iter(range(1, MAX_CONTROL_GROUPS))
    forces = bundle.controlled
    if layout == "per-force":
      for force in forces:
        name = f"CombatGroup-{force}"
        self.AGENTS[name] = self._agent_entry(name, [force], groups)
    elif forces:
      self.AGENTS["CombatGroup-all"] = self._agent_entry("CombatGroup-all", forces, groups)
    self.force_of_agent = {}
    for agent_name, entry in self.AGENTS.items():
      for team in entry['team']:
        self.force_of_agent.setdefault(agent_name, [])
        if team['force'] not in self.force_of_agent[agent_name]:
          self.force_of_agent[agent_name].append(team['force'])

  def _agent_entry(self, name, forces, groups):
    teams, action = [], {}
    describe = []
    for force in forces:
      f = self.bundle.forces[force]
      comp = f.get("composition") or [[t, 0] for t in f.get("unit_types", [])]
      describe.append(f"'{force}' ({_composition_text(f)}, role {f.get('role') or '-'})")
      seen = set()
      for unit_type, _n in comp:
        if unit_type in seen:          # one team per unit type, even if the binding lists it twice
          continue
        seen.add(unit_type)
        family = morph_family(self.race, unit_type)
        if not family:
          logger.warning(f"stratagem config: unknown unit type {unit_type} in {force}")
          continue
        group = next(groups, None)
        teams.append({'name': f"{force}-{unit_type}", 'force': force, 'unit_type': family,
                      'game_group': group if group is not None else -1,
                      'select_type': 'group' if group is not None else 'select_all_type',
                      'task': [{'time': None, 'pos': None, 'info': force_mission(self.bundle, force, self.condition)}]})
        for t in family:
          action[t] = actions_for_unit(self.race, t)
    return {
      'describe': f"{self.race.capitalize()} commander of {' and '.join(describe)} in the StarCraft II stratagem "
                  f"scenario '{self.bundle.name}'",
      'llm': {
        'basic_prompt': self.basic_prompt,
        'translator_o': self.translator_o,
        'translator_a': self.translator_a,
        'img_fea': self.ENABLE_IMAGE_FEATURE,
        'img_rgb': self.ENABLE_IMAGE_RGB,
        'model_name': self.model_name,
        'api_base': self.api_base,
        'api_key': self.api_key,
      },
      'team': teams,
      'action': action,
    }

  def auto_check(self, log_id):
    if self.model_name in ('offline', 'stratagem-offline'):
      return            # the offline planner needs no key and no waiting
    super(StratagemAgentConfig, self).auto_check(log_id)

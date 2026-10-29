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

"""Prompt ('stratagem') and observation translator ('stratagem') for StratagemDSL scenarios.

Both keep LLM-PySC2's text interface -- "Team <name>:" blocks of <Action(args)> -- and add what a stratagem
needs: the objective, named regions and terrain in minimap pixels, the situation of every force (from the
bridge's ForceTracker), and with the `intents` condition the plan and its estimated progress.
They are registered for all three races under the key 'stratagem'.
"""

from llm_pysc2.lib import llm_observation, llm_prompt
from llm_pysc2.lib.llm_observation import (BaseTranslatorO, get_game_info, get_last_action_info,
                                           get_teams_info_with_knowledge, get_valid_actions_from_obs)
from llm_pysc2.lib.llm_prompt import BasePrompt


def regions_text(bundle):
  lines = []
  for name, r in sorted(bundle.regions.items()):
    role = f" ({r['role']})" if r.get("role") else ""
    lines.append(f"  - {name}{role}: minimap {r['minimap']}, radius {r['minimap_radius']} px")
  return "\n".join(lines) or "  (none)"


def forces_text(bundle):
  lines = []
  for name, f in bundle.forces.items():
    comp = ", ".join(f"{n} {t}" for t, n in f.get("composition", [])) or "/".join(f.get("unit_types", []))
    where = f" starts near minimap {f['spawn']['minimap']}" if f.get("spawn") else ""
    who = "ours, commanded by agents" if f.get("controlled") else ("ours" if f.get("side") == "ally" else "enemy")
    lines.append(f"  - {name} ({who}, {f['kind']}, {comp}, role {f.get('role') or '-'}){where}")
  return "\n".join(lines)


class StratagemPrompt(BasePrompt):

  def __init__(self, name, log_id, config):
    super(StratagemPrompt, self).__init__()
    self.name = name
    self.config = config
    self.log_id = log_id
    b = config.bundle
    forces = config.force_of_agent.get(name, [])
    plan = ""
    if config.condition == "intents":
      plan = "\n5.The plan (a verified stratagem; follow it unless the situation demands otherwise)\n" + \
             "\n".join("  " + line for line in b.plan.get("brief", "").splitlines())
    self.sp = f"""
1.Identity
  You are a {config.AGENTS[name]['describe']}.
  You command {', '.join(forces) or 'your troops'} for the {b.races['ally']} side (player {b.players['ally']}); the
  {b.races['enemy']} enemy is commanded by the map's script. Other allied forces may have their own commanders.

2.Objective
  You win when: {b.objective.get('success', '?')}
  You lose when: {b.objective.get('failure', '?')}

3.Map ({b.width} x {b.height} cells; the minimap is {b.minimap} x {b.minimap} pixels, x right, y DOWN)
  Named places:
{regions_text(b)}
  Forces:
{forces_text(b)}
{chr(10).join('  ' + line for line in b.terrain.get('minimap', '').splitlines())}

4.Rules
  4.1 Use <Move_Minimap([x, y])> with minimap pixels to go to a named place; screen coordinates only for things
      on your screen. A move does not stop to fight; Attack_Unit targets a unit you can see by its tag.
  4.2 Concentrate fire, keep units alive, and do what the objective needs; units fight back automatically.
  4.3 Orders persist until replaced: when a team should keep doing what it does, give <No_Operation()>.
{plan}

6.Action Output
  Give analysis and then actions for each of your teams, in this form:

  Analysis:
    xxxxx
  Actions:
    Team <team name>:
      <Action(args)>
"""
    self.eip = """
Game Info:
	Time: 0:10

Team bait-Zergling Info:
	Team minimap position: [20, 40]
	Controlled Team Units:
		Unit: Zergling    Tag: 0x100040001    ScreenPos: [64, 64]    Health: 35(100 %)    Weapon Ready

Valid Actions:
	Team bait-Zergling Valid Actions:
		<Stop()>
		<No_Operation()>
		<Hold_Position()>
		<Move_Minimap(minimap)>
		<Move_Screen(screen)>
		<Attack_Unit(tag)>

Stratagem:
	Your orders in the plan: phase lure: move(bait, lure_zone) (minimap [46, 18])
"""
    self.eop = """
Analysis:
  The bait has to show itself at the lure zone; nothing is in sight yet, so it moves there now.
Actions:
  Team bait-Zergling:
    <Move_Minimap([46, 18])>
"""
    self.eip += f"\nGive each team no more than {config.MAX_NUM_ACTIONS} actions.\nNow, start generating your analysis and actions:\n"


class StratagemTranslatorO(BaseTranslatorO):

  def __init__(self, name, log_id, config):
    super(StratagemTranslatorO, self).__init__()
    self.agent_name = name
    self.log_id = log_id
    self.config = config

  def translate(self, agent) -> str:
    obs_list = agent.team_unit_obs_list
    if not isinstance(obs_list, list) or len(obs_list) < 1:
      return "obs_list error, no obs found"
    obs = obs_list[0]
    text = get_game_info(obs, agent) + get_teams_info_with_knowledge(agent) + get_valid_actions_from_obs(obs, agent)
    text += get_last_action_info(agent)
    rt = self.config.stratagem_runtime
    if rt is not None:
      text += "\n\nStratagem:\n" + "\n".join("\t" + line for line in rt.situation().splitlines())
      if self.config.condition == "intents":
        for force in self.config.force_of_agent.get(self.agent_name, []):
          steps = self.config.bundle.plan.get("force_plans", {}).get(force, [])
          now = rt.current_orders(force)
          waits = rt.expected_events(force)
          text += f"\n\tYour force {force}:"
          text += f"\n\t\tplan orders now (estimate): {'; '.join(now) if now else 'none'}"
          if waits:
            text += f"\n\t\tthe plan waits for: {'; '.join(waits)}"
          for s in steps:
            where = f" -> minimap {s['target_minimap']}" if s.get("target_minimap") else ""
            text += f"\n\t\tphase {s['phase']}: {s['order']}{where}"
        text += "\n" + "\n".join("\t" + line for line in rt.plan_progress().splitlines())
    if agent.config.ENABLE_COMMUNICATION:
      text += agent.last_text_c_inp + agent.last_text_c_tar
    text += f"\n\nGive each team no more than {agent.config.MAX_NUM_ACTIONS} actions."
    text += "\nNow, start generating your analysis and actions:"
    return text


for _race in ("protoss", "terran", "zerg"):
  llm_prompt.FACTORY[_race]['stratagem'] = StratagemPrompt
  llm_observation.FACTORY[_race]['stratagem'] = StratagemTranslatorO

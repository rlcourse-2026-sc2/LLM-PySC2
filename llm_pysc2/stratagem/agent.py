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

"""MainAgent for a StratagemDSL map.

Differences to the stock MainAgent, all through hooks:
  * the config is generated from the bundle (llm_pysc2.stratagem.config), for the bundle's allied race;
  * a new unit joins the agent of the *force* it belongs to (StratagemRuntime: owner, type, nearest spawn),
    not the first agent that lists its unit type -- two Zergling forces get two different commanders;
  * the camera transform is known from the bundle (world_range = map height, raw 1 px = 1 cell), so the
    stock calibration loop is skipped (it cannot finish for a unit near the map edge);
  * every step updates the runtime (force tracking, region events, plan progress) used by the prompt.
"""

from loguru import logger

from llm_pysc2.agents.llm_pysc2_agent import LLMAgent
from llm_pysc2.agents.llm_pysc2_agent_main import MainAgent
from llm_pysc2.stratagem import offline_client, prompt  # noqa: F401  (registers 'stratagem' and 'offline')
from llm_pysc2.stratagem.bundle import TaskBundle
from llm_pysc2.stratagem.config import StratagemAgentConfig
from llm_pysc2.stratagem.runtime import StratagemRuntime


class StratagemMainAgent(MainAgent):

  def __init__(self, bundle, *, condition="intents", layout="per-force", model_name="offline", api_base=None,
               api_key=None, temperature=None, communication=False, decision_frequency=None, max_actions=None,
               config_overrides=None, SubAgent=LLMAgent):
    self.bundle = bundle if isinstance(bundle, TaskBundle) else TaskBundle.load(bundle)
    config = StratagemAgentConfig(self.bundle, condition=condition, layout=layout, model_name=model_name,
                                  api_base=api_base, api_key=api_key, temperature=temperature,
                                  communication=communication)
    if decision_frequency is not None:
      config.MAX_LLM_DECISION_FREQUENCY = decision_frequency
    if max_actions is not None:
      config.MAX_NUM_ACTIONS = max_actions
    for k, v in (config_overrides or {}).items():
      setattr(config, k, v)
    self.runtime = StratagemRuntime(self.bundle)
    config.stratagem_runtime = self.runtime
    super(StratagemMainAgent, self).__init__(config, SubAgent)
    # The camera transform is known: raw_resolution = map side, so raw x = floor(world x) and raw y =
    # floor(height - world y); get_camera_xy gives world coordinates (within a cell) with world_range = height
    # and zero offsets. The stock calibration loop (main_agent_func0) is not needed, and it never ends when
    # the calibration unit stands closer to the map edge than half a screen: the game clamps the camera, so
    # the unit can never reach the screen centre (e.g. the Hatchery of dhls).
    self.world_range = self.bundle.height
    self.world_xy_calibration = True
    self.agent_of_force = {}
    for agent_name, forces in config.force_of_agent.items():
      for f in forces:
        self.agent_of_force[f] = agent_name
    self.episode_result = None
    self.last_reward = 0
    logger.success(f"[ID {self.log_id}] StratagemMainAgent for {self.bundle.name}: race {config.race}, "
                   f"condition {condition}, layout {layout}, agents {list(config.AGENTS)}")

  # main_agent_funcs.get_new_unit_agent hook
  def unit_agent_resolver(self, obs, unit):
    force = self.runtime.force_of(unit.tag)
    agent = self.agent_of_force.get(force)
    if agent is None:
      return f"unit {hex(unit.tag)} belongs to {force or 'no force'}, which no agent commands"
    return agent

  def step(self, obs):
    self.runtime.update(obs)
    if self.first_select_unit_tag is None:
      # main_agent_func0 picks this unit while estimating world_range; we skip the estimate (it is known),
      # so pick the calibration unit the same way: a base if there is one, else any unit of ours.
      from llm_pysc2.lib.utils import BASE_BUILDING_TYPE
      from pysc2.lib import features
      own = [u for u in obs.observation.raw_units if u.alliance == features.PlayerRelative.SELF]
      base = [u for u in own if u.unit_type in BASE_BUILDING_TYPE]
      if own:
        pick = (base or own)[-1]
        self.first_select_unit_tag, self.first_select_unit_type = pick.tag, pick.unit_type
    if obs.last():
      self.last_reward = int(obs.reward)
      self.episode_result = {1: "victory", -1: "defeat"}.get(self.last_reward, "tie")
    return super(StratagemMainAgent, self).step(obs)

  def setup_complete(self):
    """Calibrated, and every living unit of a commanded force is in its agent's unit list."""
    if not self.world_xy_calibration:
      return False
    alive = sum(len(self.runtime.tracker.states[f].alive) for f in self.agent_of_force)
    grouped = sum(len(a.unit_tag_list) for a in self.agents.values())
    return grouped >= alive and not self.unit_uid_appear

  def llm_stats(self):
    out = {}
    for name, agent in self.agents.items():
      c = agent.client
      out[name] = {"queries": c.num_query, "seconds": round(c.total_query_time, 2),
                   "tokens_in": c.total_query_token_in, "tokens_out": c.total_query_token_out,
                   "enabled": agent.enable, "units": len(agent.unit_tag_list)}
    return out

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

"""Three-race actions and the StratagemDSL bridge (python -m pytest tests/test_stratagem_bridge.py).

The bridge tests build maps with StratagemDSL (`strat llm-pysc2`) and play them on the fake engine with the
offline planner, so they need stratagemdsl installed but neither StarCraft II nor an LLM.
"""

import json
import os
from pathlib import Path

import pytest
from absl import flags

from pysc2.lib import actions, units

flags.FLAGS(["pytest"], known_only=True)

from llm_pysc2.lib import llm_action, llm_client, llm_observation, llm_prompt  # noqa: E402
from llm_pysc2.lib.unit_actions import actions_for_unit, morph_family, unit_type_id  # noqa: E402

stratagemdsl = pytest.importorskip("stratagemdsl")
from stratagemdsl import paths as strat_paths  # noqa: E402

EXAMPLES = strat_paths.REPO_ROOT / "examples"


# ------------------------------------------------------------------ actions
def _tables():
  for name in dir(llm_action):
    v = getattr(llm_action, name)
    if name.isupper() and isinstance(v, list) and v and isinstance(v[0], dict) and 'func' in v[0]:
      yield name, v


def test_every_action_id_is_its_functions_id():
  bad = [(name, a['name'], t[0], t[1].name) for name, table in _tables() for a in table for t in a['func']
         if t[0] != int(t[1].id)]
  assert not bad
  inject = next(a for a in llm_action.ZERG_ACTION_ABILITY if a['name'] == 'Ability_InjectLarva')
  assert inject['func'][1][0] == int(actions.FUNCTIONS.Effect_InjectLarva_screen.id) == 204


@pytest.mark.parametrize("race", ["protoss", "terran", "zerg"])
def test_factories_cover_every_race(race):
  assert 'default' in llm_prompt.FACTORY[race]
  assert 'default' in llm_observation.FACTORY[race]
  assert 'default' in llm_action.FACTORY[race]


def test_unit_action_spaces():
  names = lambda race, n: [a['name'] for a in actions_for_unit(race, unit_type_id(race, n))]  # noqa: E731
  assert 'BurrowDown' in names('zerg', 'Roach') and 'Attack_Unit' in names('zerg', 'Roach')
  assert names('zerg', 'RoachBurrowed') == ['Stop', 'No_Operation', 'BurrowUp']
  assert 'Morph_SiegeMode' in names('terran', 'SiegeTank') and 'Ability_Stim' in names('terran', 'Marine')
  assert 'Ability_Blink_Screen' in names('protoss', 'Stalker')
  assert 'Attack_Unit' not in names('zerg', 'Overlord')
  assert units.Zerg.RoachBurrowed in morph_family('zerg', 'Roach')


def test_translator_keys_actions_by_their_own_team():
  config = type("C", (), {})()
  config.AGENTS = {'A': {'action': {units.Zerg.Roach: actions_for_unit('zerg', units.Zerg.Roach)}}}
  tr = llm_action.DefaultTranslatorA('A', 0, config)
  lists, by_team, _ = tr.translate("Actions:\n  Team b:\n    <Move_Minimap([1, 2])>\n  Team a:\n    <Hold_Position()>\n")
  assert [x[0]['name'] for x in lists] == ['Move_Minimap', 'Hold_Position']
  assert by_team['b'][0]['name'] == 'Move_Minimap' and by_team['a'][0]['name'] == 'Hold_Position'


def test_unknown_model_names_use_the_openai_compatible_client():
  assert llm_client.get_client_class('deepseek-chat') is llm_client.GptClient
  assert llm_client.get_client_class('glm-4-flash') is llm_client.GlmClient
  assert llm_client.get_client_class('gpt-4o') is llm_client.GptClient


# ------------------------------------------------------------------ bridge
def _build(name, src, tmp_path_factory):
  from stratagemdsl import cli
  out = tmp_path_factory.mktemp(name)
  assert cli.main(["llm-pysc2", str(src), "-o", str(out)]) == 0
  return out / f"{Path(src).stem}.llm_pysc2.json"


@pytest.fixture(scope="module")
def zerg_bundle(tmp_path_factory):
  return _build("cerulean_lure", EXAMPLES / "demos/cerulean_lure_zerg_vs_protoss.strat", tmp_path_factory)


@pytest.fixture(scope="module")
def terran_bundle(tmp_path_factory):
  return _build("cerulean_feint", EXAMPLES / "petri/cerulean_feint_cycle.strat", tmp_path_factory)


def test_bundle_and_config(zerg_bundle):
  from llm_pysc2.stratagem.bundle import TaskBundle
  from llm_pysc2.stratagem.config import StratagemAgentConfig
  b = TaskBundle.load(zerg_bundle)
  assert b.races == {"ally": "zerg", "enemy": "protoss"} and b.controlled == ["zergling_bait", "roach_strike"]
  assert b.world_to_minimap(*b.regions["east_lure_zone"]["world"]) == b.regions["east_lure_zone"]["minimap"]
  cfg = StratagemAgentConfig(b, condition="intents", model_name="offline")
  assert set(cfg.AGENTS) == {"CombatGroup-zergling_bait", "CombatGroup-roach_strike"}
  team = cfg.AGENTS["CombatGroup-roach_strike"]["team"][0]
  assert team["select_type"] == "group" and units.Zerg.RoachBurrowed in team["unit_type"]
  single = StratagemAgentConfig(b, layout="single", model_name="offline")
  assert list(single.AGENTS) == ["CombatGroup-all"] and len(single.AGENTS["CombatGroup-all"]["team"]) == 2


def _run(bundle, tmp_path, **kw):
  from llm_pysc2.stratagem.runner import run
  summary, out = run(bundle, engine="fake", model_name="offline", episodes=1, out_dir=tmp_path, seed=1, **kw)
  rec = [json.loads(line) for line in (out / "episodes.jsonl").read_text().splitlines()][-1]
  return summary, rec


def test_zerg_forces_get_their_own_commanders_on_the_fake_engine(zerg_bundle, tmp_path):
  summary, rec = _run(zerg_bundle, tmp_path, max_minutes=1.5)
  assert summary["episodes"] == 1 and rec["result"] in ("victory", "defeat", "timeout")
  bait, strike = rec["agents"]["CombatGroup-zergling_bait"], rec["agents"]["CombatGroup-roach_strike"]
  assert bait["queries"] > 0 and strike["queries"] > 0
  assert rec["minimap_check_px"] and max(rec["minimap_check_px"]) < 1.5
  assert rec["calibration_warning"] is None
  # the bait reached the lure zone through LLM-PySC2's interface, and the map script reacted
  assert any(e["event"] == "enter" and e["force"] == "zergling_bait" and e["region"] == "east_lure_zone"
             for e in rec["events"])
  assert "bait_spotted" in [f for h in rec["engine"]["script"] for f in h["fired"]]
  assert rec["engine"]["agent_orders"] > 0


def test_terran_plan_runs_to_a_result(terran_bundle, tmp_path):
  summary, rec = _run(terran_bundle, tmp_path, max_minutes=3)
  assert rec["result"] in ("victory", "defeat")
  assert (tmp_path / "summary.json").is_file()


def test_provider_switches_reach_the_request(zerg_bundle, tmp_path, monkeypatch):
  """--no-thinking / --extra-body end up as fields of every chat completion request (openai 0.28 or 1.x)."""
  import types
  import openai
  from llm_pysc2.bin import stratagem_run
  from llm_pysc2.lib import llm_client
  sent = []

  def answer(kw):
    team = "zergling_bait-Zergling" if "zergling_bait" in kw["messages"][-1]["content"] else "roach_strike-Roach"
    return f"Analysis:\n  ok\nActions:\n  Team {team}:\n    <Hold_Position()>"

  if llm_client.OPENAI_V1:
    class FakeOpenAI:
      def __init__(self, api_key=None, base_url=None):
        sent.append({"client": (api_key, base_url)})
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self.create))

      def create(self, **kw):
        body = dict(kw, **(kw.pop("extra_body", None) or {}))
        sent.append(body)
        msg = types.SimpleNamespace(content=answer(body))
        return types.SimpleNamespace(usage=types.SimpleNamespace(prompt_tokens=10, completion_tokens=5),
                                     choices=[types.SimpleNamespace(message=msg)])
    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
  else:
    def fake_create(**kw):
      sent.append(kw)
      return {"usage": {"prompt_tokens": 10, "completion_tokens": 5},
              "choices": [{"message": {"content": answer(kw)}}]}
    monkeypatch.setattr(openai.ChatCompletion, "create", staticmethod(fake_create))
  rc = stratagem_run.main(["--bundle", str(zerg_bundle), "--engine", "fake", "--model", "deepseek-v4-pro",
                           "--api-base", "https://api.deepseek.com/v1", "--api-key", "sk-test", "--no-thinking",
                           "--llm-timeout", "120", "--max-minutes", "0.5", "-o", str(tmp_path)])
  bodies = [k for k in sent if "model" in k]
  assert rc == 0 and bodies
  assert all(k["model"] == "deepseek-v4-pro" and k["thinking"] == {"type": "disabled"} for k in bodies)
  if llm_client.OPENAI_V1:
    assert ("sk-test", "https://api.deepseek.com/v1") in [k["client"] for k in sent if "client" in k]
  else:
    assert openai.api_base == "https://api.deepseek.com/v1"


def test_units_at_the_map_edge_do_not_stall_the_camera(tmp_path_factory, tmp_path):
  """A force spawned within half a screen of the border: the clamped camera never centres it."""
  import re
  src = (EXAMPLES / "petri/cerulean_feint_cycle.strat").read_text(encoding="utf-8")
  src = re.sub(r"(feint_force = unit_group\([^;]*spawn=point_xy\()[0-9.]+, *[0-9.]+", r"\g<1>19.5, 70.5", src)
  d = tmp_path_factory.mktemp("edge")
  (d / "cerulean_edge.strat").write_text(src, encoding="utf-8")
  from stratagemdsl import cli
  base = strat_paths.base_maps_dir() / "cerulean_fall_le.SC2Map"
  assert cli.main(["llm-pysc2", str(d / "cerulean_edge.strat"), "--base-map", str(base), "-o", str(d)]) == 0
  summary, rec = _run(d / "cerulean_edge.llm_pysc2.json", tmp_path, max_minutes=1.5)
  assert rec["setup_loops"] is not None                     # every unit got grouped
  assert rec["agents"]["CombatGroup-feint_force"]["queries"] > 0

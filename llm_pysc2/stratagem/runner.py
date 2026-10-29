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

"""Episodes of a StratagemDSL map with LLM-PySC2 agents; writes the same summary as `strat play`.

    run(bundle_path, engine='sc2' | 'fake', episodes=N, condition=..., model_name=..., ...)

engine='sc2'  the real game: SC2Env with the map given by absolute path (no copying into Maps/), the
              agent as player 1 (allied race), a built-in bot as player 2 (the map script commands it)
engine='fake' the same SC2Env with llm_pysc2.stratagem.fake_sc2 in place of the binary

Run directory:
    summary.json         win rate (Wilson 95% interval), result counts, means, settings
    episodes.jsonl       one line per episode: result, game time, LLM queries/tokens per agent, region events,
                         calibration, the plan tracker's view; with the fake engine also the script's history
    LLM-PySC2's own per-agent logs stay in llm_log/<time>-<id>/ (path recorded per episode)
"""

import contextlib
import json
import sys
import time
from pathlib import Path

from absl import flags
from loguru import logger

from llm_pysc2.stratagem.bundle import TaskBundle

LOOPS_PER_SECOND = 22.4


def _ensure_flags():
  if not flags.FLAGS.is_parsed():
    flags.FLAGS(sys.argv[:1], known_only=True)


def map_class(bundle: TaskBundle, max_loops: int, step_mul: int):
  from pysc2.maps import lib as maps_lib
  path = bundle.map_path.resolve()
  if not path.is_file():
    raise FileNotFoundError(f"map not found: {path} (build it with `strat llm-pysc2`)")
  cls = type(f"Stratagem_{bundle.name}_{abs(hash(str(path))):x}", (maps_lib.Map,), dict(
    directory=str(path.parent), filename=path.stem, players=2, game_steps_per_episode=max_loops,
    step_mul=step_mul, score_index=-1))
  return cls()


def fake_factory(bundle: TaskBundle, max_loops: int, seed=None):
  from stratagemdsl.frontend import parse_file
  from stratagemdsl.packaging.terrain import load_profile
  from stratagemdsl.play.plansim import PlanSim
  strategy = parse_file(bundle.source_path)
  profile = load_profile(bundle.map_path)
  state = {"episode": 0}

  def make():
    state["episode"] += 1
    sim = PlanSim(strategy, profile, oracle=bool(bundle.map.get("oracle")), max_loops=max_loops,
                  player_id=int(bundle.players["ally"]), fog=True,
                  seed=None if seed is None else seed + state["episode"])
    state["sim"] = sim
    return sim, bundle
  make.state = state
  return make


@contextlib.contextmanager
def _patched_run_config(run_config):
  from pysc2 import run_configs
  from pysc2.env import sc2_env
  original = run_configs.get
  getter = lambda version=None: run_config  # noqa: E731
  run_configs.get = getter
  sc2_env.run_configs.get = getter
  try:
    yield
  finally:
    run_configs.get = original
    sc2_env.run_configs.get = original


def make_env(bundle: TaskBundle, *, max_loops: int, step_mul: int = 8, bot: str = "very_easy", sc2_version=None,
             realtime=False, visualize=False, seed=None, replay_dir=None):
  from pysc2.env import sc2_env
  from pysc2.lib import actions, features
  _ensure_flags()
  race = {"protoss": sc2_env.Race.protoss, "terran": sc2_env.Race.terran, "zerg": sc2_env.Race.zerg,
          "random": sc2_env.Race.random}
  aif = features.AgentInterfaceFormat(
    feature_dimensions=features.Dimensions(screen=(bundle.screen, bundle.screen),
                                           minimap=(bundle.minimap, bundle.minimap)),
    use_feature_units=True, use_raw_units=True, raw_resolution=bundle.raw_resolution,
    camera_width_world_units=bundle.camera_width, action_space=actions.ActionSpace.FEATURES)
  return sc2_env.SC2Env(
    map_name=map_class(bundle, max_loops, step_mul),
    players=[sc2_env.Agent(race[bundle.races["ally"]]),
             sc2_env.Bot(race.get(bundle.races["enemy"], sc2_env.Race.random), sc2_env.Difficulty[bot])],
    agent_interface_format=aif, step_mul=step_mul, game_steps_per_episode=max_loops, realtime=realtime,
    visualize=visualize, score_index=-1, random_seed=seed, version=sc2_version,
    save_replay_episodes=1 if replay_dir else 0, replay_dir=replay_dir)


def run_episode(env, agent, *, max_agent_steps=10 ** 7, fast_setup=True):
  """One game. With fast_setup the env advances 1 game loop per agent step (not step_mul) until the main
  agent has calibrated its camera and put every unit into its team's control group: LLM-PySC2 needs 2-3
  interface actions per unit for that, which at step_mul 8 costs ~10 s of game time on a 20-unit map --
  long enough for a scripted enemy to win a race the stratagem is about."""
  started = time.monotonic()
  timesteps = env.reset()
  agent.setup(env.observation_spec()[0], env.action_spec()[0])
  agent.reset()
  ts = timesteps[0]
  setup_loops = None
  for _ in range(max_agent_steps):
    func_call = agent.step(ts)
    if ts.last():
      break
    fast = fast_setup and setup_loops is None and not agent.setup_complete()
    if fast_setup and setup_loops is None and not fast:
      setup_loops = int(ts.observation.game_loop[0])
    ts = env.step([func_call], step_mul=1 if fast else None)[0]
  game_loop = int(ts.observation.game_loop[0])
  reward = int(ts.reward)
  result = {1: "victory", -1: "defeat"}.get(reward)
  if result is None:
    result = "timeout" if game_loop >= env._episode_length - 16 else "tie"
  return {"result": result, "reward": reward, "game_loop": game_loop, "setup_loops": setup_loops,
          "game_seconds": round(game_loop / LOOPS_PER_SECOND, 1),
          "wall_seconds": round(time.monotonic() - started, 1)}


def run(bundle_path, *, engine="sc2", episodes=1, condition="intents", layout="per-force", model_name="offline",
        api_base=None, api_key=None, temperature=None, communication=False, decision_frequency=None,
        max_actions=None, max_minutes=15.0, step_mul=8, bot="very_easy", sc2_version=None, realtime=False,
        visualize=False, seed=None, replay_dir=None, out_dir=None, config_overrides=None, on_episode=None,
        fast_setup=True):
  from stratagemdsl.play.runner import summarize
  from llm_pysc2.stratagem.agent import StratagemMainAgent
  bundle = TaskBundle.load(bundle_path)
  max_loops = int(max_minutes * 60 * LOOPS_PER_SECOND)
  out = Path(out_dir) if out_dir else Path("stratagem_runs") / f"{bundle.name}_{condition}_{model_name}_{engine}"
  out.mkdir(parents=True, exist_ok=True)
  settings = {"bundle": str(Path(bundle_path).resolve()), "map": str(bundle.map_path), "engine": engine,
              "condition": condition, "layout": layout, "model": model_name, "episodes": episodes,
              "max_minutes": max_minutes, "step_mul": step_mul, "bot": bot, "races": bundle.races,
              "fast_setup": fast_setup}
  factory = fake_factory(bundle, max_loops, seed) if engine == "fake" else None
  ctx = contextlib.nullcontext()
  if engine == "fake":
    from llm_pysc2.stratagem.fake_sc2 import FakeRunConfig
    ctx = _patched_run_config(FakeRunConfig(factory))
  elif engine != "sc2":
    raise ValueError("engine must be 'sc2' or 'fake'")
  records = []
  with ctx:
    env = make_env(bundle, max_loops=max_loops, step_mul=step_mul, bot=bot, sc2_version=sc2_version,
                   realtime=realtime, visualize=visualize, seed=seed, replay_dir=replay_dir)
    try:
      for k in range(episodes):
        agent = StratagemMainAgent(bundle, condition=condition, layout=layout, model_name=model_name,
                                   api_base=api_base, api_key=api_key, temperature=temperature,
                                   communication=communication, decision_frequency=decision_frequency,
                                   max_actions=max_actions, config_overrides=config_overrides)
        rec = run_episode(env, agent, fast_setup=fast_setup and not realtime)
        stats = agent.llm_stats()
        rec.update({
          "episode": k, "log_dir": str(Path(agent.log_dir_path).resolve()),
          "decisions": agent.main_loop_step,
          "llm_calls": sum(s["queries"] for s in stats.values()),
          "input_tokens": sum(s["tokens_in"] for s in stats.values()),
          "output_tokens": sum(s["tokens_out"] for s in stats.values()),
          "llm_seconds": round(sum(s["seconds"] for s in stats.values()), 1),
          "invalid_answers": 0, "agents": stats,
        })
        rec.update(agent.runtime.record())
        if factory is not None:
          sim = factory.state.get("sim")
          rec["engine"] = {"script": sim.history, "final": sim.summary(),
                           "agent_orders": len(env._controllers[0].action_log),
                           "agent_order_log": env._controllers[0].action_log[-200:]}
        records.append(rec)
        with (out / "episodes.jsonl").open("a", encoding="utf-8") as f:
          f.write(json.dumps({k2: v for k2, v in rec.items() if k2 != "final_state"}, ensure_ascii=False,
                             default=str) + "\n")
        logger.success(f"episode {k + 1}/{episodes}: {rec['result']} at {rec['game_seconds']} s game time, "
                       f"{rec['decisions']} decision loops, {rec['llm_calls']} LLM queries")
        if on_episode:
          on_episode(k, rec)
    finally:
      env.close()
  summary = summarize(records)
  summary["agent"] = f"llm-pysc2/{condition}"
  summary["settings"] = settings
  (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
  return summary, out

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

"""Play a StratagemDSL map with LLM-PySC2 agents.

  strat llm-pysc2 examples/demos/cerulean_lure_zerg_vs_protoss.strat -o build/cerulean     # in StratagemDSL
  python -m llm_pysc2.bin.stratagem_run --bundle build/cerulean/cerulean_lure_zerg_vs_protoss.llm_pysc2.json \
      --condition intents --model gpt-4o-mini --api-base https://api.openai.com/v1 --api-key sk-... --episodes 5

  --engine fake      no StarCraft II needed: a protocol-level stand-in (llm_pysc2.stratagem.fake_sc2)
  --model offline    no LLM needed: a scripted plan follower answers the prompts
"""

import argparse
import os
import sys


def main(argv=None):
  ap = argparse.ArgumentParser(prog="stratagem_run", description=__doc__,
                               formatter_class=argparse.RawDescriptionHelpFormatter)
  ap.add_argument("--bundle", required=True, help="<stem>.llm_pysc2.json written by `strat llm-pysc2`")
  ap.add_argument("--engine", choices=["sc2", "fake"], default="sc2")
  ap.add_argument("--condition", choices=["llm", "intents"], default="intents",
                  help="llm: objective, map and situation; intents: plus the plan and its estimated progress")
  ap.add_argument("--layout", choices=["per-force", "single"], default="per-force",
                  help="one LLM agent per allied force, or one agent for all of them")
  ap.add_argument("--model", default="offline", help="LLM name (any OpenAI-compatible name works); "
                                                     "'offline' = scripted plan follower, no API")
  ap.add_argument("--api-base", default=os.environ.get("LLM_PYSC2_API_BASE"))
  ap.add_argument("--api-key", default=os.environ.get("LLM_PYSC2_API_KEY"))
  ap.add_argument("--temperature", type=float)
  ap.add_argument("--extra-body", help='JSON merged into every request, e.g. \'{"thinking": {"type": "disabled"}}\'')
  ap.add_argument("--no-thinking", action="store_true",
                  help="turn reasoning off for DeepSeek/GLM ({\"thinking\": {\"type\": \"disabled\"}}) and Qwen "
                       "({\"enable_thinking\": false}); faster, fewer tokens")
  ap.add_argument("--llm-timeout", type=float, help="seconds before one LLM call counts as failed (default 45; "
                                                    "raise it for thinking models)")
  ap.add_argument("--llm-wait", type=float, help="seconds the game waits for answers per step before moving on "
                                                 "(default 15; the game is paused meanwhile unless --realtime)")
  ap.add_argument("--llm-retries", type=int, help="attempts per LLM call (default 5)")
  ap.add_argument("--communication", action="store_true", help="LLM-PySC2 agent-to-agent messages")
  ap.add_argument("--decision-frequency", type=float, help="max LLM decision loops per game second (default 1)")
  ap.add_argument("--max-actions", type=int, help="max actions per team per decision (default 3)")
  ap.add_argument("--episodes", type=int, default=1)
  ap.add_argument("--max-minutes", type=float, default=15.0)
  ap.add_argument("--step-mul", type=int, default=8)
  ap.add_argument("--bot", default="very_easy", help="difficulty of the built-in player 2 (the map script "
                                                      "commands the stratagem's enemy forces)")
  ap.add_argument("--sc2-version")
  ap.add_argument("--realtime", action="store_true")
  ap.add_argument("--visualize", action="store_true")
  ap.add_argument("--seed", type=int)
  ap.add_argument("--no-fast-setup", action="store_true", help="group units at the normal step_mul (slower "
                                                                "start, as stock LLM-PySC2)")
  ap.add_argument("--replays", help="save one replay per episode here (real game only)")
  ap.add_argument("-o", "--out-dir")
  args = ap.parse_args(argv)

  import json
  overrides = {}
  extra = json.loads(args.extra_body) if args.extra_body else {}
  if args.no_thinking:
    name = (args.model or "").lower()
    extra.update({"enable_thinking": False} if name.startswith("qwen") else {"thinking": {"type": "disabled"}})
  if extra:
    overrides["LLM_EXTRA_BODY"] = extra
  if args.llm_timeout is not None:
    overrides["MAX_LLM_RUNTIME_ERROR_TIME"] = args.llm_timeout
  if args.llm_wait is not None:
    overrides["MAX_LLM_WAITING_TIME"] = args.llm_wait
  if args.llm_retries is not None:
    overrides["MAX_LLM_QUERY_TIMES"] = args.llm_retries

  from llm_pysc2.stratagem.runner import run
  summary, out = run(args.bundle, engine=args.engine, episodes=args.episodes, condition=args.condition,
                     layout=args.layout, model_name=args.model, api_base=args.api_base, api_key=args.api_key,
                     temperature=args.temperature, communication=args.communication,
                     decision_frequency=args.decision_frequency, max_actions=args.max_actions,
                     max_minutes=args.max_minutes, step_mul=args.step_mul, bot=args.bot,
                     sc2_version=args.sc2_version, realtime=args.realtime, visualize=args.visualize,
                     seed=args.seed, replay_dir=args.replays, out_dir=args.out_dir,
                     fast_setup=not args.no_fast_setup, config_overrides=overrides)
  lo, hi = summary["win_rate_ci95"]
  print(f"{summary['agent']} ({args.model}, engine {args.engine}): win rate {summary['win_rate']:.2f} "
        f"(95% CI {lo:.2f}-{hi:.2f}) over {summary['episodes']} episodes; results {summary['results']}")
  print(f"logs in {out}")
  return 0


if __name__ == "__main__":
  sys.exit(main())

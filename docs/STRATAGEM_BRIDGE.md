# StratagemDSL 地图接入（`llm_pysc2.stratagem`）

这个分支（`feature/stratagemdsl-bridge`）让 LLM-PySC2 直接运行 [StratagemDSL](https://github.com/xxxxhong/StratagemDSL)
生成的地图，并把原来只覆盖神族的部分补全到人族和虫族。

## 1. 安装

```bash
conda create -n sc2llm python=3.10 && conda activate sc2llm     # stratagemdsl 需要 Python 3.10+
pip install -e .                                                # 本仓库（LLM-PySC2）
pip install -e <StratagemDSL 仓库>                               # feature/petri-net-v06 或之后
```

真机需要 StarCraft II（Linux 无头版或 Windows/macOS 客户端，`SC2PATH` 指向安装目录）。地图按绝对路径加载，不需要拷进 `Maps/`。

## 2. 一条命令跑通

```bash
# StratagemDSL：编译、打包 --gameover 地图，写任务包
strat llm-pysc2 examples/demos/cerulean_lure_zerg_vs_protoss.strat -o build/cerulean

# LLM-PySC2：真机 + 真实 LLM（任何 OpenAI 兼容的模型名都可以）
python -m llm_pysc2.bin.stratagem_run --bundle build/cerulean/cerulean_lure_zerg_vs_protoss.llm_pysc2.json \
    --condition intents --model deepseek-chat --api-base https://api.deepseek.com/v1 --api-key $KEY --episodes 10

# 没有 SC2 / 没有 API key 时
python -m llm_pysc2.bin.stratagem_run --bundle ... --engine fake --model offline
```

DeepSeek（OpenAI 兼容接口）示例，思考模式默认开启，关掉更快更省：

```bash
python -m llm_pysc2.bin.stratagem_run --bundle ... --model deepseek-v4-pro \
    --api-base https://api.deepseek.com/v1 --api-key $DEEPSEEK_API_KEY --no-thinking
# 保留思考模式时放宽超时：--llm-timeout 300 --llm-wait 300
```

`--extra-body '<JSON>'` 把任意字段加进每次请求；`--llm-timeout`（单次调用多久算失败，默认 45 秒）、`--llm-wait`（每步等回答多久，默认 15 秒；
非实时模式下等待期间游戏暂停，超时后游戏照常推进）、`--llm-retries`。API 地址和 key 也可以用环境变量 `LLM_PYSC2_API_BASE`、`LLM_PYSC2_API_KEY`。

常用参数：`--condition llm|intents`（只给目标 / 再给计划和进度估计），`--layout per-force|single`（每支部队一个智能体 / 一个智能体管全部），
`--step-mul`、`--max-minutes`、`--bot`（内置 AI 难度）、`--communication`（智能体间消息）、`--replays DIR`、`--no-fast-setup`。

## 3. 模块

| 文件 | 作用 |
| --- | --- |
| `stratagem/bundle.py` | 读 `stratagemdsl.llm-pysc2-task.v1` 任务包；raw ↔ 世界 ↔ 小地图坐标 |
| `stratagem/config.py` | `StratagemAgentConfig`：按任务包生成 `AGENTS`，任意种族；每支己方部队一个 `CombatGroup-<force>`，每种单位一个小队、一个编队 |
| `stratagem/runtime.py` | 每步把 raw_units 交给 StratagemDSL 的 `ForceTracker`（单位→部队、区域事件、标定）和 `PlanTracker`（计划进度估计） |
| `stratagem/agent.py` | `StratagemMainAgent`：新单位按所属部队分给智能体（`main_agent_funcs.get_new_unit_agent` 的钩子），镜头变换已知 |
| `stratagem/prompt.py` | `'stratagem'` 系统提示词和观测翻译器（目标、命名区域、地形、全局态势、计划） |
| `stratagem/offline_client.py` | `--model offline`：按计划行动的脚本，替代 LLM 回答同一份提示词（测试和"照计划执行"对照） |
| `stratagem/runner.py` / `bin/stratagem_run.py` | SC2Env、多局循环、`summary.json` / `episodes.jsonl` |
| `stratagem/fake_sc2/` | 协议级 StarCraft II 替身：`SC2Env`、pysc2 `Features` 和 MainAgent 都是真实代码，游戏进程换成 StratagemDSL 的 `PlanSim` |
| `lib/unit_actions.py` | 三族单位的动作空间（神族取自 `ProtossAgentConfig`，人族/虫族取自 `llm_action.py`） |

## 4. 对原有代码的改动

- `lib/llm_action.py`：换成加入人族/虫族动作表的版本；载入时按函数对象校正编号
  （`Ability_InjectLarva` 527→204，`Morph_Baneling` 80→458，编号错了这两个动作永远不会被判为合法）；
  `DefaultTranslatorA` 的 `action_list_dict` 现在按动作所在小队的名字记录（原来记到下一个小队名下）。
- `lib/llm_prompt.py`、`llm_observation.py`、`llm_communicate.py`：`TERRAN_FACTORY`、`ZERG_FACTORY` 补上（原来为空，人族/虫族智能体初始化即 KeyError）；
  修正 `CommanderPrompt`/`DeveloperPrompt` 的 `super()` 调用。
- `lib/llm_client.py`：`get_client_class(model_name)`，不在表里的模型名按家族回退，默认 OpenAI 兼容客户端；
  同时支持 openai 0.28 和 1.x SDK（原来锁死 0.28，和 StratagemDSL 的 `strat generate` 需要的 openai>=1.0 装不进同一个环境）。
- `agents/llm_pysc2_agent.py`：LLM 的 `Team X:` 块按名字对齐到小队执行（原来按出现顺序）；`get_func` 复制函数列表再弹出，不再清空共享的动作字典。
- `agents/main_agent_funcs.py`：`get_new_unit_agent` 先问主智能体的 `unit_agent_resolver`（没有时行为不变）；
  `get_camera_func_smart` 在镜头已两次移到同一位置、单位仍在屏幕上时不再重复移镜头（地图边缘镜头被夹住，单位永远到不了屏幕中心，原来会无限循环）。
- `agents/llm_pysc2_agent_main.py`：`func_id_history` 以一个 no-op 开头（第一步就会读 `[-1]`）；日志目录取下一个空闲编号
  （原来若同一秒已有同名目录——另一个进程同秒启动——`_initialize_logger` 会死循环）。
- `setup.py`：补全子包、`enum34` 只在老 Python 安装、`stratagem` extra、`llm_pysc2_stratagem` 命令。

## 5. 输出

`<out>/summary.json`（与 `strat play` 同格式：胜率、Wilson 95% 区间、结果计数、平均时长、LLM 调用/token）；
`<out>/episodes.jsonl` 每局：结果、`setup_loops`（编组用掉的 game loop）、各智能体查询次数与 token、区域事件、`calibration`、
`minimap_check_px`（任务包的小地图换算与游戏小地图的偏差）、`plan_tracker`；`--engine fake` 另有 `engine.script`（地图脚本实际触发的转移与敌方命令）
和 `engine.agent_order_log`。逐智能体的提示词、观测、回答、pysc2 函数在 `llm_log/<时间>-<id>/` 下。

## 6. 局限

替身引擎只用于验证接口和流程：数值、寻路、技能效果都是近似，结果不代表真机表现。计划进度是从己方视角估计的。
内置 AI（玩家 2）在真机上可能和地图脚本争夺敌方单位，先跑一局看回放。

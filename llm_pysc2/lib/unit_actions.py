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

"""Action space of one combat unit type, for all three races.

`ProtossAgentConfig` writes a Protoss unit's actions by hand inside each agent
entry. Configs that are generated (e.g. `llm_pysc2.stratagem`) need the same
thing per unit type for any race:

    actions_for_unit('zerg', units.Zerg.Roach)
      -> ZERG_BASIC_ACTION_2 + [BurrowDown, BurrowUp]

Protoss entries are collected from ProtossAgentConfig, so they stay identical
to the hand-written configs. Terran and Zerg entries pick named abilities from
TERRAN_ACTION_ABILITY / ZERG_ACTION_ABILITY in llm_action.py.
"""

from pysc2.lib import units
from loguru import logger

from llm_pysc2.lib import llm_action as A

BASIC = {
  'protoss': (A.PROTOSS_BASIC_ACTION_1, A.PROTOSS_BASIC_ACTION_2, A.PROTOSS_BASIC_ACTION_3),
  'terran': (A.TERRAN_BASIC_ACTION_1, A.TERRAN_BASIC_ACTION_2, A.TERRAN_BASIC_ACTION_3),
  'zerg': (A.ZERG_BASIC_ACTION_1, A.ZERG_BASIC_ACTION_2, A.ZERG_BASIC_ACTION_3),
}
ABILITY_TABLE = {'terran': A.TERRAN_ACTION_ABILITY, 'zerg': A.ZERG_ACTION_ABILITY, 'protoss': A.PROTOSS_ACTION_ABILITY}

# units that cannot attack: they get BASIC_ACTION_3 (no Attack_Unit)
NO_ATTACK = {
  'Observer', 'ObserverSurveillanceMode', 'WarpPrism', 'WarpPrismPhasing', 'Disruptor', 'AdeptPhaseShift',
  'Medivac', 'Raven', 'WidowMine', 'MULE',
  'Overlord', 'OverlordTransport', 'Overseer', 'OverseerOversightMode', 'Infestor', 'SwarmHostMP', 'Viper',
  'Lurker', 'Larva', 'Egg', 'LocustMP', 'Changeling',
}

TERRAN_ABILITIES = {
  'SCV': ['Ability_Repair_Unit'],
  'Marine': ['Ability_Stim'],
  'Marauder': ['Ability_Stim'],
  'Ghost': ['Ability_GhostSnipe', 'Ability_EMP_Screen', 'Ability_EMP_Unit', 'Behavior_CloakOn_Ghost',
            'Behavior_CloakOff_Ghost'],
  'Hellion': ['Morph_Hellbat'],
  'HellionTank': ['Morph_Hellion'],
  'SiegeTank': ['Morph_SiegeMode'],
  'SiegeTankSieged': ['Morph_Unsiege'],
  'Cyclone': ['Ability_LockOn_Unit'],
  'WidowMine': ['BurrowDown_WidowMine'],
  'WidowMineBurrowed': ['BurrowUp_WidowMine'],
  'Thor': ['Morph_ThorHighImpactMode'],
  'ThorHighImpactMode': ['Morph_ThorExplosiveMode'],
  'VikingFighter': ['Morph_VikingAssaultMode'],
  'VikingAssault': ['Morph_VikingFighterMode'],
  'Medivac': ['Load_Medivac', 'UnloadAllAt_Medivac_Screen', 'UnloadAllAt_Medivac_Minimap',
              'Ability_MedivacIgniteAfterburners'],
  'Liberator': ['Morph_LiberatorAGMode_Screen'],
  'LiberatorAG': ['Morph_LiberatorAAMode'],
  'Raven': ['Ability_RavenAutoTurret_Screen', 'Ability_RavenAntiArmorMissile_Unit',
            'Ability_RavenInterferenceMatrix_Unit'],
  'Banshee': ['Behavior_CloakOn_Banshee', 'Behavior_CloakOff_Banshee'],
  'Battlecruiser': ['Ability_YamatoGun_Unit', 'Ability_TacticalJump_Screen', 'Ability_TacticalJump_Minimap'],
}

ZERG_ABILITIES = {
  'Drone': ['BurrowDown', 'BurrowUp'],
  'Queen': ['Ability_InjectLarva', 'Ability_Transfusion', 'Build_CreepTumor_Screen', 'BurrowDown', 'BurrowUp'],
  'Zergling': ['Morph_Baneling', 'BurrowDown', 'BurrowUp'],
  'ZerglingBurrowed': ['BurrowUp'],
  'Baneling': ['Explode', 'BurrowDown', 'BurrowUp'],
  'BanelingBurrowed': ['BurrowUp', 'Explode'],
  'Roach': ['Morph_Ravager', 'BurrowDown', 'BurrowUp'],
  'RoachBurrowed': ['BurrowUp'],
  'Ravager': ['Ability_CorrosiveBile_Screen', 'BurrowDown', 'BurrowUp'],
  'Hydralisk': ['Morph_Lurker', 'BurrowDown', 'BurrowUp'],
  'HydraliskBurrowed': ['BurrowUp'],
  'Lurker': ['BurrowDown', 'BurrowUp'],
  'LurkerBurrowed': ['BurrowUp'],
  'Infestor': ['Ability_FungalGrowth_Screen', 'Ability_FungalGrowth_Unit', 'Ability_NeuralParasite',
               'BurrowDown', 'BurrowUp'],
  'SwarmHostMP': ['Ability_SpawnLocusts_Screen', 'BurrowDown', 'BurrowUp'],
  'Ultralisk': ['BurrowDown', 'BurrowUp'],
  'Corruptor': ['Ability_CausticSpray', 'Morph_BroodLord'],
  'Viper': ['Ability_ParasiticBomb', 'Ability_ViperConsume', 'Ability_AbductUnit', 'Ability_BlindingCloud_Screen'],
  'Overlord': ['Morph_Overseer', 'Morph_OverlordTransport'],
  'OverlordTransport': ['Load_Unit', 'UnloadAllAt_Screen', 'UnloadAllAt_Minimap'],
  'Overseer': ['Ability_Contaminate', 'Ability_SpawnChangeling', 'Morph_OversightMode'],
  'OverseerOversightMode': ['Morph_OverseerMode'],
  'NydusCanal': ['UnloadAll_NydusWorm_quick'],
}

BURROWED = {'ZerglingBurrowed', 'BanelingBurrowed', 'RoachBurrowed', 'HydraliskBurrowed', 'LurkerBurrowed',
            'WidowMineBurrowed', 'SiegeTankSieged', 'DroneBurrowed', 'InfestorBurrowed', 'UltraliskBurrowed',
            'QueenBurrowed', 'SwarmHostBurrowedMP', 'RavagerBurrowed'}


def _race_enum(race):
  return {'protoss': units.Protoss, 'terran': units.Terran, 'zerg': units.Zerg}[race]


def unit_name(unit_type) -> str:
  try:
    return units.get_unit_type(int(unit_type)).name
  except Exception:
    return str(unit_type)


def _protoss_table():
  from llm_pysc2.agents.configs.config import ProtossAgentConfig
  table = {}
  for agent in ProtossAgentConfig().AGENTS.values():
    for unit_type, acts in agent['action'].items():
      if isinstance(unit_type, str):
        continue
      have = table.setdefault(int(unit_type), [])
      names = {a['name'] for a in have}
      have += [a for a in acts if a['name'] not in names]
  return table


_PROTOSS = None


def actions_for_unit(race: str, unit_type) -> list:
  """The action list (LLM-PySC2 action dicts) for one unit type of `race`."""
  global _PROTOSS
  name = unit_name(unit_type)
  structure = False
  try:
    from llm_pysc2.lib.utils import BUILDING_TYPE
    structure = int(unit_type) in [int(t) for t in BUILDING_TYPE]
  except Exception:
    pass
  b1, b2, b3 = BASIC[race]
  if race == 'protoss':
    if _PROTOSS is None:
      _PROTOSS = _protoss_table()
    if int(unit_type) in _PROTOSS:
      return list(_PROTOSS[int(unit_type)])
    return list(b1) if structure else list(b3 if name in NO_ATTACK else b2)
  if structure:
    return list(b1)
  wanted = (TERRAN_ABILITIES if race == 'terran' else ZERG_ABILITIES).get(name, [])
  table = {a['name']: a for a in ABILITY_TABLE[race]}
  extra = []
  for w in wanted:
    if w in table:
      extra.append(table[w])
    else:
      logger.warning(f"unit_actions: {race} ability {w} for {name} is not in the action table")
  if name in BURROWED:
    keep = [a for a in b3 if a['name'] in ('Stop', 'No_Operation')]
    if name in ('LurkerBurrowed', 'SiegeTankSieged', 'WidowMineBurrowed'):
      keep += [a for a in b2 if a['name'] == 'Attack_Unit']
    return keep + extra
  return list(b3 if name in NO_ATTACK else b2) + extra


def unit_type_id(race: str, name: str):
  """'Roach' -> units.Zerg.Roach (None when the race has no such unit)."""
  enum = _race_enum(race)
  try:
    return enum[name]
  except KeyError:
    for e in (units.Protoss, units.Terran, units.Zerg, units.Neutral):
      try:
        return e[name]
      except KeyError:
        continue
  return None


def morph_family(race: str, name: str) -> list:
  """Unit types a unit of type `name` can turn into during a game (burrow, siege, morphs)."""
  fam = {
    'Zergling': ['ZerglingBurrowed', 'Baneling'], 'Baneling': ['BanelingBurrowed'],
    'Roach': ['RoachBurrowed', 'Ravager'], 'Ravager': ['RavagerBurrowed'],
    'Hydralisk': ['HydraliskBurrowed', 'Lurker', 'LurkerBurrowed'], 'Lurker': ['LurkerBurrowed'],
    'Drone': ['DroneBurrowed'], 'Infestor': ['InfestorBurrowed'], 'Ultralisk': ['UltraliskBurrowed'],
    'Queen': ['QueenBurrowed'], 'SwarmHostMP': ['SwarmHostBurrowedMP'], 'Corruptor': ['BroodLord'],
    'Overlord': ['Overseer', 'OverlordTransport', 'OverseerOversightMode'], 'Overseer': ['OverseerOversightMode'],
    'SiegeTank': ['SiegeTankSieged'], 'Hellion': ['HellionTank'], 'HellionTank': ['Hellion'],
    'VikingFighter': ['VikingAssault'], 'VikingAssault': ['VikingFighter'], 'WidowMine': ['WidowMineBurrowed'],
    'Liberator': ['LiberatorAG'], 'Thor': ['ThorHighImpactMode'],
    'Observer': ['ObserverSurveillanceMode'], 'WarpPrism': ['WarpPrismPhasing'], 'Adept': ['AdeptPhaseShift'],
    'HighTemplar': ['Archon'], 'DarkTemplar': ['Archon'],
  }
  out = []
  for n in [name] + fam.get(name, []):
    t = unit_type_id(race, n)
    if t is not None and t not in out:
      out.append(t)
  return out

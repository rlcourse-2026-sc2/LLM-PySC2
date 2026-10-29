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

from pysc2.lib.actions import FUNCTIONS as F
from pysc2.lib import features

from llm_pysc2.lib.utils import *

from loguru import logger
import random
import re

# # Basic Terran actions for SMAC tasks where attack is sufficient
# TERRAN_BASIC_ACTION_SMAC = [
#     {'name': 'Attack_Unit', 'arg': ['tag'],
#      'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
# ]

# # Basic Terran actions for SMAC tasks where movement is required
# TERRAN_BASIC_ACTION_SMAC2 = [
#     {'name': 'Attack_Unit', 'arg': ['tag'],
#      'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
#     {'name': 'Move_Screen', 'arg': ['screen'],
#      'func': [(331, F.Move_screen, ('queued', 'screen'))]},
# ]

# # Actions for Terran buildings
# TERRAN_BASIC_ACTION_1 = [
#     {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]},
#     {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
#     {'name': 'Stop_Building', 'arg': [], 'func': [(454, F.Stop_Building_quick, ('queued'))]},
# ]

# # Actions for Terran combat units
# TERRAN_BASIC_ACTION_2 = [
#     {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]}, 
#     {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
#     {'name': 'Hold_Position', 'arg': [], 'func': [(274, F.HoldPosition_quick, ('queued'))]},
#     {'name': 'Move_Minimap', 'arg': ['minimap'], 'func': [(332, F.Move_minimap, ('queued', 'minimap'))]},
#     {'name': 'Move_Screen', 'arg': ['screen'], 'func': [(331, F.Move_screen, ('queued', 'screen'))]},
#     {'name': 'Attack_Unit', 'arg': ['tag'], 'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
# ]

# # Actions for non-combat Terran units
# TERRAN_BASIC_ACTION_3 = [
#     {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]},
#     {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
#     {'name': 'Hold_Position', 'arg': [], 'func': [(274, F.HoldPosition_quick, ('queued'))]},
#     {'name': 'Move_Minimap', 'arg': ['minimap'], 'func': [(332, F.Move_minimap, ('queued', 'minimap'))]},
#     {'name': 'Move_Screen', 'arg': ['screen'], 'func': [(331, F.Move_screen, ('queued', 'screen'))]},
# ]

# # Training actions for Terran production buildings
# TERRAN_ACTION_TRAIN = [
#     # Command Center
#     {'name': 'Train_SCV', 'arg': [], 'func': [(490, F.Train_SCV_quick, ('queued'))]},
    
#     # Barracks
#     {'name': 'Train_Marine', 'arg': [], 'func': [(477, F.Train_Marine_quick, ('queued'))]},
#     {'name': 'Train_Marauder', 'arg': [], 'func': [(476, F.Train_Marauder_quick, ('queued'))]},
#     {'name': 'Train_Reaper', 'arg': [], 'func': [(488, F.Train_Reaper_quick, ('queued'))]},
#     {'name': 'Train_Ghost', 'arg': [], 'func': [(468, F.Train_Ghost_quick, ('queued'))]},
    
#     # Factory  
#     {'name': 'Train_Hellion', 'arg': [], 'func': [(470, F.Train_Hellion_quick, ('queued'))]},
#     {'name': 'Train_Hellbat', 'arg': [], 'func': [(469, F.Train_Hellbat_quick, ('queued'))]},
#     {'name': 'Train_SiegeTank', 'arg': [], 'func': [(492, F.Train_SiegeTank_quick, ('queued'))]},
#     {'name': 'Train_Thor', 'arg': [], 'func': [(496, F.Train_Thor_quick, ('queued'))]},
#     {'name': 'Train_Cyclone', 'arg': [], 'func': [(597, F.Train_Cyclone_quick, ('queued'))]},
#     {'name': 'Train_WidowMine', 'arg': [], 'func': [(502, F.Train_WidowMine_quick, ('queued'))]},
    
#     # Starport
#     {'name': 'Train_Viking', 'arg': [], 'func': [(498, F.Train_VikingFighter_quick, ('queued'))]},
#     {'name': 'Train_Medivac', 'arg': [], 'func': [(478, F.Train_Medivac_quick, ('queued'))]},
#     {'name': 'Train_Liberator', 'arg': [], 'func': [(475, F.Train_Liberator_quick, ('queued'))]},
#     {'name': 'Train_Raven', 'arg': [], 'func': [(487, F.Train_Raven_quick, ('queued'))]},
#     {'name': 'Train_Banshee', 'arg': [], 'func': [(459, F.Train_Banshee_quick, ('queued'))]},
#     {'name': 'Train_Battlecruiser', 'arg': [], 'func': [(460, F.Train_Battlecruiser_quick, ('queued'))]},
# ]

# # Research actions for Terran tech buildings
# TERRAN_ACTION_RESEARCH = [
#     # Engineering Bay Research
#     {'name': 'Research_TerranInfantryArmor', 'arg': [], 
#      'func': [(406, F.Research_TerranInfantryArmor_quick, ('queued'))]},
#     {'name': 'Research_TerranInfantryWeapons', 'arg': [], 
#      'func': [(410, F.Research_TerranInfantryWeapons_quick, ('queued'))]},
#     {'name': 'Research_HiSecAutoTracking', 'arg': [], 
#      'func': [(369, F.Research_HiSecAutoTracking_quick, ('queued'))]},
#     {'name': 'Research_TerranStructureArmor', 'arg': [], 
#      'func': [(418, F.Research_TerranStructureArmorUpgrade_quick, ('queued'))]},

#     # Armory Research
#     {'name': 'Research_TerranVehicleWeapons', 'arg': [], 
#      'func': [(423, F.Research_TerranVehicleWeapons_quick, ('queued'))]},
#     {'name': 'Research_TerranShipWeapons', 'arg': [], 
#      'func': [(414, F.Research_TerranShipWeapons_quick, ('queued'))]},
#     {'name': 'Research_TerranVehicleAndShipPlating', 'arg': [], 
#      'func': [(419, F.Research_TerranVehicleAndShipPlating_quick, ('queued'))]},

#     # Barracks Tech Lab Research
#     {'name': 'Research_Stimpack', 'arg': [], 
#      'func': [(405, F.Research_Stimpack_quick, ('queued'))]},
#     {'name': 'Research_CombatShield', 'arg': [], 
#      'func': [(361, F.Research_CombatShield_quick, ('queued'))]},
#     {'name': 'Research_ConcussiveShells', 'arg': [], 
#      'func': [(362, F.Research_ConcussiveShells_quick, ('queued'))]},

#     # Factory Tech Lab Research
#     {'name': 'Research_InfernalPreigniter', 'arg': [], 
#      'func': [(371, F.Research_InfernalPreigniter_quick, ('queued'))]},
#     {'name': 'Research_DrillClaws', 'arg': [], 
#      'func': [(363, F.Research_DrillingClaws_quick, ('queued'))]},
#     {'name': 'Research_CycloneLockOnDamage', 'arg': [], 
#      'func': [(570, F.Research_CycloneLockOnDamage_quick, ('queued'))]},
#     {'name': 'Research_SmartServos', 'arg': [], 
#      'func': [(373, F.Research_SmartServos_quick, ('queued'))]},

#     # Starport Tech Lab Research
#     {'name': 'Research_BansheeCloak', 'arg': [], 
#      'func': [(353, F.Research_BansheeCloakingField_quick, ('queued'))]},
#     {'name': 'Research_BansheeSpeed', 'arg': [], 
#      'func': [(354, F.Research_BansheeHyperflightRotors_quick, ('queued'))]},
#     {'name': 'Research_RavenCorvidReactor', 'arg': [], 
#      'func': [(402, F.Research_RavenCorvidReactor_quick, ('queued'))]},

#     # Fusion Core Research
#     {'name': 'Research_BattlecruiserWeaponRefit', 'arg': [], 
#      'func': [(355, F.Research_BattlecruiserWeaponRefit_quick, ('queued'))]},
# ]

# # Building actions for Terran structures
# TERRAN_ACTION_BUILD = [
#     {'name': 'Build_CommandCenter_Near', 'arg': ['tag'],
#      'func': [(573, F.llm_pysc2_move_camera, ('world_tag')), 
#               (44, F.Build_CommandCenter_screen, ('queued', 'screen_tag'))]},
#     {'name': 'Build_Refinery_Near', 'arg': ['tag'],
#      'func': [(79, F.Build_Refinery_screen, ('queued', 'screen_tag'))]},
#     {'name': 'Build_SupplyDepot_Screen', 'arg': ['screen'],
#      'func': [(91, F.Build_SupplyDepot_screen, ('queued', 'screen'))]},
#     {'name': 'Build_Barracks_Screen', 'arg': ['screen'],
#      'func': [(42, F.Build_Barracks_screen, ('queued', 'screen'))]},
#     {'name': 'Build_EngineeringBay_Screen', 'arg': ['screen'],
#      'func': [(50, F.Build_EngineeringBay_screen, ('queued', 'screen'))]},
#     {'name': 'Build_Bunker_Screen', 'arg': ['screen'],
#      'func': [(43, F.Build_Bunker_screen, ('queued', 'screen'))]},
#     {'name': 'Build_MissileTurret_Screen', 'arg': ['screen'],
#      'func': [(64, F.Build_MissileTurret_screen, ('queued', 'screen'))]},
#     {'name': 'Build_SensorTower_Screen', 'arg': ['screen'],
#      'func': [(83, F.Build_SensorTower_screen, ('queued', 'screen'))]},
#     {'name': 'Build_GhostAcademy_Screen', 'arg': ['screen'],
#      'func': [(58, F.Build_GhostAcademy_screen, ('queued', 'screen'))]},
#     {'name': 'Build_Factory_Screen', 'arg': ['screen'],
#      'func': [(53, F.Build_Factory_screen, ('queued', 'screen'))]},
#     {'name': 'Build_Starport_Screen', 'arg': ['screen'],
#      'func': [(89, F.Build_Starport_screen, ('queued', 'screen'))]},
#     {'name': 'Build_Armory_Screen', 'arg': ['screen'],
#      'func': [(39, F.Build_Armory_screen, ('queued', 'screen'))]},
#     {'name': 'Build_FusionCore_Screen', 'arg': ['screen'],
#      'func': [(56, F.Build_FusionCore_screen, ('queued', 'screen'))]},
#     {'name': 'Build_Reactor_screen', 'arg': ['screen'], 
#      'func': [(72, F.Build_Reactor_screen, ('queued', 'screen'))]},
#     {'name': 'Build_TechLab_screen', 'arg': ['screen'], 
#      'func': [(93, F.Build_TechLab_screen, ('queued', 'screen'))]},

# ]

# # Unit abilities for Terran units
# TERRAN_ACTION_ABILITY = [
#     # Basic Unit Abilities
#     {'name': 'Ability_Repair_Unit', 'arg': ['tag'],
#      'func': [(220, F.Effect_Repair_screen, ('queued', 'screen_tag'))]},
#     {'name': 'Ability_Stim', 'arg': [],
#      'func': [(234, F.Effect_Stim_quick, ('queued'))]},
#     {'name': 'Load_Unit', 'arg': ['tag'],
#      'func': [(272, F.Load_screen, ('queued', 'screen_tag'))]},
#     {'name': 'UnloadAll_Quick', 'arg': [],
#      'func': [(274, F.UnloadAll_quick, ('queued'))]},
#     {'name': 'UnloadAllAt_Screen', 'arg': ['screen'],
#      'func': [(275, F.UnloadAllAt_screen, ('queued', 'screen'))]},

#     # Command Center Abilities
#     {'name': 'Ability_CalldownMULE_Screen', 'arg': ['screen'],
#      'func': [(183, F.Effect_CalldownMULE_screen, ('queued', 'screen'))]},
#     {'name': 'Ability_Scan_Screen', 'arg': ['screen'],
#      'func': [(227, F.Effect_Scan_screen, ('queued', 'screen'))]},
#     {'name': 'Ability_SupplyDrop_Unit', 'arg': ['tag'],
#      'func': [(239, F.Effect_SupplyDrop_screen, ('queued', 'screen_tag'))]},

#     # Building Morphs
#     {'name': 'Morph_SupplyDepot_Lower', 'arg': [],
#      'func': [(318, F.Morph_SupplyDepot_Lower_quick, ('queued'))]},
#     {'name': 'Morph_SupplyDepot_Raise', 'arg': [],
#      'func': [(319, F.Morph_SupplyDepot_Raise_quick, ('queued'))]},

#     # Unit Transformations
#     {'name': 'Morph_SiegeMode', 'arg': [],
#      'func': [(317, F.Morph_SiegeMode_quick, ('queued'))]},
#     {'name': 'Morph_Unsiege', 'arg': [],
#      'func': [(322, F.Morph_Unsiege_quick, ('queued'))]},
#     {'name': 'Morph_VikingAssaultMode', 'arg': [],
#      'func': [(321, F.Morph_VikingAssaultMode_quick, ('queued'))]},
#     {'name': 'Morph_VikingFighterMode', 'arg': [],
#      'func': [(322, F.Morph_VikingFighterMode_quick, ('queued'))]},
#     {'name': 'Morph_Hellion', 'arg': [],
#      'func': [(312, F.Morph_Hellion_quick, ('queued'))]},
#     {'name': 'Morph_Hellbat', 'arg': [],
#      'func': [(311, F.Morph_Hellbat_quick, ('queued'))]},
#     {'name': 'Morph_ThorHighImpact', 'arg': [],
#      'func': [(320, F.Morph_ThorHighImpactMode_quick, ('queued'))]},
#     {'name': 'Morph_ThorExplosive', 'arg': [],
#      'func': [(319, F.Morph_ThorExplosiveMode_quick, ('queued'))]},

#     # Special Unit Abilities
#     {'name': 'Ability_GhostSnipe', 'arg': ['tag'],
#      'func': [(195, F.Effect_GhostSnipe_screen, ('queued'))]},
#     {'name': 'Ability_GhostNuke_Screen', 'arg': ['screen'],
#      'func': [(217, F.Effect_NukeCalldown_screen, ('queued', 'screen'))]},
#     {'name': 'Ability_EMP_Screen', 'arg': ['screen'],
#      'func': [(195, F.Effect_EMP_screen, ('queued', 'screen'))]},
#     {'name': 'Ability_Cloak_On', 'arg': [],
#      'func': [(185, F.Behavior_CloakOn_quick, ('queued'))]},
#     {'name': 'Ability_RavenTurret_Screen', 'arg': ['screen'],
#      'func': [(180, F.Effect_AutoTurret_screen, ('queued', 'screen'))]},
#     {'name': 'Ability_RavenAntiArmor_Screen', 'arg': ['screen'],
#      'func': [(765, F.Effect_AntiArmorMissile_screen, ('queued', 'screen'))]},
#     {'name': 'Ability_RavenMatrix_Screen', 'arg': ['screen'],
#      'func': [(764, F.Effect_InterferenceMatrix_screen, ('queued', 'screen'))]},
#     {'name': 'Ability_YamatoGun_Screen', 'arg': ['screen'],
#      'func': [(277, F.Effect_YamatoGun_screen, ('queued', 'screen'))]},
#     {'name': 'Ability_TacticalJump_Screen', 'arg': ['screen'],
#      'func': [(763, F.Effect_TacticalJump_screen, ('queued', 'screen'))]},
#     {'name': 'Ability_WidowMineBurrow', 'arg': [],
#      'func': [(115, F.BurrowDown_WidowMine_quick, ('queued'))]},
#     {'name': 'Ability_WidowMineUnburrow', 'arg': [],
#      'func': [(137, F.BurrowUp_WidowMine_quick, ('queued'))]},
#     {'name': 'Ability_MedivacBoost', 'arg': [],
#      'func': [(211, F.Effect_MedivacIgniteAfterburners_quick, ('queued'))]},
# ]

# Basic Terran actions for SMAC tasks where attack is sufficient
TERRAN_BASIC_ACTION_SMAC = [
    {'name': 'Attack_Unit', 'arg': ['tag'],
     'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
]

# Basic Terran actions for SMAC tasks where movement is required
TERRAN_BASIC_ACTION_SMAC2 = [
    {'name': 'Attack_Unit', 'arg': ['tag'],
     'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
    {'name': 'Move_Screen', 'arg': ['screen'],
     'func': [(331, F.Move_screen, ('queued', 'screen'))]},
]

# Actions for Terran buildings
TERRAN_BASIC_ACTION_1 = [
    {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]},
    {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
    {'name': 'Stop_Building', 'arg': [], 'func': [(454, F.Stop_Building_quick, ('queued'))]},
]

# Actions for Terran combat units
TERRAN_BASIC_ACTION_2 = [
    {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]}, 
    {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
    {'name': 'Hold_Position', 'arg': [], 'func': [(274, F.HoldPosition_quick, ('queued'))]},
    {'name': 'Move_Minimap', 'arg': ['minimap'], 'func': [(332, F.Move_minimap, ('queued', 'minimap'))]},
    {'name': 'Move_Screen', 'arg': ['screen'], 'func': [(331, F.Move_screen, ('queued', 'screen'))]},
    {'name': 'Attack_Unit', 'arg': ['tag'], 'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
]

# Actions for non-combat Terran units
TERRAN_BASIC_ACTION_3 = [
    {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]},
    {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
    {'name': 'Hold_Position', 'arg': [], 'func': [(274, F.HoldPosition_quick, ('queued'))]},
    {'name': 'Move_Minimap', 'arg': ['minimap'], 'func': [(332, F.Move_minimap, ('queued', 'minimap'))]},
    {'name': 'Move_Screen', 'arg': ['screen'], 'func': [(331, F.Move_screen, ('queued', 'screen'))]},
]

# Training actions for Terran production buildings
TERRAN_ACTION_TRAIN = [
    # Command Center
    {'name': 'Train_SCV', 'arg': [], 'func': [(490, F.Train_SCV_quick, ('queued'))]},
    
    # Barracks
    {'name': 'Train_Marine', 'arg': [], 'func': [(477, F.Train_Marine_quick, ('queued'))]},
    {'name': 'Train_Marauder', 'arg': [], 'func': [(476, F.Train_Marauder_quick, ('queued'))]},
    {'name': 'Train_Reaper', 'arg': [], 'func': [(488, F.Train_Reaper_quick, ('queued'))]},
    {'name': 'Train_Ghost', 'arg': [], 'func': [(468, F.Train_Ghost_quick, ('queued'))]},
    
    # Factory  
    {'name': 'Train_Hellion', 'arg': [], 'func': [(470, F.Train_Hellion_quick, ('queued'))]},
    {'name': 'Train_Hellbat', 'arg': [], 'func': [(469, F.Train_Hellbat_quick, ('queued'))]},
    {'name': 'Train_SiegeTank', 'arg': [], 'func': [(492, F.Train_SiegeTank_quick, ('queued'))]},
    {'name': 'Train_Thor', 'arg': [], 'func': [(496, F.Train_Thor_quick, ('queued'))]},
    {'name': 'Train_Cyclone', 'arg': [], 'func': [(464, F.Train_Cyclone_quick, ('queued'))]},
    {'name': 'Train_WidowMine', 'arg': [], 'func': [(502, F.Train_WidowMine_quick, ('queued'))]},
    
    # Starport
    {'name': 'Train_Viking', 'arg': [], 'func': [(498, F.Train_VikingFighter_quick, ('queued'))]},
    {'name': 'Train_Medivac', 'arg': [], 'func': [(478, F.Train_Medivac_quick, ('queued'))]},
    {'name': 'Train_Liberator', 'arg': [], 'func': [(475, F.Train_Liberator_quick, ('queued'))]},
    {'name': 'Train_Raven', 'arg': [], 'func': [(487, F.Train_Raven_quick, ('queued'))]},
    {'name': 'Train_Banshee', 'arg': [], 'func': [(459, F.Train_Banshee_quick, ('queued'))]},
    {'name': 'Train_Battlecruiser', 'arg': [], 'func': [(460, F.Train_Battlecruiser_quick, ('queued'))]},
]

# Research actions for Terran tech buildings
TERRAN_ACTION_RESEARCH = [
    # Engineering Bay
    {'name': 'Research_TerranInfantryArmor', 'arg': [], 
     'func': [(406, F.Research_TerranInfantryArmor_quick, ('queued'))]},
    {'name': 'Research_TerranInfantryWeapons', 'arg': [], 
     'func': [(410, F.Research_TerranInfantryWeapons_quick, ('queued'))]},
    {'name': 'Research_HiSecAutoTracking', 'arg': [], 
     'func': [(369, F.Research_HiSecAutoTracking_quick, ('queued'))]},
    {'name': 'Research_TerranStructureArmor', 'arg': [], 
     'func': [(418, F.Research_TerranStructureArmorUpgrade_quick, ('queued'))]},

    # Armory
    {'name': 'Research_TerranVehicleWeapons', 'arg': [], 
     'func': [(423, F.Research_TerranVehicleWeapons_quick, ('queued'))]},
    {'name': 'Research_TerranShipWeapons', 'arg': [], 
     'func': [(414, F.Research_TerranShipWeapons_quick, ('queued'))]},
    {'name': 'Research_TerranVehicleAndShipPlating', 'arg': [], 
     'func': [(419, F.Research_TerranVehicleAndShipPlating_quick, ('queued'))]},

    # Barracks Tech Lab
    {'name': 'Research_Stimpack', 'arg': [], 
     'func': [(405, F.Research_Stimpack_quick, ('queued'))]},
    {'name': 'Research_CombatShield', 'arg': [], 
     'func': [(361, F.Research_CombatShield_quick, ('queued'))]},
    {'name': 'Research_ConcussiveShells', 'arg': [], 
     'func': [(362, F.Research_ConcussiveShells_quick, ('queued'))]},

    # Factory Tech Lab
    {'name': 'Research_InfernalPreigniter', 'arg': [], 
     'func': [(371, F.Research_InfernalPreigniter_quick, ('queued'))]},
    {'name': 'Research_DrillingClaws', 'arg': [], 
     'func': [(363, F.Research_DrillingClaws_quick, ('queued'))]},
    {'name': 'Research_CycloneLockOnDamage', 'arg': [], 
     'func': [(570, F.Research_CycloneLockOnDamage_quick, ('queued'))]},
    {'name': 'Research_SmartServos', 'arg': [], 
     'func': [(373, F.Research_SmartServos_quick, ('queued'))]},

    # Starport Tech Lab
    {'name': 'Research_BansheeCloakingField', 'arg': [], 
     'func': [(353, F.Research_BansheeCloakingField_quick, ('queued'))]},
    {'name': 'Research_BansheeHyperflightRotors', 'arg': [], 
     'func': [(354, F.Research_BansheeHyperflightRotors_quick, ('queued'))]},
    {'name': 'Research_RavenCorvidReactor', 'arg': [], 
     'func': [(402, F.Research_RavenCorvidReactor_quick, ('queued'))]},
    {'name': 'Research_RavenRecalibratedExplosives', 'arg': [], 
     'func': [(403, F.Research_RavenRecalibratedExplosives_quick, ('queued'))]},

    # Ghost Academy
    {'name': 'Research_PersonalCloaking', 'arg': [], 
     'func': [(378, F.Research_PersonalCloaking_quick, ('queued'))]},

    # Fusion Core
    {'name': 'Research_BattlecruiserWeaponRefit', 'arg': [], 
     'func': [(355, F.Research_BattlecruiserWeaponRefit_quick, ('queued'))]},
]

# Building actions for Terran structures
TERRAN_ACTION_BUILD = [
    # Base structures
    {'name': 'Build_CommandCenter_Near', 'arg': ['tag'],
     'func': [(573, F.llm_pysc2_move_camera, ('world_tag')), 
              (44, F.Build_CommandCenter_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_CommandCenter_Screen', 'arg': ['screen'],
     'func': [(44, F.Build_CommandCenter_screen, ('queued', 'screen'))]},
    
    # Gas structure
    {'name': 'Build_Refinery_Near', 'arg': ['tag'],
     'func': [(79, F.Build_Refinery_screen, ('queued', 'screen_tag'))]},
    
    # Basic structures
    {'name': 'Build_SupplyDepot_Near', 'arg': ['tag'],
     'func': [(91, F.Build_SupplyDepot_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_SupplyDepot_Screen', 'arg': ['screen'],
     'func': [(91, F.Build_SupplyDepot_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_Barracks_Near', 'arg': ['tag'],
     'func': [(42, F.Build_Barracks_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_Barracks_Screen', 'arg': ['screen'],
     'func': [(42, F.Build_Barracks_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_EngineeringBay_Near', 'arg': ['tag'],
     'func': [(50, F.Build_EngineeringBay_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_EngineeringBay_Screen', 'arg': ['screen'],
     'func': [(50, F.Build_EngineeringBay_screen, ('queued', 'screen'))]},
    
    # Defense structures
    {'name': 'Build_Bunker_Near', 'arg': ['tag'],
     'func': [(43, F.Build_Bunker_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_Bunker_Screen', 'arg': ['screen'],
     'func': [(43, F.Build_Bunker_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_MissileTurret_Near', 'arg': ['tag'],
     'func': [(64, F.Build_MissileTurret_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_MissileTurret_Screen', 'arg': ['screen'],
     'func': [(64, F.Build_MissileTurret_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_SensorTower_Near', 'arg': ['tag'],
     'func': [(83, F.Build_SensorTower_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_SensorTower_Screen', 'arg': ['screen'],
     'func': [(83, F.Build_SensorTower_screen, ('queued', 'screen'))]},
    
    # Tech structures
    {'name': 'Build_GhostAcademy_Near', 'arg': ['tag'],
     'func': [(58, F.Build_GhostAcademy_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_GhostAcademy_Screen', 'arg': ['screen'],
     'func': [(58, F.Build_GhostAcademy_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_Factory_Near', 'arg': ['tag'],
     'func': [(53, F.Build_Factory_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_Factory_Screen', 'arg': ['screen'],
     'func': [(53, F.Build_Factory_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_Starport_Near', 'arg': ['tag'],
     'func': [(89, F.Build_Starport_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_Starport_Screen', 'arg': ['screen'],
     'func': [(89, F.Build_Starport_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_Armory_Near', 'arg': ['tag'],
     'func': [(39, F.Build_Armory_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_Armory_Screen', 'arg': ['screen'],
     'func': [(39, F.Build_Armory_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_FusionCore_Near', 'arg': ['tag'],
     'func': [(56, F.Build_FusionCore_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_FusionCore_Screen', 'arg': ['screen'],
     'func': [(56, F.Build_FusionCore_screen, ('queued', 'screen'))]},
    
    # Add-ons (these are built on the building, so need screen position)
    {'name': 'Build_Reactor_Screen', 'arg': ['screen'], 
     'func': [(72, F.Build_Reactor_screen, ('queued', 'screen'))]},
    {'name': 'Build_TechLab_Screen', 'arg': ['screen'], 
     'func': [(93, F.Build_TechLab_screen, ('queued', 'screen'))]},
]

# Unit abilities for Terran units
TERRAN_ACTION_ABILITY = [
    # SCV abilities
    {'name': 'Ability_Repair_Unit', 'arg': ['tag'],
     'func': [(220, F.Effect_Repair_screen, ('queued', 'screen_tag'))]},
    {'name': 'Ability_Repair_Autocast', 'arg': [],
     'func': [(221, F.Effect_Repair_autocast, ())]},
    
    # Marine/Marauder abilities
    {'name': 'Ability_Stim', 'arg': [],
     'func': [(234, F.Effect_Stim_quick, ('queued'))]},
    
    # Transport abilities
    {'name': 'Load_Unit', 'arg': ['tag'],
     'func': [(287, F.Load_screen, ('queued', 'screen_tag'))]},
    {'name': 'Load_Bunker', 'arg': ['tag'],
     'func': [(288, F.Load_Bunker_screen, ('queued', 'screen_tag'))]},
    {'name': 'Load_Medivac', 'arg': ['tag'],
     'func': [(289, F.Load_Medivac_screen, ('queued', 'screen_tag'))]},
    
    {'name': 'UnloadAll', 'arg': [],
     'func': [(511, F.UnloadAll_quick, ('queued'))]},
    {'name': 'UnloadAll_Bunker', 'arg': [],
     'func': [(512, F.UnloadAll_Bunker_quick, ('queued'))]},
    {'name': 'UnloadAll_CommandCenter', 'arg': [],
     'func': [(513, F.UnloadAll_CommandCenter_quick, ('queued'))]},
    
    {'name': 'UnloadAllAt_Screen', 'arg': ['screen'],
     'func': [(516, F.UnloadAllAt_screen, ('queued', 'screen'))]},
    {'name': 'UnloadAllAt_Minimap', 'arg': ['minimap'],
     'func': [(517, F.UnloadAllAt_minimap, ('queued', 'minimap'))]},
    {'name': 'UnloadAllAt_Medivac_Screen', 'arg': ['screen'],
     'func': [(518, F.UnloadAllAt_Medivac_screen, ('queued', 'screen'))]},
    {'name': 'UnloadAllAt_Medivac_Minimap', 'arg': ['minimap'],
     'func': [(519, F.UnloadAllAt_Medivac_minimap, ('queued', 'minimap'))]},

    # Command Center abilities
    {'name': 'Ability_CalldownMULE_Screen', 'arg': ['screen'],
     'func': [(183, F.Effect_CalldownMULE_screen, ('queued', 'screen'))]},
    {'name': 'Ability_CalldownMULE_Unit', 'arg': ['tag'],
     'func': [(183, F.Effect_CalldownMULE_screen, ('queued', 'screen_tag'))]},
    {'name': 'Ability_Scan_Screen', 'arg': ['screen'],
     'func': [(227, F.Effect_Scan_screen, ('queued', 'screen'))]},
    {'name': 'Ability_Scan_Minimap', 'arg': ['minimap'],
     'func': [(542, F.Effect_Scan_minimap, ('queued', 'minimap'))]},
    {'name': 'Ability_SupplyDrop_Unit', 'arg': ['tag'],
     'func': [(239, F.Effect_SupplyDrop_screen, ('queued', 'screen_tag'))]},
    
    # Command Center morphs
    {'name': 'Morph_OrbitalCommand', 'arg': [],
     'func': [(309, F.Morph_OrbitalCommand_quick, ('queued'))]},
    {'name': 'Morph_PlanetaryFortress', 'arg': [],
     'func': [(312, F.Morph_PlanetaryFortress_quick, ('queued'))]},

    # Building abilities
    {'name': 'Morph_SupplyDepot_Lower', 'arg': [],
     'func': [(318, F.Morph_SupplyDepot_Lower_quick, ('queued'))]},
    {'name': 'Morph_SupplyDepot_Raise', 'arg': [],
     'func': [(319, F.Morph_SupplyDepot_Raise_quick, ('queued'))]},
    
    {'name': 'Lift_Building', 'arg': [],
     'func': [(281, F.Lift_quick, ('queued'))]},
    {'name': 'Land_Building_Screen', 'arg': ['screen'],
     'func': [(275, F.Land_screen, ('queued', 'screen'))]},
    
    {'name': 'Ability_Salvage_Bunker', 'arg': [],
     'func': [(226, F.Effect_Salvage_quick, ('queued'))]},

    # Siege Tank
    {'name': 'Morph_SiegeMode', 'arg': [],
     'func': [(317, F.Morph_SiegeMode_quick, ('queued'))]},
    {'name': 'Morph_Unsiege', 'arg': [],
     'func': [(322, F.Morph_Unsiege_quick, ('queued'))]},
    
    # Viking
    {'name': 'Morph_VikingAssaultMode', 'arg': [],
     'func': [(326, F.Morph_VikingAssaultMode_quick, ('queued'))]},
    {'name': 'Morph_VikingFighterMode', 'arg': [],
     'func': [(327, F.Morph_VikingFighterMode_quick, ('queued'))]},
    
    # Hellion/Hellbat
    {'name': 'Morph_Hellion', 'arg': [],
     'func': [(301, F.Morph_Hellion_quick, ('queued'))]},
    {'name': 'Morph_Hellbat', 'arg': [],
     'func': [(300, F.Morph_Hellbat_quick, ('queued'))]},
    
    # Thor
    {'name': 'Morph_ThorHighImpactMode', 'arg': [],
     'func': [(321, F.Morph_ThorHighImpactMode_quick, ('queued'))]},
    {'name': 'Morph_ThorExplosiveMode', 'arg': [],
     'func': [(320, F.Morph_ThorExplosiveMode_quick, ('queued'))]},
    
    # Liberator
    {'name': 'Morph_LiberatorAGMode_Screen', 'arg': ['screen'],
     'func': [(305, F.Morph_LiberatorAGMode_screen, ('queued', 'screen'))]},
    {'name': 'Morph_LiberatorAGMode_Minimap', 'arg': ['minimap'],
     'func': [(554, F.Morph_LiberatorAGMode_minimap, ('queued', 'minimap'))]},
    {'name': 'Morph_LiberatorAAMode', 'arg': [],
     'func': [(304, F.Morph_LiberatorAAMode_quick, ('queued'))]},

    # Ghost abilities
    {'name': 'Ability_GhostSnipe', 'arg': ['tag'],
     'func': [(195, F.Effect_GhostSnipe_screen, ('queued', 'screen_tag'))]},
    {'name': 'Ability_EMP_Screen', 'arg': ['screen'],
     'func': [(190, F.Effect_EMP_screen, ('queued', 'screen'))]},
    {'name': 'Ability_EMP_Unit', 'arg': ['tag'],
     'func': [(190, F.Effect_EMP_screen, ('queued', 'screen_tag'))]},
    {'name': 'Ability_NukeCalldown_Screen', 'arg': ['screen'],
     'func': [(213, F.Effect_NukeCalldown_screen, ('queued', 'screen'))]},
    {'name': 'Build_Nuke', 'arg': [],
     'func': [(66, F.Build_Nuke_quick, ('queued'))]},
    
    # Cloak abilities
    {'name': 'Behavior_CloakOn', 'arg': [],
     'func': [(26, F.Behavior_CloakOn_quick, ('queued'))]},
    {'name': 'Behavior_CloakOn_Banshee', 'arg': [],
     'func': [(27, F.Behavior_CloakOn_Banshee_quick, ('queued'))]},
    {'name': 'Behavior_CloakOn_Ghost', 'arg': [],
     'func': [(28, F.Behavior_CloakOn_Ghost_quick, ('queued'))]},
    {'name': 'Behavior_CloakOff', 'arg': [],
     'func': [(23, F.Behavior_CloakOff_quick, ('queued'))]},
    {'name': 'Behavior_CloakOff_Banshee', 'arg': [],
     'func': [(24, F.Behavior_CloakOff_Banshee_quick, ('queued'))]},
    {'name': 'Behavior_CloakOff_Ghost', 'arg': [],
     'func': [(25, F.Behavior_CloakOff_Ghost_quick, ('queued'))]},

    # Raven abilities
    {'name': 'Ability_RavenAutoTurret_Screen', 'arg': ['screen'],
     'func': [(178, F.Effect_AutoTurret_screen, ('queued', 'screen'))]},
    {'name': 'Ability_RavenAntiArmorMissile_Unit', 'arg': ['tag'],
     'func': [(526, F.Effect_AntiArmorMissile_screen, ('queued', 'screen_tag'))]},
    {'name': 'Ability_RavenInterferenceMatrix_Unit', 'arg': ['tag'],
     'func': [(528, F.Effect_InterferenceMatrix_screen, ('queued', 'screen_tag'))]},
    
    # Battlecruiser abilities
    {'name': 'Ability_YamatoGun_Unit', 'arg': ['tag'],
     'func': [(247, F.Effect_YamatoGun_screen, ('queued', 'screen_tag'))]},
    {'name': 'Ability_TacticalJump_Screen', 'arg': ['screen'],
     'func': [(240, F.Effect_TacticalJump_screen, ('queued', 'screen'))]},
    {'name': 'Ability_TacticalJump_Minimap', 'arg': ['minimap'],
     'func': [(553, F.Effect_TacticalJump_minimap, ('queued', 'minimap'))]},
    
    # Widow Mine
    {'name': 'BurrowDown_WidowMine', 'arg': [],
     'func': [(115, F.BurrowDown_WidowMine_quick, ('queued'))]},
    {'name': 'BurrowUp_WidowMine', 'arg': [],
     'func': [(137, F.BurrowUp_WidowMine_quick, ('queued'))]},
    {'name': 'Ability_WidowMineAttack_Autocast', 'arg': [],
     'func': [(246, F.Effect_WidowMineAttack_autocast, ())]},
    
    # Medivac
    {'name': 'Ability_MedivacIgniteAfterburners', 'arg': [],
     'func': [(211, F.Effect_MedivacIgniteAfterburners_quick, ('queued'))]},
    {'name': 'Ability_Heal_Autocast', 'arg': [],
     'func': [(199, F.Effect_Heal_autocast, ())]},
    
    # Cyclone
    {'name': 'Ability_LockOn_Unit', 'arg': ['tag'],
     'func': [(206, F.Effect_LockOn_screen, ('queued', 'screen_tag'))]},
    {'name': 'Ability_LockOn_Autocast', 'arg': [],
     'func': [(557, F.Effect_LockOn_autocast, ())]},
]

# standard action object
AN_ACTION = {'name': '', 'arg': [], 'func': []}

# actions for smac tasks, ACTION_SMAC for tasks that attack is enough
PROTOSS_BASIC_ACTION_SMAC = [
  {'name': 'Attack_Unit', 'arg': ['tag'],
   'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
  # {'name': 'Select_Unit_Attack_Unit', 'arg': ['tag', 'tag'],  # single unit control
  #  'func': [(3, F.select_rect, ('select', 'screen1_tag', 'screen2_tag')),
  #           (12, F.Attack_screen, ('queued', 'screen_tag2'))]},
]
# actions for smac tasks, ACTION_SMAC2 for those moving is indispensable
PROTOSS_BASIC_ACTION_SMAC2 = [
  {'name': 'Attack_Unit', 'arg': ['tag'],
   'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
  {'name': 'Move_Screen', 'arg': ['screen'],
   'func': [(331, F.Move_screen, ('queued', 'screen'))]},
  # {'name': 'Select_Unit_Attack_Unit', 'arg': ['tag', 'tag'],  # single unit control
  #  'func': [(3, F.select_rect, ('select', 'screen1_tag', 'screen2_tag')),
  #           (12, F.Attack_screen, ('queued', 'screen_tag2'))]},
  # {'name': 'Select_Unit_Move_Screen', 'arg': ['tag', 'screen'],  # single unit control
  #  'func': [(3, F.select_rect, ('select', 'screen1_tag', 'screen2_tag')),
  #           (331, F.Move_screen, ('queued', 'screen'))]},
]
# actions for sc2 unit, 1 for buildings
PROTOSS_BASIC_ACTION_1 = [
  {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]},
  {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
  {'name': 'Stop_Building', 'arg': [], 'func': [(454, F.Stop_Building_quick, ('queued'))]},
  # {'name': 'Stop_Building_Unit',  'arg': ['tag'],
  #  'func': [(573, F.llm_pysc2_move_camera, ('world_tag')),
  #           (3, F.select_rect, ('select', 'screen1_tag', 'screen2_tag')),
  #           (454, F.Stop_Building_quick, ('queued'))]},
]
# actions for sc2 unit, 2 for units capable of launching attacks
PROTOSS_BASIC_ACTION_2 = [
  {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]},
  {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
  {'name': 'Hold_Position',   'arg': [],  'func': [(274, F.HoldPosition_quick, ('queued'))]},
  {'name': 'Move_Minimap', 'arg': ['minimap'], 'func': [(332, F.Move_minimap, ('queued', 'minimap'))]},
  {'name': 'Move_Screen', 'arg': ['screen'], 'func': [(331, F.Move_screen, ('queued', 'screen'))]},
  {'name': 'Attack_Unit', 'arg': ['tag'], 'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
  # {'name': 'Attack_Screen',   'arg': ['screen'],  'func': [(12, F.Attack_screen, ('queued', 'screen'))]},
  # {'name': 'Board_WarpPrism', 'arg': ['screen'],  'func': [(331, F.Move_screen, ('queued', 'screen_tag'))]},
]
# actions for sc2 unit, 3 for those unable to attack
PROTOSS_BASIC_ACTION_3 = [
  {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]},
  {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
  {'name': 'Hold_Position',   'arg': [],  'func': [(274, F.HoldPosition_quick, ('queued'))]},
  {'name': 'Move_Minimap', 'arg': ['minimap'], 'func': [(332, F.Move_minimap, ('queued', 'minimap'))]},
  {'name': 'Move_Screen', 'arg': ['screen'], 'func': [(331, F.Move_screen, ('queued', 'screen'))]},
  # {'name': 'Board_WarpPrism', 'arg': ['screen'],  'func': [(331, F.Move_screen, ('queued', 'screen_tag'))]},
]
# WarpTrain of protoss WarpGates
PROTOSS_ACTION_WARPTRAIN = [
  {'name': 'Warp_Adept_Near', 'arg': ['tag'],
   'func': [(8, F.select_warp_gates, ('select')), (573, F.llm_pysc2_move_camera, ('world_tag')),
            (505, F.TrainWarp_Adept_screen, ('queued', 'screen_tag'))]},  # tag for WarpprismPhasing/Pylon
  {'name': 'Warp_DarkTemplar_Near', 'arg': ['tag'],
   'func': [(8, F.select_warp_gates, ('select')), (573, F.llm_pysc2_move_camera, ('world_tag')),
            (506, F.TrainWarp_DarkTemplar_screen, ('queued', 'screen_tag'))]},  # tag for WarpprismPhasing/Pylon
  {'name': 'Warp_HighTemplar_Near', 'arg': ['tag'],
   'func': [(8, F.select_warp_gates, ('select')), (573, F.llm_pysc2_move_camera, ('world_tag')),
            (507, F.TrainWarp_HighTemplar_screen, ('queued', 'screen_tag'))]},  # tag for WarpprismPhasing/Pylon
  {'name': 'Warp_Sentry_Near', 'arg': ['tag'],
   'func': [(8, F.select_warp_gates, ('select')), (573, F.llm_pysc2_move_camera, ('world_tag')),
            (508, F.TrainWarp_Sentry_screen, ('queued', 'screen_tag'))]},  # tag for WarpprismPhasing/Pylon
  {'name': 'Warp_Stalker_Near', 'arg': ['tag'],
   'func': [(8, F.select_warp_gates, ('select')), (573, F.llm_pysc2_move_camera, ('world_tag')),
            (509, F.TrainWarp_Stalker_screen, ('queued', 'screen_tag'))]},  # tag for WarpprismPhasing/Pylon
  {'name': 'Warp_Zealot_Near', 'arg': ['tag'],
   'func': [(8, F.select_warp_gates, ('select')), (573, F.llm_pysc2_move_camera, ('world_tag')),
            (510, F.TrainWarp_Zealot_screen, ('queued', 'screen_tag')),
            (510, F.TrainWarp_Zealot_screen, ('queued', 'screen_tag')),
            (510, F.TrainWarp_Zealot_screen, ('queued', 'screen_tag')),
            (510, F.TrainWarp_Zealot_screen, ('queued', 'screen_tag')),]},  # tag for WarpprismPhasing/Pylon
  # {'name': 'Warp_One_Adept_Screen', 'arg': ['screen'],
  #  'func': [(8, F.select_warp_gates, ('select')), (505, F.TrainWarp_Adept_screen, ('queued', 'screen'))]},
  # {'name': 'Warp_One_DarkTemplar_Screen', 'arg': ['screen'],
  #  'func': [(8, F.select_warp_gates, ('select')), (506, F.TrainWarp_DarkTemplar_screen, ('queued', 'screen'))]},
  # {'name': 'Warp_One_HighTemplar_Screen', 'arg': ['screen'],
  #  'func': [(8, F.select_warp_gates, ('select')), (507, F.TrainWarp_HighTemplar_screen, ('queued', 'screen'))]},
  # {'name': 'Warp_One_Sentry_Screen', 'arg': ['screen'],
  #  'func': [(8, F.select_warp_gates, ('select')), (508, F.TrainWarp_Sentry_screen, ('queued', 'screen'))]},
  # {'name': 'Warp_One_Stalker_Screen', 'arg': ['screen'],
  #  'func': [(8, F.select_warp_gates, ('select')), (509, F.TrainWarp_Stalker_screen, ('queued', 'screen'))]},
  # {'name': 'Warp_One_Zealot_Screen', 'arg': ['screen'],
  #  'func': [(8, F.select_warp_gates, ('select')), (510, F.TrainWarp_Zealot_screen, ('queued', 'screen'))]},
]
# Idle production buildings will be automatically selected by LLMAgent._add_func_for_train_and_research()
PROTOSS_ACTION_TRAIN = [
  # Nexus, BN
  {'name': 'Train_Mothership', 'arg': [], 'func': [(541, F.Train_Mothership_quick, ('queued'))]},
  # GateWay BG
  {'name': 'Train_Adept', 'arg': [], 'func': [(457, F.Train_Adept_quick, ('queued'))]},
  {'name': 'Train_DarkTemplar', 'arg': [], 'func': [(465, F.Train_DarkTemplar_quick, ('queued'))]},
  {'name': 'Train_HighTemplar', 'arg': [], 'func': [(471, F.Train_HighTemplar_quick, ('queued'))]},
  {'name': 'Train_Sentry', 'arg': [], 'func': [(491, F.Train_Sentry_quick, ('queued'))]},
  {'name': 'Train_Stalker', 'arg': [], 'func': [(493, F.Train_Stalker_quick, ('queued'))]},
  {'name': 'Train_Zealot', 'arg': [], 'func': [(503, F.Train_Zealot_quick, ('queued'))]},
  # StarGate VS
  {'name': 'Train_Oracle', 'arg': [], 'func': [(482, F.Train_Oracle_quick, ('queued'))]},
  {'name': 'Train_Phoenix', 'arg': [], 'func': [(484, F.Train_Phoenix_quick, ('queued'))]},
  {'name': 'Train_VoidRay', 'arg': [], 'func': [(500, F.Train_VoidRay_quick, ('queued'))]},
  {'name': 'Train_Tempest', 'arg': [], 'func': [(495, F.Train_Tempest_quick, ('queued'))]},
  {'name': 'Train_Carrier', 'arg': [], 'func': [(461, F.Train_Carrier_quick, ('queued'))]},
  # RoboticFacility VR
  {'name': 'Train_Observer', 'arg': [], 'func': [(481, F.Train_Observer_quick, ('queued'))]},
  {'name': 'Train_WarpPrism', 'arg': [], 'func': [(501, F.Train_WarpPrism_quick, ('queued'))]},
  {'name': 'Train_Immortal', 'arg': [], 'func': [(473, F.Train_Immortal_quick, ('queued'))]},
  {'name': 'Train_Colossus', 'arg': [], 'func': [(462, F.Train_Colossus_quick, ('queued'))]},
  {'name': 'Train_Disruptor', 'arg': [], 'func': [(466, F.Train_Disruptor_quick, ('queued'))]},
]
# Idle technology buildings will be automatically selected by LLMAgent._add_func_for_train_and_research()
PROTOSS_ACTION_RESEARCH = [
  # CyberneticsCore BY
  {'name': 'Research_ProtossAirArmor', 'arg': [],
   'func': [(381, F.Research_ProtossAirArmor_quick, ('queued'))]},
  {'name': 'Research_ProtossAirWeapons', 'arg': [],
   'func': [(385, F.Research_ProtossAirWeapons_quick, ('queued'))]},
  {'name': 'Research_WarpGate', 'arg': [],
   'func': [(428, F.Research_WarpGate_quick, ('queued'))]},
  # Forge BF
  {'name': 'Research_ProtossGroundArmor', 'arg': [],
   'func': [(389, F.Research_ProtossGroundArmor_quick, ('queued'))]},
  {'name': 'Research_ProtossGroundWeapons', 'arg': [],
   'func': [(393, F.Research_ProtossGroundWeapons_quick, ('queued'))]},
  {'name': 'Research_ProtossShields', 'arg': [],
   'func': [(397, F.Research_ProtossShields_quick, ('queued'))]},
  # TwilightCouncil VC
  {'name': 'Research_Charge', 'arg': [],
   'func': [(359, F.Research_Charge_quick, ('queued'))]},
  {'name': 'Research_Blink', 'arg': [],
   'func': [(356, F.Research_Blink_quick, ('queued'))]},
  {'name': 'Research_AdeptResonatingGlaives', 'arg': [],
   'func': [(351, F.Research_AdeptResonatingGlaives_quick, ('queued'))]},
  # FleetBeacon VF (Void ray upgrade and Tempest upgrade are not realised in pysc2)
  {'name': 'Research_PhoenixAnionPulseCrystals', 'arg': [],
   'func': [(379, F.Research_PhoenixAnionPulseCrystals_quick, ('queued'))]},
  # RoboticsBay VB
  {'name': 'Research_ExtendedThermalLance', 'arg': [],
   'func': [(364, F.Research_ExtendedThermalLance_quick, ('queued'))]},
  {'name': 'Research_GraviticBooster', 'arg': [],
   'func': [(366, F.Research_GraviticBooster_quick, ('queued'))]},
  {'name': 'Research_GraviticDrive', 'arg': [],
   'func': [(367, F.Research_GraviticDrive_quick, ('queued'))]},
  # TemplarArchive VT
  {'name': 'Research_PsiStorm', 'arg': [],
   'func': [(401, F.Research_PsiStorm_quick, ('queued'))]},
  # DarkShrine VD
  {'name': 'Research_ShadowStrike', 'arg': [],
   'func': [(404, F.Research_ShadowStrike_quick, ('queued'))]},
]
# Standard build actions
PROTOSS_ACTION_BUILD = [
  # tag for Vespene Geyser
  {'name': 'Build_Nexus_Near', 'arg': ['tag'],
   'func': [(573, F.llm_pysc2_move_camera, ('world_tag')), (65, F.Build_Nexus_screen, ('queued', 'screen_tag'))]},
  # tag for Vespene Geyser
  {'name': 'Build_Assimilator_Near', 'arg': ['tag'],
   'func': [(40, F.Build_Assimilator_screen, ('queued', 'screen_tag'))]},
  {'name': 'Build_Nexus_Screen', 'arg': ['screen'],
   'func': [(65, F.Build_Nexus_screen, ('queued', 'screen'))]},
  {'name': 'Build_Assimilator_Screen', 'arg': ['screen'],
   'func': [(40, F.Build_Assimilator_screen, ('queued', 'screen'))]},
  {'name': 'Build_Pylon_Screen', 'arg': ['screen'],
   'func': [(70, F.Build_Pylon_screen, ('queued', 'screen'))]},
  {'name': 'Build_Gateway_Screen', 'arg': ['screen'],
   'func': [(57, F.Build_Gateway_screen, ('queued', 'screen'))]},
  {'name': 'Build_CyberneticsCore_Screen', 'arg': ['screen'],
   'func': [(48, F.Build_CyberneticsCore_screen, ('queued', 'screen'))]},
  {'name': 'Build_Forge_Screen', 'arg': ['screen'],
   'func': [(55, F.Build_Forge_screen, ('queued', 'screen'))]},
  {'name': 'Build_PhotonCannon_Screen', 'arg': ['screen'],
   'func': [(69, F.Build_PhotonCannon_screen, ('queued', 'screen'))]},
  {'name': 'Build_ShieldBattery_Screen', 'arg': ['screen'],
   'func': [(525, F.Build_ShieldBattery_screen, ('queued', 'screen'))]},
  {'name': 'Build_TwilightCouncil_Screen', 'arg': ['screen'],
   'func': [(101, F.Build_TwilightCouncil_screen, ('queued', 'screen'))]},
  {'name': 'Build_TemplarArchive_Screen', 'arg': ['screen'],
   'func': [(100, F.Build_TemplarArchive_screen, ('queued', 'screen'))]},
  {'name': 'Build_DarkShrine_Screen', 'arg': ['screen'],
   'func': [(49, F.Build_DarkShrine_screen, ('queued', 'screen'))]},
  {'name': 'Build_Stargate_Screen', 'arg': ['screen'],
   'func': [(88, F.Build_Stargate_screen, ('queued', 'screen'))]},
  {'name': 'Build_FleetBeacon_Screen', 'arg': ['screen'],
   'func': [(54, F.Build_FleetBeacon_screen, ('queued', 'screen'))]},
  {'name': 'Build_RoboticsBay_Screen', 'arg': ['screen'],
   'func': [(81, F.Build_RoboticsBay_screen, ('queued', 'screen'))]},
  {'name': 'Build_RoboticsFacility_Screen', 'arg': ['screen'],
   'func': [(82, F.Build_RoboticsFacility_screen, ('queued', 'screen'))]},
]
# Simplified build actions
PROTOSS_ACTION_EASY_BUILD = [
  # tag for Vespene Geyser
  {'name': 'Build_Nexus_Near', 'arg': ['tag'],
   'func': [(65, F.Build_Nexus_screen, ('queued', 'screen_tag'))]},
  # tag for Vespene Geyser
  {'name': 'Build_Assimilator_Near', 'arg': ['tag'],
   'func': [(40, F.Build_Assimilator_screen, ('queued', 'screen_tag'))]},
  # tag for WarpprismPhasing/Pylon
  {'name': 'Build_Pylon_Near', 'arg': ['tag'],
   'func': [(70, F.Build_Pylon_screen, ('queued', 'screen_tag'))]},
  {'name': 'Build_Gateway_Near', 'arg': ['tag'],
   'func': [(57, F.Build_Gateway_screen, ('queued', 'screen_tag'))]},
  {'name': 'Build_CyberneticsCore_Near', 'arg': ['tag'],
   'func': [(48, F.Build_CyberneticsCore_screen, ('queued', 'screen_tag'))]},
  {'name': 'Build_Forge_Near', 'arg': ['tag'],
   'func': [(55, F.Build_Forge_screen, ('queued', 'screen_tag'))]},
  {'name': 'Build_PhotonCannon_Near', 'arg': ['tag'],
   'func': [(69, F.Build_PhotonCannon_screen, ('queued', 'screen_tag'))]},
  {'name': 'Build_ShieldBattery_Near', 'arg': ['tag'],
   'func': [(525, F.Build_ShieldBattery_screen, ('queued', 'screen_tag'))]},
  {'name': 'Build_TwilightCouncil_Near', 'arg': ['tag'],
   'func': [(101, F.Build_TwilightCouncil_screen, ('queued', 'screen_tag'))]},
  {'name': 'Build_TemplarArchive_Near', 'arg': ['tag'],
   'func': [(100, F.Build_TemplarArchive_screen, ('queued', 'screen_tag'))]},
  {'name': 'Build_DarkShrine_Near', 'arg': ['tag'],
   'func': [(49, F.Build_DarkShrine_screen, ('queued', 'screen_tag'))]},
  {'name': 'Build_Stargate_Near', 'arg': ['tag'],
   'func': [(88, F.Build_Stargate_screen, ('queued', 'screen_tag'))]},
  {'name': 'Build_FleetBeacon_Near', 'arg': ['tag'],
   'func': [(54, F.Build_FleetBeacon_screen, ('queued', 'screen_tag'))]},
  {'name': 'Build_RoboticsBay_Near', 'arg': ['tag'],
   'func': [(81, F.Build_RoboticsBay_screen, ('queued', 'screen_tag'))]},
  {'name': 'Build_RoboticsFacility_Near', 'arg': ['tag'],
   'func': [(82, F.Build_RoboticsFacility_screen, ('queued', 'screen_tag'))]},
]
# Unit Abilities
PROTOSS_ACTION_ABILITY = [
  {'name': 'Morph_WarpPrismPhasingMode', 'arg': [],
   'func': [(329, F.Morph_WarpPrismPhasingMode_quick, ('queued'))]},
  {'name': 'Morph_WarpPrismTransportMode', 'arg': [],
   'func': [(330, F.Morph_WarpPrismTransportMode_quick, ('queued'))]},
  {'name': 'Morph_SurveillanceMode', 'arg': [],
   'func': [(538, F.Morph_SurveillanceMode_quick, ('queued'))]},
  {'name': 'Morph_ObserverMode', 'arg': [],
   'func': [(535, F.Morph_ObserverMode_quick, ('queued'))]},
  {'name': 'Morph_Archon', 'arg': [],
   'func': [(296, F.Morph_Archon_quick, ('queued'))]},
  {'name': 'Ability_PrismaticAlignment', 'arg': [],
   'func': [(244, F.Effect_VoidRayPrismaticAlignment_quick, ('queued'))]},
  {'name': 'Ability_CancelPhaseShift', 'arg': [],
   'func': [(453, F.Stop_quick, ('queued'))]},
  {'name': 'Ability_GuardianShield', 'arg': [],
   'func': [(197, F.Effect_GuardianShield_quick, ('queued'))]},
  {'name': 'Ability_PulsarBeamOn', 'arg': [],
   'func': [(38, F.Behavior_PulsarBeamOn_quick, ('queued'))]},
  {'name': 'Ability_ChronoBoost_Unit', 'arg': ['tag'],
   'func': [(573, F.llm_pysc2_move_camera, ('world_tag')), (527, F.Effect_ChronoBoostEnergyCost_screen, ('queued', 'screen_tag'))]},
  {'name': 'Ability_NexusMassRecall_Near', 'arg': ['tag'],
   'func': [(573, F.llm_pysc2_move_camera, ('world_tag')), (529, F.Effect_MassRecall_Nexus_screen, ('queued', 'screen_tag'))]},
  {'name': 'Ability_MothershipMassRecall_Near', 'arg': ['tag'],
   'func': [(573, F.llm_pysc2_move_camera, ('world_tag')), (208, F.Effect_MassRecall_screen, ('queued', 'screen_tag'))]},
  {'name': 'Ability_ShadowStride_Unit', 'arg': ['tag'],
   'func': [(182, F.Effect_ShadowStride_screen, ('queued', 'screen_tag'))]},
  {'name': 'Ability_GravitonBeam_Unit', 'arg': ['tag'],
   'func': [(196, F.Effect_GravitonBeam_screen, ('queued', 'screen_tag'))]},
  {'name': 'Ability_Blink_Screen', 'arg': ['screen'],
   'func': [(180, F.Effect_Blink_screen, ('queued', 'screen'))]},
  {'name': 'Ability_AdeptPhaseShift_Screen', 'arg': ['screen'],
   'func': [(177, F.Effect_AdeptPhaseShift_screen, ('queued', 'screen'))]},
  {'name': 'Ability_PsiStorm_Screen', 'arg': ['screen'],
   'func': [(218, F.Effect_PsiStorm_screen, ('queued', 'screen'))]},
  {'name': 'Ability_PurificationNova_Screen', 'arg': ['screen'],
   'func': [(219, F.Effect_PurificationNova_screen, ('queued', 'screen'))]},
  {'name': 'Ability_ForceField_Screen', 'arg': ['screen'],
   'func': [(193, F.Effect_ForceField_screen, ('queued', 'screen'))]},
  {'name': 'Ability_TimeWarp_Screen', 'arg': ['screen'],
   'func': [(241, F.Effect_TimeWarp_screen, ('queued', 'screen'))]},
  {'name': 'Ability_OracleRevelation_Screen', 'arg': ['screen'],
   'func': [(214, F.Effect_OracleRevelation_screen, ('queued', 'screen'))]},
  {'name': 'Ability_StasisTrap_Screen', 'arg': ['screen'],
   'func': [(90, F.Build_StasisTrap_screen, ('queued', 'screen'))]},
  {'name': 'Load_Unit', 'arg': ['tag'],
   'func': [(287, F.Load_screen, ('queued', 'screen_tag'))]},
  {'name': 'Unload_Screen', 'arg': ['screen'],
   'func': [(516, F.UnloadAllAt_screen, ('queued', 'screen'))]},
  {'name': 'Lock_Nexus_Near', 'arg': ['tag'],
   'func': [(70, F.Build_Pylon_screen, ('queued', 'screen_tag'))]},
  {'name': 'Lock_Assimilator_Near', 'arg': ['tag'],
   'func': [(40, F.Build_Assimilator_screen, ('queued', 'screen_tag'))]},
  {'name': 'Select_Unit_Blink_Screen', 'arg': ['tag', 'screen'],
   'func': [(3, F.select_rect, ('select', 'screen1_tag', 'screen2_tag')),
            (180, F.Effect_Blink_screen, ('queued', 'screen'))]},
  {'name': 'Hallucination_Adept', 'arg': [],
   'func': [(248, F.Hallucination_Adept_quick, ('queued'))]},
  {'name': 'Hallucination_Archon', 'arg': [],
   'func': [(249, F.Hallucination_Archon_quick, ('queued'))]},
  {'name': 'Hallucination_Colossus', 'arg': [],
   'func': [(250, F.Hallucination_Colossus_quick, ('queued'))]},
  {'name': 'Hallucination_Disruptor', 'arg': [],
   'func': [(251, F.Hallucination_Disruptor_quick, ('queued'))]},
  {'name': 'Hallucination_HighTemplar', 'arg': [],
   'func': [(252, F.Hallucination_HighTemplar_quick, ('queued'))]},
  {'name': 'Hallucination_Immortal', 'arg': [],
   'func': [(253, F.Hallucination_Immortal_quick, ('queued'))]},
  {'name': 'Hallucination_Oracle', 'arg': [],
   'func': [(254, F.Hallucination_Oracle_quick, ('queued'))]},
  {'name': 'Hallucination_Phoenix', 'arg': [],
   'func': [(255, F.Hallucination_Phoenix_quick, ('queued'))]},
  {'name': 'Hallucination_Probe', 'arg': [],
   'func': [(256, F.Hallucination_Probe_quick, ('queued'))]},
  {'name': 'Hallucination_Stalker', 'arg': [],
   'func': [(257, F.Hallucination_Stalker_quick, ('queued'))]},
  {'name': 'Hallucination_VoidRay', 'arg': [],
   'func': [(258, F.Hallucination_VoidRay_quick, ('queued'))]},
  {'name': 'Hallucination_WarpPrism', 'arg': [],
   'func': [(259, F.Hallucination_WarpPrism_quick, ('queued'))]},
  {'name': 'Hallucination_Zealot', 'arg': [],
   'func': [(260, F.Hallucination_Zealot_quick, ('queued'))]},
]
# # Basic Zerg actions for SMAC tasks where attack is sufficient
# ZERG_BASIC_ACTION_SMAC = [
#     {'name': 'Attack_Unit', 'arg': ['tag'],
#      'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
# ]

# # Basic Zerg actions for SMAC tasks where movement is required
# ZERG_BASIC_ACTION_SMAC2 = [
#     {'name': 'Attack_Unit', 'arg': ['tag'],
#      'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
#     {'name': 'Move_Screen', 'arg': ['screen'],
#      'func': [(331, F.Move_screen, ('queued', 'screen'))]},
# ]

# # Actions for Zerg buildings
# ZERG_BASIC_ACTION_1 = [
#     {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]},
#     {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
#     {'name': 'Stop_Building', 'arg': [], 'func': [(454, F.Stop_Building_quick, ('queued'))]},
# ]

# # Actions for Zerg combat units
# ZERG_BASIC_ACTION_2 = [
#     {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]},
#     {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
#     {'name': 'Hold_Position', 'arg': [], 'func': [(274, F.HoldPosition_quick, ('queued'))]},
#     {'name': 'Move_Minimap', 'arg': ['minimap'], 'func': [(332, F.Move_minimap, ('queued', 'minimap'))]},
#     {'name': 'Move_Screen', 'arg': ['screen'], 'func': [(331, F.Move_screen, ('queued', 'screen'))]},
#     {'name': 'Attack_Unit', 'arg': ['tag'], 'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
# ]

# # Actions for non-combat Zerg units
# ZERG_BASIC_ACTION_3 = [
#     {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]},
#     {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
#     {'name': 'Hold_Position', 'arg': [], 'func': [(274, F.HoldPosition_quick, ('queued'))]},
#     {'name': 'Move_Minimap', 'arg': ['minimap'], 'func': [(332, F.Move_minimap, ('queued', 'minimap'))]},
#     {'name': 'Move_Screen', 'arg': ['screen'], 'func': [(331, F.Move_screen, ('queued', 'screen'))]},
# ]


# # Training actions for Zerg production structures
# ZERG_ACTION_TRAIN = [
#     # Hatchery
#     {'name': 'Train_Drone', 'arg': [], 'func': [(467, F.Train_Drone_quick, ('queued'))]},
#     {'name': 'Train_Overlord', 'arg': [], 'func': [(483, F.Train_Overlord_quick, ('queued'))]},
#     {'name': 'Train_Zergling', 'arg': [], 'func': [(504, F.Train_Zergling_quick, ('queued'))]},
#     {'name': 'Train_Roach', 'arg': [], 'func': [(489, F.Train_Roach_quick, ('queued'))]},
#     {'name': 'Train_Hydralisk', 'arg': [], 'func': [(472, F.Train_Hydralisk_quick, ('queued'))]},
#     {'name': 'Train_Mutalisk', 'arg': [], 'func': [(480, F.Train_Mutalisk_quick, ('queued'))]},
#     {'name': 'Train_Corruptor', 'arg': [], 'func': [(463, F.Train_Corruptor_quick, ('queued'))]},
#     {'name': 'Train_Ultralisk', 'arg': [], 'func': [(497, F.Train_Ultralisk_quick, ('queued'))]},
#     {'name': 'Train_Baneling', 'arg': [], 'func': [(458, F.Train_Baneling_quick, ('queued'))]},
#     {'name': 'Train_Disruptor', 'arg': [], 'func': [(466, F.Train_Disruptor_quick, ('queued'))]},
#     {'name': 'Train_Infestor', 'arg': [], 'func': [(474, F.Train_Infestor_quick, ('queued'))]},
#     {'name': 'Train_Queen', 'arg': [], 'func': [(486, F.Train_Queen_quick, ('queued'))]},
#     {'name': 'Train_SwarmHost', 'arg': [], 'func': [(494, F.Train_SwarmHost_quick, ('queued'))]},
#     {'name': 'Train_Viper', 'arg': [], 'func': [(499, F.Train_Viper_quick, ('queued'))]},
# ]

# # Research actions for Zerg tech structures
# ZERG_ACTION_RESEARCH = [
#     {'name': 'Research_AdaptiveTalons', 'arg': [],'func': [(429, F.Research_AdaptiveTalons_quick, ('queued'))]},
#     {'name': 'Research_AnabolicSynthesis', 'arg': [],'func': [(429, F.Research_AnabolicSynthesis_quick, ('queued'))]},
#     {'name': 'Research_Burrow', 'arg': [],'func': [(429, F.Research_Burrow_quick, ('queued'))]},
#     {'name': 'Research_CentrifugalHooks', 'arg': [],'func': [(429, F.Research_CentrifugalHooks_quick, ('queued'))]},
#     {'name': 'Research_DrillingClaws', 'arg': [],'func': [(429, F.Research_DrillingClaws_quick, ('queued'))]},
#     {'name': 'Research_GlialRegeneration', 'arg': [],'func': [(429, F.Research_GlialRegeneration_quick, ('queued'))]},
#     {'name': 'Research_GroovedSpines', 'arg': [],'func': [(429, F.Research_GroovedSpines_quick, ('queued'))]},
#     {'name': 'Research_MuscularAugments', 'arg': [],'func': [(429, F.Research_MuscularAugments_quick, ('queued'))]},
#     {'name': 'Research_NeuralParasite', 'arg': ['screen'],'func': [(429, F.Research_NeuralParasite_quick, ('queued'))]},
#     {'name': 'Research_PathogenGlands', 'arg': [],'func': [(429, F.Research_PathogenGlands_quick, ('queued'))]},
#     {'name': 'Research_PneumatizedCarapace', 'arg': [],'func': [(429, F.Research_PneumatizedCarapace_quick, ('queued'))]},
#     {'name': 'Research_TunnelingClaws', 'arg': [],'func': [(429, F.Research_TunnelingClaws_quick, ('queued'))]},
#     {'name': 'Research_ZergFlyerArmor', 'arg': [],'func': [(429, F.Research_ZergFlyerArmor_quick, ('queued'))]},
#     {'name': 'Research_ZergFlyerAttack', 'arg': [],'func': [(429, F.Research_ZergFlyerAttack_quick, ('queued'))]},
#     {'name': 'Research_ZergGroundArmor', 'arg': [],'func': [(429, F.Research_ZergGroundArmor_quick, ('queued'))]},
#     {'name': 'Research_ZergMeleeWeapons', 'arg': [],'func': [(429, F.Research_ZergMeleeWeapons_quick, ('queued'))]},
#     {'name': 'Research_ZergMissileWeapons', 'arg': [],'func': [(429, F.Research_ZergMissileWeapons_quick, ('queued'))]},
#     {'name': 'Research_ZerglingAdrenalGlands', 'arg': [],'func': [(429, F.Research_ZerglingAdrenalGlands_quick, ('queued'))]},
#     {'name': 'Research_ZerglingMetabolicBoost', 'arg': [],'func': [(429, F.Research_ZerglingMetabolicBoost_quick, ('queued'))]},
# ]

# # Building actions for Zerg structures
# ZERG_ACTION_BUILD = [
#     {'name': 'Build_Hatchery_Screen', 'arg': ['screen'],
#      'func': [(59, F.Build_Hatchery_screen, ('queued', 'screen'))]},
#     {'name': 'Build_Extractor_Screen', 'arg': ['screen'],
#      'func': [(52, F.Build_Extractor_screen, ('queued', 'screen'))]},
#     {'name': 'Build_SpawningPool_Screen', 'arg': ['screen'],
#      'func': [(84, F.Build_SpawningPool_screen, ('queued', 'screen'))]},
#     {'name': 'Build_RoachWarren_Screen', 'arg': ['screen'],
#      'func': [(80, F.Build_RoachWarren_screen, ('queued', 'screen'))]},
#     {'name': 'Build_HydraliskDen_Screen', 'arg': ['screen'],
#      'func': [(60, F.Build_HydraliskDen_screen, ('queued', 'screen'))]},
#     {'name': 'Build_Spire_Screen', 'arg': ['screen'],
#      'func': [(86, F.Build_Spire_screen, ('queued', 'screen'))]}, 
#     {'name': 'Build_InfestationPit_Screen', 'arg': ['screen'],
#      'func': [(61, F.Build_InfestationPit_screen, ('queued', 'screen'))]},
#     {'name': 'Build_UltraliskCavern_Screen', 'arg': ['screen'],
#      'func': [(102, F.Build_UltraliskCavern_screen, ('queued', 'screen'))]},
#     {'name': 'Build_BanelingNest_screen', 'arg': ['screen'],
#      'func': [(41, F.Build_BanelingNest_screen, ('queued', 'screen'))]},
#     {'name': 'Build_CreepTumor_screen', 'arg': ['screen'],
#      'func': [(45, F.Build_CreepTumor_screen, ('queued', 'screen'))]},
#     {'name': 'Build_EvolutionChamber_screen', 'arg': ['screen'],
#      'func': [(51, F.Build_EvolutionChamber_screen, ('queued', 'screen'))]},
#     {'name': 'Build_LurkerDen_screen', 'arg': ['screen'],
#      'func': [(524, F.Build_LurkerDen_screen, ('queued', 'screen'))]},
#     {'name': 'Build_NydusNetwork_screen', 'arg': ['screen'],
#      'func': [(67, F.Build_NydusNetwork_screen, ('queued', 'screen'))]},
#     {'name': 'Build_NydusWorm_screen', 'arg': ['screen'],
#      'func': [(68, F.Build_NydusWorm_screen, ('queued', 'screen'))]},
#     {'name': 'Build_SpineCrawler_screen', 'arg': ['screen'],
#      'func': [(85, F.Build_SpineCrawler_screen, ('queued', 'screen'))]},
#     {'name': 'Build_SporeCrawler_screen', 'arg': ['screen'],
#      'func': [(87, F.Build_SporeCrawler_screen, ('queued', 'screen'))]},
# ]

# # Unit abilities for Zerg units
# ZERG_ACTION_ABILITY = [
#     {'name': 'Ability_InjectLarva', 'arg': ['tag'],'func': [(204, F.llm_pysc2_move_camera, ('world_tag')), (527, F.Effect_InjectLarva_screen, ('queued', 'screen_tag'))]},
#     {'name': 'Ability_BurrowDown', 'arg': [],'func': [(103, F.BurrowDown_quick, ('queued'))]},
#     {'name': 'Ability_CausticSpray', 'arg': [],'func': [(184, F.Effect_CausticSpray_screen, ('queued'))]},
#     {'name': 'Ability_Contaminate', 'arg': [],'func': [(188, F.Effect_Contaminate_screen, ('queued'))]},
#     {'name': 'Ability_CorrosiveBile', 'arg': [],'func': [(189, F.Effect_CorrosiveBile_screen, ('queued'))]},
#     {'name': 'Ability_Explode', 'arg': [],'func': [(191, F.Effect_Explode_quick, ('queued'))]},
#     {'name': 'Ability_FungalGrowth', 'arg': [],'func': [(194, F.Effect_FungalGrowth_screen, ('queued'))]},
#     {'name': 'Ability_InfestedTerrans', 'arg': [],'func': [(203, F.Effect_InfestedTerrans_screen, ('queued'))]},
#     {'name': 'Ability_LocustSwoop', 'arg': [],'func': [(207, F.Effect_LocustSwoop_screen, ('queued'))]},
#     {'name': 'Ability_NeuralParasite', 'arg': [],'func': [(212, F.Effect_NeuralParasite_screen, ('queued'))]},
#     {'name': 'Ability_ParasiticBomb', 'arg': [],'func': [(215, F.Effect_ParasiticBomb_screen, ('queued'))]},
#     {'name': 'Ability_SpawnChangeling', 'arg': [],'func': [(228, F.Effect_SpawnChangeling_quick, ('queued'))]},
#     {'name': 'Ability_SpawnLocusts', 'arg': [],'func': [(229, F.Effect_SpawnLocusts_screen, ('queued'))]},
#     {'name': 'Ability_Transfusion', 'arg': [],'func': [(242, F.Effect_Transfusion_screen, ('queued'))]},
#     {'name': 'Ability_ViperConsume', 'arg': [],'func': [(243, F.Effect_ViperConsume_screen, ('queued'))]},
#     {'name': 'Morph_BroodLord', 'arg': [],'func': [(297, F.Morph_BroodLord_quick, ('queued'))]},
#     {'name': 'Morph_GreaterSpire', 'arg': [],'func': [(299, F.Morph_GreaterSpire_quick, ('queued'))]},
#     {'name': 'Morph_Hive', 'arg': [],'func': [(302, F.Morph_Hive_quick, ('queued'))]},
#     {'name': 'Morph_Lair', 'arg': [],'func': [(303, F.Morph_Lair_quick, ('queued'))]},
#     {'name': 'Morph_Lurker', 'arg': [],'func': [(306, F.Morph_Lurker_quick, ('queued'))]},
#     {'name': 'Morph_LurkerDen', 'arg': [],'func': [(307, F.Morph_LurkerDen_quick, ('queued'))]},
#     {'name': 'Morph_OverlordTransport', 'arg': [],'func': [(310, F.Morph_OverlordTransport_quick, ('queued'))]},
#     {'name': 'Morph_Overseer', 'arg': [],'func': [(311, F.Morph_Overseer_quick, ('queued'))]},
#     {'name': 'Morph_OverseerMode', 'arg': [],'func': [(536, F.Morph_OverseerMode_quick, ('queued'))]},
#     {'name': 'Morph_OversightMode', 'arg': [],'func': [(537, F.Morph_OversightMode_quick, ('queued'))]},
#     {'name': 'Morph_Ravager', 'arg': [],'func': [(313, F.Morph_Ravager_quick, ('queued'))]},
#     {'name': 'Morph_Root', 'arg': [],'func': [(314, F.Morph_Root_screen, ('queued'))]},
#     {'name': 'Morph_Uproot', 'arg': [],'func': [(323, F.Morph_Uproot_quick, ('queued'))]},
#     {'name': 'Ability_UnloadAllUnits', 'arg': [],'func': [(514, F.UnloadAll_NydusNetwork_quick, ('queued'))]},
#     {'name': 'Ability_LoadAnUnit', 'arg': ['tag'],'func': [(290, F.Load_NydusNetwork_screen, ('queued', 'screen_tag'))]},
#     {'name': 'Cancel_BuildInProgress', 'arg': [],'func': [(144, F.Cancel_BuildInProgress_quick, ('queued'))]},
# ]

# Basic Zerg actions for SMAC tasks where attack is sufficient
ZERG_BASIC_ACTION_SMAC = [
    {'name': 'Attack_Unit', 'arg': ['tag'],
     'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
]

# Basic Zerg actions for SMAC tasks where movement is required
ZERG_BASIC_ACTION_SMAC2 = [
    {'name': 'Attack_Unit', 'arg': ['tag'],
     'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
    {'name': 'Move_Screen', 'arg': ['screen'],
     'func': [(331, F.Move_screen, ('queued', 'screen'))]},
]

# Actions for Zerg buildings
ZERG_BASIC_ACTION_1 = [
    {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]},
    {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
    {'name': 'Stop_Building', 'arg': [], 'func': [(454, F.Stop_Building_quick, ('queued'))]},
]

# Actions for Zerg combat units
ZERG_BASIC_ACTION_2 = [
    {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]},
    {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
    {'name': 'Hold_Position', 'arg': [], 'func': [(274, F.HoldPosition_quick, ('queued'))]},
    {'name': 'Move_Minimap', 'arg': ['minimap'], 'func': [(332, F.Move_minimap, ('queued', 'minimap'))]},
    {'name': 'Move_Screen', 'arg': ['screen'], 'func': [(331, F.Move_screen, ('queued', 'screen'))]},
    {'name': 'Attack_Unit', 'arg': ['tag'], 'func': [(12, F.Attack_screen, ('queued', 'screen_tag'))]},
]

# Actions for non-combat Zerg units
ZERG_BASIC_ACTION_3 = [
    {'name': 'Stop', 'arg': [], 'func': [(453, F.Stop_quick, ('now'))]},
    {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]},
    {'name': 'Hold_Position', 'arg': [], 'func': [(274, F.HoldPosition_quick, ('queued'))]},
    {'name': 'Move_Minimap', 'arg': ['minimap'], 'func': [(332, F.Move_minimap, ('queued', 'minimap'))]},
    {'name': 'Move_Screen', 'arg': ['screen'], 'func': [(331, F.Move_screen, ('queued', 'screen'))]},
]

# Training actions for Zerg production structures
ZERG_ACTION_TRAIN = [
    # Hatchery/Lair/Hive
    {'name': 'Train_Drone', 'arg': [], 'func': [(467, F.Train_Drone_quick, ('queued'))]},
    {'name': 'Train_Overlord', 'arg': [], 'func': [(483, F.Train_Overlord_quick, ('queued'))]},
    {'name': 'Train_Queen', 'arg': [], 'func': [(486, F.Train_Queen_quick, ('queued'))]},
    
    # SpawningPool
    {'name': 'Train_Zergling', 'arg': [], 'func': [(504, F.Train_Zergling_quick, ('queued'))]},
    
    # BanelingNest
    {'name': 'Train_Baneling', 'arg': [], 'func': [(458, F.Train_Baneling_quick, ('queued'))]},
    
    # RoachWarren
    {'name': 'Train_Roach', 'arg': [], 'func': [(489, F.Train_Roach_quick, ('queued'))]},
    
    # HydraliskDen
    {'name': 'Train_Hydralisk', 'arg': [], 'func': [(472, F.Train_Hydralisk_quick, ('queued'))]},
    
    # InfestationPit
    {'name': 'Train_Infestor', 'arg': [], 'func': [(474, F.Train_Infestor_quick, ('queued'))]},
    {'name': 'Train_SwarmHost', 'arg': [], 'func': [(494, F.Train_SwarmHost_quick, ('queued'))]},
    
    # Spire/GreaterSpire
    {'name': 'Train_Mutalisk', 'arg': [], 'func': [(480, F.Train_Mutalisk_quick, ('queued'))]},
    {'name': 'Train_Corruptor', 'arg': [], 'func': [(463, F.Train_Corruptor_quick, ('queued'))]},
    {'name': 'Train_Viper', 'arg': [], 'func': [(499, F.Train_Viper_quick, ('queued'))]},
    
    # UltraliskCavern
    {'name': 'Train_Ultralisk', 'arg': [], 'func': [(497, F.Train_Ultralisk_quick, ('queued'))]},
]

# Research actions for Zerg tech structures
ZERG_ACTION_RESEARCH = [
    # SpawningPool
    {'name': 'Research_ZerglingMetabolicBoost', 'arg': [], 
     'func': [(450, F.Research_ZerglingMetabolicBoost_quick, ('queued'))]},
    {'name': 'Research_ZerglingAdrenalGlands', 'arg': [], 
     'func': [(449, F.Research_ZerglingAdrenalGlands_quick, ('queued'))]},
    
    # BanelingNest
    {'name': 'Research_CentrifugalHooks', 'arg': [], 
     'func': [(358, F.Research_CentrifugalHooks_quick, ('queued'))]},
    
    # RoachWarren
    {'name': 'Research_GlialRegeneration', 'arg': [], 
     'func': [(365, F.Research_GlialRegeneration_quick, ('queued'))]},
    {'name': 'Research_TunnelingClaws', 'arg': [], 
     'func': [(427, F.Research_TunnelingClaws_quick, ('queued'))]},
    
    # HydraliskDen
    {'name': 'Research_GroovedSpines', 'arg': [], 
     'func': [(368, F.Research_GroovedSpines_quick, ('queued'))]},
    {'name': 'Research_MuscularAugments', 'arg': [], 
     'func': [(374, F.Research_MuscularAugments_quick, ('queued'))]},
    
    # LurkerDen
    {'name': 'Research_AdaptiveTalons', 'arg': [], 
     'func': [(539, F.Research_AdaptiveTalons_quick, ('queued'))]},
    
    # InfestationPit
    {'name': 'Research_PathogenGlands', 'arg': [], 
     'func': [(377, F.Research_PathogenGlands_quick, ('queued'))]},
    {'name': 'Research_NeuralParasite', 'arg': [], 
     'func': [(376, F.Research_NeuralParasite_quick, ('queued'))]},
    
    # UltraliskCavern
    {'name': 'Research_ChitinousPlating', 'arg': [], 
     'func': [(360, F.Research_ChitinousPlating_quick, ('queued'))]},
    {'name': 'Research_AnabolicSynthesis', 'arg': [], 
     'func': [(569, F.Research_AnabolicSynthesis_quick, ('queued'))]},
    
    # Lair (requires Hatchery upgrade)
    {'name': 'Research_Burrow', 'arg': [], 
     'func': [(357, F.Research_Burrow_quick, ('queued'))]},
    {'name': 'Research_PneumatizedCarapace', 'arg': [], 
     'func': [(380, F.Research_PneumatizedCarapace_quick, ('queued'))]},
    
    # EvolutionChamber
    {'name': 'Research_ZergMeleeWeapons', 'arg': [], 
     'func': [(441, F.Research_ZergMeleeWeapons_quick, ('queued'))]},
    {'name': 'Research_ZergGroundArmor', 'arg': [], 
     'func': [(437, F.Research_ZergGroundArmor_quick, ('queued'))]},
    {'name': 'Research_ZergMissileWeapons', 'arg': [], 
     'func': [(445, F.Research_ZergMissileWeapons_quick, ('queued'))]},
    
    # Spire
    {'name': 'Research_ZergFlyerAttack', 'arg': [], 
     'func': [(433, F.Research_ZergFlyerAttack_quick, ('queued'))]},
    {'name': 'Research_ZergFlyerArmor', 'arg': [], 
     'func': [(429, F.Research_ZergFlyerArmor_quick, ('queued'))]},
]

# Building actions for Zerg structures
ZERG_ACTION_BUILD = [
    # Base structures
    {'name': 'Build_Hatchery_Near', 'arg': ['tag'],
     'func': [(573, F.llm_pysc2_move_camera, ('world_tag')),
              (59, F.Build_Hatchery_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_Hatchery_Screen', 'arg': ['screen'],
     'func': [(59, F.Build_Hatchery_screen, ('queued', 'screen'))]},
    
    # Gas structure - must be on geyser
    {'name': 'Build_Extractor_Near', 'arg': ['tag'],
     'func': [(52, F.Build_Extractor_screen, ('queued', 'screen_tag'))]},
    
    # Basic structures
    {'name': 'Build_SpawningPool_Near', 'arg': ['tag'],
     'func': [(84, F.Build_SpawningPool_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_SpawningPool_Screen', 'arg': ['screen'],
     'func': [(84, F.Build_SpawningPool_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_EvolutionChamber_Near', 'arg': ['tag'],
     'func': [(51, F.Build_EvolutionChamber_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_EvolutionChamber_Screen', 'arg': ['screen'],
     'func': [(51, F.Build_EvolutionChamber_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_RoachWarren_Near', 'arg': ['tag'],
     'func': [(80, F.Build_RoachWarren_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_RoachWarren_Screen', 'arg': ['screen'],
     'func': [(80, F.Build_RoachWarren_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_BanelingNest_Near', 'arg': ['tag'],
     'func': [(41, F.Build_BanelingNest_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_BanelingNest_Screen', 'arg': ['screen'],
     'func': [(41, F.Build_BanelingNest_screen, ('queued', 'screen'))]},
    
    # Lair tech structures
    {'name': 'Build_HydraliskDen_Near', 'arg': ['tag'],
     'func': [(60, F.Build_HydraliskDen_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_HydraliskDen_Screen', 'arg': ['screen'],
     'func': [(60, F.Build_HydraliskDen_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_LurkerDen_Near', 'arg': ['tag'],
     'func': [(524, F.Build_LurkerDen_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_LurkerDen_Screen', 'arg': ['screen'],
     'func': [(524, F.Build_LurkerDen_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_Spire_Near', 'arg': ['tag'],
     'func': [(86, F.Build_Spire_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_Spire_Screen', 'arg': ['screen'],
     'func': [(86, F.Build_Spire_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_InfestationPit_Near', 'arg': ['tag'],
     'func': [(61, F.Build_InfestationPit_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_InfestationPit_Screen', 'arg': ['screen'],
     'func': [(61, F.Build_InfestationPit_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_NydusNetwork_Near', 'arg': ['tag'],
     'func': [(67, F.Build_NydusNetwork_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_NydusNetwork_Screen', 'arg': ['screen'],
     'func': [(67, F.Build_NydusNetwork_screen, ('queued', 'screen'))]},
    
    # Hive tech structures
    {'name': 'Build_UltraliskCavern_Near', 'arg': ['tag'],
     'func': [(102, F.Build_UltraliskCavern_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_UltraliskCavern_Screen', 'arg': ['screen'],
     'func': [(102, F.Build_UltraliskCavern_screen, ('queued', 'screen'))]},
    
    # Defense structures
    {'name': 'Build_SpineCrawler_Near', 'arg': ['tag'],
     'func': [(85, F.Build_SpineCrawler_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_SpineCrawler_Screen', 'arg': ['screen'],
     'func': [(85, F.Build_SpineCrawler_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_SporeCrawler_Near', 'arg': ['tag'],
     'func': [(87, F.Build_SporeCrawler_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_SporeCrawler_Screen', 'arg': ['screen'],
     'func': [(87, F.Build_SporeCrawler_screen, ('queued', 'screen'))]},
    
    # Special structures
    {'name': 'Build_CreepTumor_Near', 'arg': ['tag'],
     'func': [(45, F.Build_CreepTumor_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_CreepTumor_Screen', 'arg': ['screen'],
     'func': [(45, F.Build_CreepTumor_screen, ('queued', 'screen'))]},
    
    {'name': 'Build_NydusWorm_Near', 'arg': ['tag'],
     'func': [(68, F.Build_NydusWorm_screen, ('queued', 'screen_tag'))]},
    {'name': 'Build_NydusWorm_Screen', 'arg': ['screen'],
     'func': [(68, F.Build_NydusWorm_screen, ('queued', 'screen'))]},
]

# Unit abilities for Zerg units
ZERG_ACTION_ABILITY = [
    # Queen abilities
    {'name': 'Ability_InjectLarva', 'arg': ['tag'],
     'func': [(573, F.llm_pysc2_move_camera, ('world_tag')),
              (204, F.Effect_InjectLarva_screen, ('queued', 'screen_tag'))]},
    
    {'name': 'Ability_Transfusion', 'arg': ['tag'],
     'func': [(242, F.Effect_Transfusion_screen, ('queued', 'screen_tag'))]},
    
    {'name': 'Build_CreepTumor_Screen', 'arg': ['screen'],
     'func': [(45, F.Build_CreepTumor_screen, ('queued', 'screen'))]},
    
    # Burrow abilities
    {'name': 'BurrowDown', 'arg': [],
     'func': [(103, F.BurrowDown_quick, ('queued'))]},
    
    {'name': 'BurrowDown_Zergling', 'arg': [],
     'func': [(116, F.BurrowDown_Zergling_quick, ('queued'))]},
    
    {'name': 'BurrowUp', 'arg': [],
     'func': [(117, F.BurrowUp_quick, ('queued'))]},
    
    {'name': 'BurrowUp_Zergling', 'arg': [],
     'func': [(138, F.BurrowUp_Zergling_quick, ('queued'))]},
    
    {'name': 'BurrowUp_autocast', 'arg': [],
     'func': [(118, F.BurrowUp_autocast, ())]},
    
    # Corruptor ability
    {'name': 'Ability_CausticSpray', 'arg': ['tag'],
     'func': [(184, F.Effect_CausticSpray_screen, ('queued', 'screen_tag'))]},
    
    # Overseer abilities
    {'name': 'Ability_Contaminate', 'arg': ['tag'],
     'func': [(188, F.Effect_Contaminate_screen, ('queued', 'screen_tag'))]},
    
    {'name': 'Ability_SpawnChangeling', 'arg': [],
     'func': [(228, F.Effect_SpawnChangeling_quick, ('queued'))]},
    
    # Ravager ability
    {'name': 'Ability_CorrosiveBile_Screen', 'arg': ['screen'],
     'func': [(189, F.Effect_CorrosiveBile_screen, ('queued', 'screen'))]},
    
    # Baneling ability
    {'name': 'Explode', 'arg': [],
     'func': [(191, F.Effect_Explode_quick, ('queued'))]},
    
    # Infestor abilities
    {'name': 'Ability_FungalGrowth_Screen', 'arg': ['screen'],
     'func': [(194, F.Effect_FungalGrowth_screen, ('queued', 'screen'))]},
    
    {'name': 'Ability_FungalGrowth_Unit', 'arg': ['tag'],
     'func': [(194, F.Effect_FungalGrowth_screen, ('queued', 'screen_tag'))]},
    
    {'name': 'Ability_InfestedTerrans_Screen', 'arg': ['screen'],
     'func': [(203, F.Effect_InfestedTerrans_screen, ('queued', 'screen'))]},
    
    {'name': 'Ability_NeuralParasite', 'arg': ['tag'],
     'func': [(212, F.Effect_NeuralParasite_screen, ('queued', 'screen_tag'))]},
    
    # SwarmHost abilities
    {'name': 'Ability_SpawnLocusts_Screen', 'arg': ['screen'],
     'func': [(229, F.Effect_SpawnLocusts_screen, ('queued', 'screen'))]},
    
    {'name': 'Ability_LocustSwoop_Screen', 'arg': ['screen'],
     'func': [(207, F.Effect_LocustSwoop_screen, ('queued', 'screen'))]},
    
    # Viper abilities
    {'name': 'Ability_ParasiticBomb', 'arg': ['tag'],
     'func': [(215, F.Effect_ParasiticBomb_screen, ('queued', 'screen_tag'))]},
    
    {'name': 'Ability_ViperConsume', 'arg': ['tag'],
     'func': [(243, F.Effect_ViperConsume_screen, ('queued', 'screen_tag'))]},
    
    {'name': 'Ability_AbductUnit', 'arg': ['tag'],
     'func': [(176, F.Effect_Abduct_screen, ('queued', 'screen_tag'))]},
    
    {'name': 'Ability_BlindingCloud_Screen', 'arg': ['screen'],
     'func': [(179, F.Effect_BlindingCloud_screen, ('queued', 'screen'))]},
    
    # Unit morphs
    {'name': 'Morph_BroodLord', 'arg': [],
     'func': [(297, F.Morph_BroodLord_quick, ('queued'))]},
    
    {'name': 'Morph_Lurker', 'arg': [],
     'func': [(306, F.Morph_Lurker_quick, ('queued'))]},
    
    {'name': 'Morph_Ravager', 'arg': [],
     'func': [(313, F.Morph_Ravager_quick, ('queued'))]},
    
    {'name': 'Morph_Baneling', 'arg': [],
     'func': [(458, F.Train_Baneling_quick, ('queued'))]},
    
    # Building morphs
    {'name': 'Morph_Lair', 'arg': [],
     'func': [(303, F.Morph_Lair_quick, ('queued'))]},
    
    {'name': 'Morph_Hive', 'arg': [],
     'func': [(302, F.Morph_Hive_quick, ('queued'))]},
    
    {'name': 'Morph_GreaterSpire', 'arg': [],
     'func': [(299, F.Morph_GreaterSpire_quick, ('queued'))]},
    
    {'name': 'Morph_LurkerDen', 'arg': [],
     'func': [(307, F.Morph_LurkerDen_quick, ('queued'))]},
    
    # Overlord morphs
    {'name': 'Morph_Overseer', 'arg': [],
     'func': [(311, F.Morph_Overseer_quick, ('queued'))]},
    
    {'name': 'Morph_OverlordTransport', 'arg': [],
     'func': [(310, F.Morph_OverlordTransport_quick, ('queued'))]},
    
    # Overseer modes
    {'name': 'Morph_OverseerMode', 'arg': [],
     'func': [(536, F.Morph_OverseerMode_quick, ('queued'))]},
    
    {'name': 'Morph_OversightMode', 'arg': [],
     'func': [(537, F.Morph_OversightMode_quick, ('queued'))]},
    
    # Spine/Spore Crawler abilities
    {'name': 'Morph_SpineCrawlerRoot_Screen', 'arg': ['screen'],
     'func': [(314, F.Morph_Root_screen, ('queued', 'screen'))]},
    
    {'name': 'Morph_SporeCrawlerRoot_Screen', 'arg': ['screen'],
     'func': [(314, F.Morph_Root_screen, ('queued', 'screen'))]},
    
    {'name': 'Morph_SpineCrawlerUproot', 'arg': [],
     'func': [(323, F.Morph_Uproot_quick, ('queued'))]},
    
    {'name': 'Morph_SporeCrawlerUproot', 'arg': [],
     'func': [(323, F.Morph_Uproot_quick, ('queued'))]},
    
    # Transport abilities
    {'name': 'Load_Unit', 'arg': ['tag'],
     'func': [(287, F.Load_screen, ('queued', 'screen_tag'))]},
    
    {'name': 'UnloadAll', 'arg': [],
     'func': [(511, F.UnloadAll_quick, ('queued'))]},
    
    {'name': 'UnloadAllAt_Screen', 'arg': ['screen'],
     'func': [(516, F.UnloadAllAt_screen, ('queued', 'screen'))]},
    
    {'name': 'UnloadAll_NydusWorm_quick', 'arg': [],
      'func': [(515, F.UnloadAll_NydusWorm_quick, ('queued'))]},
    
    {'name': 'UnloadAllAt_Minimap', 'arg': ['minimap'],
     'func': [(517, F.UnloadAllAt_minimap, ('queued', 'minimap'))]},
    
    {'name': 'LoadAll', 'arg': [],
     'func': [(294, F.LoadAll_quick, ('queued'))]},
    
    {'name': 'Cancel_BuildInProgress', 'arg': [],
     'func': [(144, F.Cancel_BuildInProgress_quick, ('queued'))]},
    
    {'name': 'Cancel', 'arg': [],
     'func': [(140, F.Cancel_quick, ('queued'))]}
]

# The action tables above write each pysc2 function twice: as an id and as F.xxx. The id is what
# LLMAgent checks against obs.observation.available_actions, so a typo there silently disables an
# action (Ability_InjectLarva and Morph_Baneling had wrong ids). Trust the function object.
def normalize_function_ids(action_list):
  for action in action_list:
    action['func'] = [(int(t[1].id), t[1], t[2]) for t in action['func']]
  return action_list


for _name, _value in list(globals().items()):
  if _name.isupper() and isinstance(_value, list) and _value and isinstance(_value[0], dict) and 'func' in _value[0]:
    normalize_function_ids(_value)


# 目标类型查询函数，获取Research和Train所需的源单位类型
def find_unit_type_the_func_belongs_to(func_id, race):
  if race == 'protoss':
    if func_id in [541, 485]:
      return units.Protoss.Nexus
    if func_id in [457, 465, 471, 491, 493, 503]:
      return units.Protoss.Gateway
    if func_id in [482, 484, 500, 495, 461]:
      return units.Protoss.Stargate
    if func_id in [481, 501, 473, 462, 466]:
      return units.Protoss.RoboticsFacility
    if func_id in [381, 385, 428]:
      return units.Protoss.CyberneticsCore
    if func_id in [389, 393, 397]:
      return units.Protoss.Forge
    if func_id in [359, 356, 351]:
      return units.Protoss.TwilightCouncil
    if func_id in [379]:  # 缺失两个升级选项
      return units.Protoss.FleetBeacon
    if func_id in [364, 366, 367]:
      return units.Protoss.RoboticsBay
    if func_id in [401]:
      return units.Protoss.TemplarArchive
    if func_id in [404]:
      return units.Protoss.DarkShrine
  if race == 'zerg':
    if func_id in [528, 504]:
      return units.Zerg.Larva
  if race == 'terran':
    pass  # Support for Terran is undergoing
  return None


def find_building_size(build_name: str) -> int:
  if build_name in SIZE5_BUILDING_NAMES:  # Support for Terran/Zerg is undergoing
    return 5
  elif build_name in SIZE3_BUILDING_NAMES:  # Support for Terran/Zerg is undergoing
    return 3
  elif build_name in SIZE2_BUILDING_NAMES:  # Support for Terran/Zerg is undergoing
    return 2
  elif build_name in SIZE1_BUILDING_NAMES:  # Support for Terran/Zerg is undergoing
    return 1
  else:
    return 0


# Find idle unit tag, conditions: ours + reigh-type + already-built + not-active
def find_idle_unit_tag(obs, unit_type, queued_source_unit_tag_list):
  for unit in obs.observation.raw_units:
    if unit.alliance == features.PlayerRelative.SELF and unit.build_progress == 100 and unit.active == 0 \
        and unit_type is not None and unit.unit_type == unit_type and unit.tag not in queued_source_unit_tag_list:
      return unit.tag
  return None


# Parameter verification
def get_arg_minimap(obs, minimap: list, size_minimap, action_name) -> tuple[tuple, bool]:  # 小地图坐标，校验范围
  if isinstance(minimap, list) and len(minimap) == 2 and isinstance(minimap[0], (int, float)) and isinstance(minimap[1], (int, float)):
    x = min(max(0, minimap[0]), size_minimap)
    y = min(max(0, minimap[1]), size_minimap)
    if 'Attack' in action_name and obs.observation.feature_minimap.player_relative[x][y] in [1, 2]:
      return f'({x}, {y}) is alliance', False
    if 'Load' in action_name and obs.observation.feature_minimap.player_relative[x][y] not in [1, 2]:
      return f'({x}, {y}) is not alliance', False
    if 'Follow' in action_name and obs.observation.feature_minimap.player_relative[x][y] not in [1, 2]:
      return f'({x}, {y}) is not alliance', False
    return (x, y), True
  return f'minimap={minimap}, unknown error', False


# Parameter verification
def get_arg_screen(obs, screen: list, size_screen, action_name) -> tuple[tuple, bool]:  # 屏幕坐标，校验范围
  if isinstance(screen, list) and len(screen) == 2 and isinstance(screen[0], (int, float)) and isinstance(screen[1], (int, float)):
    x = int(min(max(0, screen[0]), size_screen))
    y = int(min(max(0, screen[1]), size_screen))
    if 'Attack' in action_name and obs.observation.feature_screen.player_relative[x][y] in [1, 2]:
      return f'({x}, {y}) is alliance', False
    if 'Load' in action_name and obs.observation.feature_screen.player_relative[x][y] not in [1, 2]:
      return f'({x}, {y}) is not alliance', False
    if 'Follow' in action_name and obs.observation.feature_screen.player_relative[x][y] not in [1, 2]:
      return f'({x}, {y}) is not alliance', False
    return (x, y), True
  return f'input arg {screen} error', False


# Parameter verification, for build
def get_arg_screen_build(obs, screen: list, size_screen, action_name) -> tuple[tuple, bool]:  # 标准建造，校验地点和建造条件
  building_name = action_name.split('Build_')[1].split('_Screen')[0]
  building_size = find_building_size(building_name)
  if isinstance(screen, list) and len(screen) == 2 and isinstance(screen[0], (int, float)) and isinstance(screen[1], (
  int, float)) and building_size != 0:
    ratio = int(size_screen / SCREEN_WORLD_GRID)
    x0 = int(min(max(0, screen[0]), size_screen))
    y0 = int(min(max(0, screen[1]), size_screen))
    x1 = int(min(max(0, screen[0]), size_screen) - ratio * (building_size - 1) / 2)
    y1 = int(min(max(0, screen[1]), size_screen) - ratio * (building_size - 1) / 2)
    if building_name in POWER_BUILDING_NAMES and obs.observation.feature_screen.power[x0][y0] == 0:
      return f'({x0}, {y0}) need power', False
    if building_name in CREEP_BUILDING_NAMES and obs.observation.feature_screen.creep[x0][y0] == 0:
      return f'({x0}, {y0}) need creep', False
    for i in range(building_size):
      for j in range(building_size):
        x = int(x1 + i * ratio)
        y = int(y1 + j * ratio)
        if not (0 < x < size_screen and 0 < y < size_screen):
          return f'({x0}, {y0}) too close to screen edge', False
        if obs.observation.feature_screen.buildable[x][y] != 1:
          return f'area near ({x0}, {y0}) not buildable', False
        if obs.observation.feature_screen.pathable[x][y] != 1:
          return f'area near ({x0}, {y0}) not pathable', False
        if obs.observation.feature_screen.player_relative[x][y] not in [0, 1]:
          return f'area near ({x0}, {y0}) not blocked', False
    return (x0, y0), True
  return f'input arg {screen} error', False


# Parameter verification, tag to world coordinate
def get_arg_world_tag(obs, tag: int, x_offset, y_offset, world_range) -> tuple[tuple, bool]:  # 获取指定tag单位的世界坐标
  for unit in obs.observation.raw_units:
    if unit.tag == tag:
      x = unit.x + x_offset
      y = max(0, world_range - unit.y + y_offset)
      return (x, y), True
  tag = hex(tag) if isinstance(tag, int) else tag
  return f'cannot find unit {tag}', False


# Parameter verification, tag to screen coordinate
def get_arg_screen_tag(obs, tag: int, size_screen, action_name) -> tuple[tuple, bool]:  # 获取指定tag单位的屏幕坐标
  for unit in obs.observation.feature_units:
    if unit.tag == tag:
      x, y = unit.x, unit.y
      if 'Attack' in action_name and unit.alliance in [1, 2]:
        return f'({x}, {y}) is alliance', False
      if 'Load' in action_name and unit.alliance not in [1]:
        return f'({x}, {y}) is not alliance', False
      if 'Follow' in action_name and unit.alliance not in [1, 2]:
        return f'({x}, {y}) is not alliance', False
      if 'MassRecall' in action_name and unit.alliance not in [1]:
        return f'({x}, {y}) is not alliance', False
      if 'Chrono_Boost' in action_name and (unit.alliance not in [1] or unit.unit_type not in BOOSTABLE_TYPE):
        return f'({x}, {y}) is not boostable', False
      if 'Board_' in action_name and (unit.alliance not in [1] or unit.unit_type not in TRANSPORTER_TYPE):
        return f'({x}, {y}) is not a transporter', False
      if unit.is_on_screen and (0 < unit.x < size_screen and 0 < unit.y < size_screen):
        return (unit.x, unit.y), True
  tag = hex(tag) if isinstance(tag, int) else tag
  return f'cannot find unit {tag} on screen', False


# Parameter verification, tag to rect screen coordinates
def get_arg_screen_tag_sclect_rect(obs, tag: int, size_screen, func_arg_name) -> tuple[tuple, bool]:  # 获取指定tag附近单位群的中心坐标
  for unit in obs.observation.feature_units:
    if unit.tag == tag:
      if unit.alliance not in [1]:
        return f'({unit.y}, {unit.y}) is not alliance', False
      if not (0 < unit.x < size_screen and 0 < unit.y < size_screen):
        return f'unit {tag} ({unit.x}, {unit.y}) not no screen', False
      if func_arg_name == 'screen' and unit.is_on_screen:
        x = max(0, min(int(unit.x - size_screen / 64), size_screen))
        y = max(0, min(int(unit.y - size_screen / 64), size_screen))
        return (x, y), True
      if func_arg_name == 'screen2' and unit.is_on_screen:
        x = max(0, min(int(unit.x + size_screen / 64), size_screen))
        y = max(0, min(int(unit.y + size_screen / 64), size_screen))
        return (x, y), True
  tag = hex(tag) if isinstance(tag, int) else tag
  return f'cannot find unit {tag} on screen', False


# Parameter verification, tag to screen coordinate, for recall
def get_arg_screen_tag_recall(obs, tag: int, size_screen, action_name) -> tuple[tuple, bool]:  # 获取指定tag附近单位群的中心坐标
  for unit in obs.observation.feature_units:
    if unit.tag == tag:
      x, y = unit.x, unit.y
      if unit.alliance not in [1]:
        return f'({x}, {y}) is not alliance', False
      if unit.is_on_screen and (0 < unit.x < size_screen and 0 < unit.y < size_screen):
        return (unit.x, unit.y), True
  tag = hex(tag) if isinstance(tag, int) else tag
  return f'cannot find unit {tag} on screen', False


# Parameter verification, tag to screen coordinate, for warp
def get_arg_screen_tag_warp(obs, tag: int, size_screen, action_name) -> tuple[tuple, bool]:  # 获取指定tag附近可折跃单位的坐标
  n = 0
  for unit in obs.observation.feature_units:
    max_try = 72
    if unit.tag == tag:
      if unit.unit_type not in [units.Protoss.Pylon, units.Protoss.WarpPrismPhasing]:
        return f'tag {unit.tag}({unit.unit_type}) is not Pylon(60) or WarpPrismPhasing(136)', False
      else:
        radius = [2, 3, 4, 5, 6] if unit.unit_type == units.Protoss.Pylon else [1, 2, 3]
        angles = [0, 45, 90, 135, 180, 225, 270, 315]
        while n < max_try:
          r = radius[random.randint(0, len(radius) - 1)]
          a = angles[random.randint(0, len(angles) - 1)]
          x = int(unit.x + r * (size_screen / SCREEN_WORLD_GRID) * math.cos(math.radians(a)))
          y = int(unit.y + r * (size_screen / SCREEN_WORLD_GRID) * math.sin(math.radians(a)))
          if (0 < x < size_screen and 0 < y < size_screen) and \
              obs.observation.feature_screen.power[x][y] == 1 and \
              obs.observation.feature_screen.pathable[x][y] == 1 and \
              obs.observation.feature_screen.unit_type[x][y] == 0 and \
              obs.observation.feature_screen.build_progress[x][y] == 0 and \
              obs.observation.feature_screen.unit_shields[x][y] == 0:
            return (x, y), True
          else:
            n = n + 1
  if n == 36:
    return f'cannot find valid position to warp unit', False
  tag = hex(tag) if isinstance(tag, int) else tag
  return f'cannot find unit {tag} on screen', False


# Parameter verification, tag to screen coordinate, for gas building
def get_arg_screen_tag_gas_building(obs, tag: int, size_screen, action_name) -> tuple[tuple, bool]:

  # find vesoene gesyer raw_unit
  unit_r = None
  for unit in obs.observation.raw_units:
    if unit.tag == tag:
      unit_r = unit
  if unit_r is None:
    tag = hex(tag) if isinstance(tag, int) else tag
    return f'cannot find unit {tag}', False
  # confirm if is possible to construct
  for unit in obs.observation.feature_units:
    if unit.tag == tag:
      base_nearby = False
      for unit_ in obs.observation.raw_units:
        if unit_.alliance == features.PlayerRelative.SELF and unit_.unit_type in BASE_BUILDING_TYPE and \
            math.sqrt((unit_.x - unit_r.x) ** 2 + (unit_.y - unit_r.y) ** 2) < 10:
          base_nearby = True
      if not base_nearby:
        return f'tag {unit.tag}({unit.unit_type}) is far away from our base building', False
      if unit.unit_type not in GAS_TYPE:
        return f'tag {unit.tag}({unit.unit_type}) is not VespeneGeyser(342 344 608 880 881)', False
      if unit.is_on_screen and (0 < unit.x < size_screen and 0 < unit.y < size_screen):
        return (unit.x, unit.y), True
  tag = hex(tag) if isinstance(tag, int) else tag
  return f'cannot find unit {tag} on screen', False


# Parameter verification, tag to screen coordinate, for base building
def get_arg_world_tag_base_building(obs, tag: int, x_offset, y_offset, world_range) -> tuple[tuple, bool]:

  def find_nearby_raw_mg(unit_g):
    nearby_resource_unit_dict = {}
    for unit in obs.observation.raw_units:
      if unit.unit_type in MINERAL_TYPE:
        dist = math.sqrt((unit.x - unit_g.x) ** 2 + (unit.y - unit_g.y) ** 2)
        if dist < 16:
          nearby_resource_unit_dict[dist] = unit
      if unit.unit_type in GAS_TYPE:
        dist = math.sqrt((unit.x - unit_g.x) ** 2 + (unit.y - unit_g.y) ** 2)
        if dist < 16:
          nearby_resource_unit_dict[dist] = unit
    return nearby_resource_unit_dict.values()

  def artificial_force_field_iteration_world(unit_list, x, y):
    k, r, m = 0.5, 7, 1
    vespene_r, vespene_m = 8, 1
    mineral_r, mineral_m = 7, 1
    n, bad_n, fx, fy = 0, 0, 0, 0
    for unit in unit_list:
      bad = False
      if unit.unit_type in GAS_TYPE:
        r, m = vespene_r, vespene_m
      if unit.unit_type in MINERAL_TYPE:
        r, m = mineral_r, mineral_m
      d = math.sqrt((unit.x - x) ** 2 + (unit.y - y) ** 2)
      f = k * (r - d) * m
      fx += f * (x - unit.x) / d
      fy += f * (y - unit.y) / d
      n += 1
      if unit.unit_type in GAS_TYPE and not (7 < d < 10):
        bad = True
      if unit.unit_type in MINERAL_TYPE and not (6 < d < 9):
        bad = True
      if bad:
        bad_n += 1
    return (x + fx / n), (y + fy / n), bad_n

  for unit in obs.observation.raw_units:
    if unit.tag == tag:
      if unit.unit_type not in GAS_TYPE + MINERAL_TYPE:
        return f'tag {unit.tag}({unit.unit_type}) is not VespeneGaser', False
      mineral_list = find_nearby_raw_mg(unit)
      n, x0, y0 = 0, 0, 0
      for mineral in mineral_list:
        n += 1
        x0 += mineral.x
        y0 += mineral.y
      x0 = x0 / n
      y0 = y0 / n
      for i in range(16):
        x0, y0, bad_n = artificial_force_field_iteration_world(mineral_list, x0, y0)
      x = int(x0 + x_offset)
      y = int(max(0, world_range - y0 + y_offset))
      return (x, y), True
  tag = hex(tag) if isinstance(tag, int) else tag
  return f'cannot find unit {tag} on screen', False


# Parameter verification, tag to screen coordinate, for base building
def get_arg_screen_tag_base_building(obs, tag: int, size_screen, action_name) -> tuple[tuple, bool]:
  def find_nearby_screen_mg(unit_g):
    ratio = size_screen / SCREEN_WORLD_GRID
    nearby_resource_unit_dict = {}
    for unit in obs.observation.feature_units:
      if unit.unit_type in MINERAL_TYPE:
        dist = math.sqrt((unit.x - unit_g.x) ** 2 + (unit.y - unit_g.y) ** 2)
        if dist < 16 * ratio:
          nearby_resource_unit_dict[dist] = unit
      if unit.unit_type in GAS_TYPE:
        dist = math.sqrt((unit.x - unit_g.x) ** 2 + (unit.y - unit_g.y) ** 2)
        if dist < 16 * ratio:
          nearby_resource_unit_dict[dist] = unit
    return nearby_resource_unit_dict.values()

  def artificial_force_field_iteration_screen(unit_list, x, y):
    ratio = size_screen / SCREEN_WORLD_GRID
    k, r, m = 0.5, 7 * ratio, 1
    vespene_r, vespene_m = 8 * ratio, 1
    mineral_r, mineral_m = 7 * ratio, 1
    n, bad_n, fx, fy = 0, 0, 0, 0
    for unit in unit_list:
      bad = False
      if unit.unit_type in GAS_TYPE:
        r, m = vespene_r, vespene_m
      if unit.unit_type in MINERAL_TYPE:
        r, m = mineral_r, mineral_m
      d = math.sqrt((unit.x - x) ** 2 + (unit.y - y) ** 2)
      f = k * (r - d) * m
      fx += f * (x - unit.x) / d
      fy += f * (y - unit.y) / d
      n += 1
      if unit.unit_type in GAS_TYPE and not (7 * ratio < d < 10 * ratio):
        bad = True
      if unit.unit_type in MINERAL_TYPE and not (6 * ratio < d < 9 * ratio):
        bad = True
      if bad:
        bad_n += 1
    return (x + fx / n), (y + fy / n), bad_n

  building_name = action_name.split('_Screen')[0].split('_')[1]  # Build/Lock
  building_size = find_building_size(building_name)
  for unit in obs.observation.feature_units:
    if unit.tag == tag or (unit.unit_type in GAS_TYPE + MINERAL_TYPE and unit.is_on_screen):
      if unit.unit_type not in GAS_TYPE + MINERAL_TYPE:
        return f'tag {unit.tag}({unit.unit_type}) is not VespeneGaser', False
      mineral_gas_list = find_nearby_screen_mg(unit)
      n, x0, y0 = 0, 0, 0
      for mineral in mineral_gas_list:
        n += 1
        x0 += mineral.x
        y0 += mineral.y
      x = x0 / n
      y = y0 / n
      bad_n = len(mineral_gas_list)
      for i in range(16):
        x, y, bad_n = artificial_force_field_iteration_screen(mineral_gas_list, x, y)
      x, y = int(x), int(y)
      if bad_n > 3:
        return f'({x}, {y}) may be a bad position for base building', False
      if not (0 < x < size_screen and 0 < y < size_screen):
        return f'({x}, {y}) too close to screen edge', False
      if obs.observation.feature_screen.buildable[x][y] != 1:
        return f'area near ({x}, {y}) not buildable', False
      if obs.observation.feature_screen.pathable[x][y] != 1:
        return f'area near ({x}, {y}) not pathable', False
      if obs.observation.feature_screen.player_relative[x][y] not in [0, 1]:
        return f'area near ({x}, {y}) not blocked', False
      if unit.is_on_screen and (0 < x < size_screen and 0 < y < size_screen):
        return (x, y), True
  tag = hex(tag) if isinstance(tag, int) else tag
  return f'cannot find unit {tag} on screen', False


# 补齐拖农民的前置函数
def add_func_for_select_workers(self, obs, action):

  action_name = action['name']
  action_arg = action['arg']
  action_func = action['func']
  if not ('Select_Workers_' in action_name):
    return action

  full_shape_action = None
  logger.debug(self.action_list)

  func_id, func, arg_type = action_func[0]
  source_unit_tag = None
  for unit in obs.observation.raw_units:
    if unit.alliance == features.PlayerRelative.SELF and unit.unit_type in WORKER_TYPE and \
        unit.is_on_screen and (0 < unit.x < self.size_screen and 0 < unit.y < self.size_screen):
      source_unit_tag = unit.tag
  if source_unit_tag is None:
    logger.error(
      f"[ID {self.log_id}] Agent {self.name}, Can not find source unit type for func {actions.FUNCTIONS[func_id].name}")
  else:
    logger.debug(f"[ID {self.log_id}] Agent {self.name}, find source unit worker {source_unit_tag}")

  if source_unit_tag is not None:
    full_shape_action = {'name': action_name, 'arg': [], 'func':
      [(2, actions.FUNCTIONS.select_point, ['select_all_type', int(source_unit_tag)])] + action['func']}
  else:
    full_shape_action = {'name': 'No_Operation', 'arg': [], 'func':
      [(0, actions.FUNCTIONS.no_op, {})]}

  return full_shape_action


# 补齐训练和升级的前置函数，移动相机到闲置建筑，并选择该建筑
def add_func_for_train_and_research(self, obs, action):
  # 该函数将train/research动作需要的move_camera和select动作补齐，
  #  补到self.text_func_list中，将它从单一的F.Train_xxx_quick/F.Research_xxx_quick变成三个动作

  action_name = action['name']
  action_arg = action['arg']
  action_func = action['func']
  if not ('Train_' in action_name or 'Research_' in action_name):
    return action

  full_shape_action = None
  queued_source_unit_tag_list = []  # 已经准备训练/升级单位的建筑，用于避免重复选中
  logger.debug(self.action_list)

  func_id, func, arg_type = action_func[0]
  source_unit_type = find_unit_type_the_func_belongs_to(func_id, self.race)
  source_unit_tag = find_idle_unit_tag(obs, source_unit_type, queued_source_unit_tag_list)

  if source_unit_type is None:
    logger.error(
      f"[ID {self.log_id}] Agent {self.name}, Can not find source unit type for func {actions.FUNCTIONS[func_id].name}")
  elif source_unit_tag is None:
    logger.error(
      f"[ID {self.log_id}] Agent {self.name}, Can not find source unit of {str(units.get_unit_type(source_unit_type))} type")
  else:
    queued_source_unit_tag_list.append(source_unit_tag)

  if source_unit_tag is not None:
    full_shape_action = {'name': action_name, 'arg': [], 'func':
      [(573, actions.FUNCTIONS.llm_pysc2_move_camera, [int(source_unit_tag)]),
       (2, actions.FUNCTIONS.select_point, ['select', int(source_unit_tag)])] + action['func']}
  else:
    full_shape_action = {'name': 'No_Operation', 'arg': [], 'func':
      [(0, actions.FUNCTIONS.no_op, {})]}

  return full_shape_action


class BaseTranslatorA:

  def __init__(self):
    pass

  def translate(self, obs) -> list[tuple[int, callable]]:
    pass


# TODO: You can specialize your TranslatorA here


class DefaultTranslatorA(BaseTranslatorA):

  def __init__(self, name, log_id, config):
    super(DefaultTranslatorA, self).__init__()
    self.agent_name = name
    self.ACTION_SPACE = config.AGENTS[name]['action']
    self.ACTION_SPACE_DICT = {}
    for unit_type in self.ACTION_SPACE.keys():
      for action in self.ACTION_SPACE[unit_type]:
        self.ACTION_SPACE_DICT[action['name']] = action
    self.log_id = log_id
    logger.info(f"[ID {self.log_id}] {name} DefaultTranslatorA initialized")

  # text actions recognition
  def translate(self, raw_text_a: str):
    action_list_dict = {}
    action_lists, action_lists2 = [], []
    team_actions, team_actions2 = [], []
    processed_text_a, team_name = '', ''
    lines = raw_text_a.splitlines()
    start_recognize = False
    first_function = True
    for line in lines:
      if ("Actions:" in line) or ("Action:" in line) or \
          ("actions:" in line) or ("action:" in line):
        processed_text_a = "Actions:"
        start_recognize = True
      if ("Communications:" in line) or ("Communication:" in line) or \
          ("communications:" in line) or ("Communication:" in line):
        start_recognize = False
      if start_recognize:
        if ("Team" in line and ":" in line) or ("team" in line and ":" in line):
          if len(team_actions) != 0:
            action_lists.append(team_actions)
            action_lists2.append(team_actions2)
            action_list_dict[team_name] = team_actions  # the team these actions were written under
            team_actions, team_actions2 = [], []
          first_function = True
          team_name = line.split("eam ")[1].split(":")[0].strip()  # Team/team xxxx:  -->  xxxx
          processed_text_a += f"\n\tTeam {team_name}:"
        elif "<" in line and ">" in line:
          action_text = line.split("<")[1].split(">")[0]
          action_name = action_text.split("(")[0]
          action_args = action_text.split("(")[1].split(")")[0]
          action_valid, tag, tag2, tag3, x, y = True, None, None, None, None, None
          if "0x" in action_args:
            tag = int(re.findall(r'0x\w+', action_args)[0], 16)
            if len(re.findall(r'0x\w+', action_args)) > 1:
              tag2 = int(re.findall(r'0x\w+', action_args)[1], 16)
            if len(re.findall(r'0x\w+', action_args)) > 2:
              tag3 = int(re.findall(r'0x\w+', action_args)[2], 16)
          if "[" in action_args:
            x = float(re.findall(r'\[-?\d+\.?\d*e?-?\d*?', action_args)[0].split("[")[1])
            y = float(re.findall(r'-?\d+\.?\d*e?-?\d*?\]', action_args)[0].split("]")[0])

          # 在动作空间中查找action_name对应的action
          if action_name in self.ACTION_SPACE_DICT.keys():
            action = self.ACTION_SPACE_DICT[action_name]
          else:
            logger.error(f"translator unable to find {action_name}")
            action = {'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]}
            action_valid = False

          # 将识别出的动作参数填入函数参数元组中
      
          new_func_triples, new_func_triples2 = [], []
          for func_triple in action['func']:  # func_triple 形如 (0, F.no_op, ())
            new_func_triple, new_func_triple2, new_func_args = [], [], []
            func_args = func_triple[2]
            if len(list(func_args)) > 0:
              if not isinstance(func_args, tuple):
                func_args = [func_args]
              for arg in list(func_args):
                if arg == "now":
                  new_func_args.append('now')
                if arg == "queued":
                  if first_function:
                    new_func_args.append('now')
                  else:
                    new_func_args.append('queued')
                if arg == "select":
                  new_func_args.append('select')
                if arg in ["screen_tag", "minimap_tag", "world_tag", "screen1_tag", "screen2_tag"]:
                  if tag is not None:
                    new_func_args.append(tag)
                  else:
                    new_func_args.append('error')
                if arg in ["screen_tag2", "minimap_tag2", "world_tag2", "screen1_tag2", "screen2_tag2"]:
                  if tag2 is not None:
                    new_func_args.append(tag2)
                  else:
                    new_func_args.append('error')
                if arg in ["screen", "minimap"]:
                  if (x is not None) and (y is not None):
                    new_func_args.append([x, y])
                  else:
                    new_func_args.append('error')
                # if arg in ["screen1_tag", "screen2_tag"]:
                #   if tag is not None:
                #     new_func_args.append(tag)
                #   else:
                #     new_func_args.append('error')
                # if arg in ["screen1_tag2", "screen2_tag2"]:
                #   if tag2 is not None:
                #     new_func_args.append(tag2)
                #   else:
                #     new_func_args.append('error')
            if 'error' not in new_func_args and first_function and 'now' in new_func_args:
              first_function = False
            if 'error' in new_func_args:
                action_valid = False
            new_func_triple.append(func_triple[0])
            new_func_triple.append(func_triple[1])
            new_func_triple.append(tuple(new_func_args))
            new_func_triples.append(tuple(new_func_triple))

            new_func_triple2.append(func_triple[0])
            new_func_triple2.append(func_triple[1].name)
            new_func_triple2.append(tuple(new_func_args))
            new_func_triples2.append(tuple(new_func_triple2))

          if action_valid:
            team_actions.append({'name': action['name'], 'arg': action['arg'], 'func': new_func_triples})
            team_actions2.append({'name': action['name'], 'arg': action['arg'], 'func': new_func_triples2})
            processed_text_a += f"\n\t\t<{action_text}>"
          else:
            team_actions.append({'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]})
            team_actions2.append({'name': 'No_Operation', 'arg': [], 'func': [(0, F.no_op, ())]})
        else:
          pass

    if len(team_actions) != 0:
      action_lists.append(team_actions)
      action_lists2.append(team_actions2)
      action_list_dict[team_name] = team_actions
      first_function = True
      team_actions, team_actions2 = [], []

    return action_lists, action_list_dict, processed_text_a


PROTOSS_FACTORY = {'default': DefaultTranslatorA}
TERRAN_FACTORY = {'default': DefaultTranslatorA}
ZERG_FACTORY = {'default': DefaultTranslatorA}

FACTORY = {
  'protoss': PROTOSS_FACTORY,
  'terran': TERRAN_FACTORY,
  'zerg': ZERG_FACTORY,
}


if __name__ == "__main__":
  from llm_pysc2.agents.configs.config import ProtossAgentConfig
  config = ProtossAgentConfig()

  # ----------------- show action space -----------------
  def show(config):
    for name in config.AGENTS.keys():
      agent_actions = config.AGENTS[name]['action']
      print(name)
      for unit_type in agent_actions.keys():
        print(f"\t{str(units.get_unit_type(unit_type))}")
        for i in range(len(agent_actions[unit_type])):
          action = agent_actions[unit_type][i]
          if len(action['arg']) == 0:
            print(f"\t\t <{action['name']}()>")
        for i in range(len(agent_actions[unit_type])):
          action = agent_actions[unit_type][i]
          if len(action['arg']) == 1 and 'minimap' in action['arg']:
            print(f"\t\t <{action['name']}({action['arg'][0]})>")
        for i in range(len(agent_actions[unit_type])):
          action = agent_actions[unit_type][i]
          if len(action['arg']) == 1 and 'screen' in action['arg']:
            print(f"\t\t <{action['name']}({action['arg'][0]})>")
        for i in range(len(agent_actions[unit_type])):
          action = agent_actions[unit_type][i]
          if len(action['arg']) == 1 and 'tag' in action['arg']:
            print(f"\t\t <{action['name']}({action['arg'][0]})>")
        for i in range(len(agent_actions[unit_type])):
          action = agent_actions[unit_type][i]
          if len(action['arg']) == 2:
            print(f"\t\t <{action['name']}({action['arg'][0]}, {action['arg'][1]})>")
  show(config)

  # ----------------- example of TranslatorA -----------------

  translator = DefaultTranslatorA('CombatGroup1', 0, config)
  text = \
"""
Analysis:
    We should do xxx and xxx.

Actions:
    Team Stalker-1:
        <Move_Screen([2, 9])>
        <Attack_Unit(0x200540001)>
    Team Stalker-2:
        <Ability_Blink_Screen([33, 96])>
        <Move_Minimap([24, 54])>
    Team Stalker-3:
        <Select_Unit_Blink_Screen(0x1007c0001 ,[33, 96])>
        <Hold_Position()>
"""

  actions, processed_text_a, _ = translator.translate(text)
  print(f"\n\ntext to translator:{text}")
  print(f"detected action from translator:\n{actions}\n")
  print(f"detected text_a from translator:\n{processed_text_a}\n")
  print(f"agent {translator.agent_name} action names: {translator.ACTION_SPACE_DICT.keys()}")
  print(f"agent {translator.agent_name} action num: {len(translator.ACTION_SPACE_DICT.keys())}")

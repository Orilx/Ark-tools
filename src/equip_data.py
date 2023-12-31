import json
from pathlib import Path
import re
from decimal import Decimal
from typing import Dict
from ruamel.yaml import YAML

# 特性/天赋
target_table = {"TRAIT": "overrideTraitDataBundle",
                "TRAIT_DATA_ONLY": "overrideTraitDataBundle",
                "DISPLAY": "overrideTraitDataBundle",
                "TALENT": "addOrOverrideTalentDataBundle",
                "TALENT_DATA_ONLY": "addOrOverrideTalentDataBundle"}

# 专有名词
name_table = {
    "atk": "攻击",
    "def": "防御",
    "max_hp": "生命",
    "attack_speed": "攻速",
    "block_cnt": "阻挡数",
    "cost": "部署费用",
    "respawn_time": "再部署时间",
    "sp": "技力",
    "dist": "距离",
    "value": "值",
    "interval": "周期",
    "heal_scale": "治疗相当于攻击力百分比的生命",
    "damage_resistance": "庇护",
    "hp_ratio": "生命值比率",
    "atk_to_hp_recovery_ratio": "恢复相当于攻击力百分比的生命",
    "atk_scale": "攻击力提升",
    "element_atk_scale": "",
    "range_radius": "范围半径",
    "cnt": "",
    "magic_resistance": "法术抗性",
    "buildable_type": "可部署状态",
    "attack@chain.max_target": "最大攻击目标数",
    "attack@sluggish": "停顿时间",
    "attack@chain.atk_scale": "",
    "skill@chain.atk_scale": "",
    "max_stack_cnt": "最大叠加次数",
    "e_hidden_duration": "隐匿时间",
}


class Equip:
    def __init__(self, uniequip_table: Path, battle_equip_table: Path, character_table: Path) -> None:
        with open(battle_equip_table, "r", encoding='utf-8') as file:
            self.battle_equip_table = json.load(file)
        with open(character_table, "r", encoding='utf-8') as file:
            self.character_table = json.load(file)
        with open(uniequip_table, "r", encoding='utf-8') as file:
            equip_table = json.load(file)
        self.new_equips = equip_table["equipTrackDict"][-1]["trackList"]
        self.equipDict = equip_table["equipDict"]
        self.missionList = equip_table["missionList"]
        self.result = []


    def t(self, key: str, key_map: Dict[str, float]) -> str:
        """匹配 {} 中的内容并以字符串形式返回对应的值

        Args:
            key (str): 输入的 key
            key_map (Dict[str, float]): 映射表

        Returns:
            str: _description_
        """

        r = key.split(':')
        value = Decimal(f'{key_map[r[0]]}')
        result = f'{value.to_integral_value()}'
        if len(r) == 2:
            if r[1] == "0%":
                result = f'{(value*100).to_integral_value()}%'
        return result

    def parser(self, src: str, key_map: Dict[str, float]):
        # 替换全角符号
        src = src.replace("％", "%")
        # 匹配并清除多余的标签
        src = re.sub(r"(<([@$/].*?)>)", "", src)

        # 匹配被 {} 包围的部分
        result = re.sub(
            r"\{(.*?)\}", lambda match: self.t(match.group(1), key_map), src)
        return result

    def process(self, equip_id, char_id, battle_equip_table):
        tem = {
            "char_name": self.character_table[char_id]["name"],
            "equip_name": self.equipDict[equip_id]["uniEquipName"],
            "equip": []
        }
        phases = battle_equip_table.get(equip_id)
        if not phases:
            return
        for equip in phases["phases"]:
            # 模组等级
            equipLevel = equip["equipLevel"]
            attributeBlackboard = []
            # 白值更新
            for i in equip["attributeBlackboard"]:
                k = i["key"]
                v = int(i["value"])
                attributeBlackboard.append(f"{name_table[k]} +{v}")
            TRAIT = []
            TALENT = []
            for part in equip["parts"]:
                # 增强目标
                target = part["target"]

                if target in ["TRAIT", "TRAIT_DATA_ONLY", "DISPLAY"]:
                    for candidate in part["overrideTraitDataBundle"]["candidates"]:
                        blackboard = {}
                        for b in candidate["blackboard"]:
                            blackboard[b["key"]] = b["value"]
                        # 提取描述
                        if additionalDescription := candidate["additionalDescription"]:
                            res = self.parser(
                                f"{additionalDescription}", blackboard)
                            TRAIT.append(res)

                        if overrideDescripton := candidate["overrideDescripton"]:
                            res = self.parser(
                                f"{overrideDescripton}", blackboard)
                            TRAIT.append(res)
                elif target in ["TALENT", "TALENT_DATA_ONLY"]:
                    # 提取 addOrOverrideTalentDataBundle
                    for candidate in part["addOrOverrideTalentDataBundle"]["candidates"]:
                        # 提取天赋更新描述
                        if upgradeDescription := candidate["upgradeDescription"]:
                            requiredPotentialRank = candidate["requiredPotentialRank"]
                            # 只保留 1 潜情况下的数据
                            if requiredPotentialRank:
                                continue
                            name = candidate["name"]
                            res = self.parser(
                                # 天赋 [{name}] 更新（潜能为 {requiredPotentialRank+1} 时）:
                                f"{upgradeDescription}", {})
                            TALENT.append(res)

            tem["equip"].append({
                # "level": equipLevel,
                "attributeBlackboard": attributeBlackboard,
                "TRAIT": TRAIT,
                "TALENT": TALENT
            })
        self.result.append(tem)

    def do_process(self):
        for e in self.new_equips:
            equipId = e["equipId"]
            char_id = e["charId"]
            self.process(equipId, char_id, self.battle_equip_table)
        # print(self.result)
        with open(dataPath / f"equip_table.yaml", "w") as file:
            # json.dump(self.result, file, ensure_ascii=False)
            yaml = YAML(pure=True)

            yaml.dump(self.result, file)


dataPath = Path("data/game_data/equip_data")

Equip(dataPath / "uniequip_table.json",
      dataPath / "battle_equip_table.json",
      dataPath / "character_table.json").do_process()

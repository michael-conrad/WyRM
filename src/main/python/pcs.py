from character_sheet import CharacterSheet
from equipment import Armor
from equipment import Weapon
from mana import MageSpellList
from talents import CharacterTalent
from talents import TalentList


class PCs:
    @classmethod
    def player_forsaken_alley(cls) -> CharacterSheet:
        player = CharacterSheet()
        player.name = "Player"
        player.warrior_base = 5
        player.rogue_base = 2
        player.mage_base = 3
        player.equip_armor(Armor.by_name("Chain"))
        player.weapons.append(Weapon.by_name("Axe"))
        player.spells.append(MageSpellList.spell_by_name("Frost Burn"))
        player.spells.append(MageSpellList.spell_by_name("Healing Hand"))
        player.talents.append(TalentList.by_name("Massive Attack"))
        player.reset_pools()
        return player

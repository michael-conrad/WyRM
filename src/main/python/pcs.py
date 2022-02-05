from character_sheet import CharacterSheet
from equipment import Armor
from equipment import Weapon
from mana import MageSpellList


class PCs:
    @classmethod
    def player_forsaken_alley(cls) -> CharacterSheet:
        player = CharacterSheet()
        player.warrior = 5
        player.rogue = 2
        player.mage = 3
        player.armor_penalty = 1
        player.reset_pools()

        # Leather, Armor: +2, Armor Penalty: 1
        player.equip_armor(Armor.by_name("Leather"))

        player.weapons.append(Weapon.by_name("Axe"))

        player.spells.append(MageSpellList.spell_by_name("Frost Burn"))
        player.spells.append(MageSpellList.spell_by_name("Healing Hand"))
        return player

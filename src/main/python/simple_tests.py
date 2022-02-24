from dnd5e_monsters import CharacterSheet5
from dnd5e_monsters import from_dnd5e

if __name__ == "__main__":
    dnd: CharacterSheet5 = CharacterSheet5()
    dnd.name="Skeleton Warrior"
    dnd.armor_class = 13
    dnd.str = 10
    dnd.dex = 14
    dnd.con = 15
    dnd.int = 6
    dnd.wis = 8
    dnd.cha = 5
    dnd.xp = 50
    dnd.main_attack_dmg="1d6+2"
    dnd.attack_bonus=4
    dnd.weapon = "Shortsword"
    print(dnd)
    print(from_dnd5e(dnd))

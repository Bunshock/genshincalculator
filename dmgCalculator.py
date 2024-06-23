# Note: Every multiplier/additive value is given by its percentage / 100

# To calculate non-reaction DMG, set reaction to ''

from math import ceil


class Character:
    def __init__(self, name, Level, LevelMult, HP, ATK, EM, CR, CD, ER):
        self.name = name
        self.Level = Level
        self.LevelMult = LevelMult
        self.HP = HP
        self.ATK = ATK
        self.EM = EM
        self.CR = CR
        self.CD = CD
        self.ER = ER
        # Dictionary of character abilities
        self.abilities = {}
    
    # scalingStats is an array of [stat, value] pairs
    def setAbility(self, name, scalingStats, damageType):
        self.abilities[name] = {}
        self.abilities[name]['ScalingStats'] = {}
        self.abilities[name]['DMGType'] = damageType

        for stat in scalingStats:
            self.abilities[name]['ScalingStats'][stat[0]] = stat[1]


class Enemy:
    def __init__(self, name, Level=100, DEFReduction=0, DEFIgnored=0,
                 DMGReduction=0, RES={}):
        self.name = name
        self.Level = Level
        self.DEFReduction = DEFReduction
        self.DEFIgnored = DEFIgnored
        self.DMGReduction = DMGReduction
        # Initialize resistances
        self.RES = {}
        self.RES['Physical'] = 0
        self.RES['Anemo'] = 0
        self.RES['Hydro'] = 0
        self.RES['Pyro'] = 0
        self.RES['Cryo'] = 0
        self.RES['Electro'] = 0
        self.RES['Dendro'] = 0
        self.RES['Geo'] = 0
        # Set resistances
        for resistance in RES:
            self.RES[resistance] = RES[resistance]
    
    # Get an enemy's RES multiplier
    def getRESMult(self, RESType):
        RES = self.RES[RESType]
        if RES < 0:
            return 1 - RES / 2
        elif RES < 0.75:
            return 1 - RES
        else:
            return 1 / (4 * RES + 1)


class Buffs:
    def __init__(self, baseMult=0, baseAdd=0, bonusMult=0):
        self.baseMult = baseMult
        self.baseAdd = baseAdd
        self.bonusMult = bonusMult


class Reaction:
    def __init__(self, type, bonusDMG):
        self.type = type
        self.bonusDMG = bonusDMG


# Reactions multipliers
TRANSFORMATIVE = {
    'Overloaded': 2.0,
    'Shattered': 1.5,
    'Electro-Charged': 1.2,
    'Superconduct': 0.5,
    'Swirl': 0.6,
    'Burning': 0.25,
    'Bloom': 2.0,
    'Hyperbloom': 3.0,
    'Burgeon': 3.0
}
AMPLIFYING = {
    'Melt': 2.0,
    'Rev-Melt': 1.5,
    'Vaporize': 2.0,
    'Rev-Vaporize': 1.5
}
CATALYZE = {
    'Spread': 1.25,
    'Aggravate': 1.15
}


# Non-transformative DMG calculation
def nonTransformativeDMG(reaction, character, ability, buffs, enemy):

    # Raw ability DMG: is the sum of every scaling stat multiplied by its scaling value
    BaseDMG = sum([eval('character.' + stat) * ability['ScalingStats'][stat]
        for stat in ability['ScalingStats']
    ])

    # (Furina's E, Neuvillette's 1st Ascension, Yoimiya's E, etc)
    BaseMult = 1 + buffs.baseMult

    # (Spread, Aggravate, Yun Jin's 4th Ascension, Zhongli's 4th Ascension
    # Song of Days Past 4-set bonus, etc)
    BaseAdd = buffs.baseAdd
    if reaction.type in CATALYZE:
        EMBonus = 5 * character.EM / (character.EM + 1200)
        BaseAdd += CATALYZE[reaction.type] * character.LevelMult * (
            1 + EMBonus + reaction.bonusDMG
        )

    # Bonus multipliers (Furina's Q, Yelan's Q, 2-set (elemental) bonuses, etc)
    BonusMult = 1 + buffs.bonusMult - enemy.DMGReduction

    # Enemy defense multiplier
    DEFMult = (character.Level + 100) / (
        (1-enemy.DEFReduction) * (1-enemy.DEFIgnored) * (
            enemy.Level + 100
        ) + (character.Level + 100)
    )

    # Enemy resistance multiplier
    RESMult = enemy.getRESMult(ability['DMGType'])

    # Base ability damage
    abilityDMG = (BaseDMG * BaseMult + BaseAdd) * BonusMult * DEFMult * RESMult

    # Melt/Vaporize bonus
    if reaction.type in AMPLIFYING:
        EMBonus = 2.78 * character.EM / (character.EM + 1400)
        abilityDMG *= AMPLIFYING[reaction.type] * (
            1 + EMBonus + reaction.bonusDMG
        )

    # Return ability damage (non-crit)
    return abilityDMG


# Transformative DMG calculation
def transformativeDMG(reaction, charEM, charLevelMult, RESMult):

    # Elemental mastery bonus
    EMBonus = 16 * charEM / (charEM + 2000)
    
    return TRANSFORMATIVE[reaction.type] * charLevelMult * (
        1 + EMBonus + reaction.bonusDMG
    ) * RESMult


# Critical damage formula for a given crit damage CD
def critDMG(nonCrit, CD):
    return nonCrit * (1 + CD / 100.0)


# Average damage formula for a given damage and crit rate CR
def averageDMG(nonCrit, CR, CD):
    crit = critDMG(nonCrit, CD)
    return (CR / 100.0) * crit + (1 - CR / 100.0) * nonCrit


# Calculate non-critical ability damage (Genshin uses integer damage values)
def calculateAbilityDMG(character, abilityName, reaction, buffs, enemy):
    nonCritDMG = 0
    if reaction.type in TRANSFORMATIVE:
        nonCritDMG = ceil(transformativeDMG(
            reaction=reaction,
            charEM=character.EM,
            charLevelMult=character.LevelMult,
            RESMult=enemy.getRESMult(
                character.abilities[abilityName]['DMGType']
            )
        ))
    else:
        nonCritDMG = ceil(nonTransformativeDMG(
            reaction=reaction,
            character=character,
            ability=character.abilities[abilityName],
            buffs=buffs,
            enemy=enemy
        ))

    # Print results
    print((
        f'{character.name}: {abilityName} {reaction.type} damage on '
        f'level {enemy.Level} {enemy.name}:'
    ))
    print(f'Non-crit damage: {nonCritDMG}')
    print(f'Crit damage: {int(critDMG(nonCritDMG, character.CD))}')
    print(f'Average damage: {ceil(averageDMG(nonCritDMG, character.CR, character.CD))}',
          end='\n\n')

    return nonCritDMG


if __name__ == '__main__':

    # Damage will be tested against a lv 85 Ruin Guard
    enemy = Enemy(name='Ruin Guard', Level=85, DEFReduction=0, DEFIgnored=0,
                DMGReduction=0, RES={
                    'Physical': 0.7,
                    'Pyro': 0.1,
                    'Hydro': 0.1,
                    'Electro': 0.1,
                    'Cryo': 0.1,
                    'Anemo': 0.1,
                    'Dendro': 0.1,
                    'Geo': 0.1,
                })
        
    # TEST: Level 90 Hu Tao lv.9 Normal Attack 1 (not in Paramita Papilio state)
    # Note: Paramita Papilio state (at lv.9) increases ATK by 5.96% of HP
    huTao = Character(name='Hu Tao', Level=90, LevelMult=1446.853458, HP=34508,
                    EM=103, CR=81.1, CD=214.3, ER=111, ATK=1441)

    huTao.setAbility(name='NA-1', scalingStats=[['ATK', 0.789]],
                    damageType='Physical')

    buffs = Buffs(baseMult=0, baseAdd=0, bonusMult=0)

    reaction = Reaction(type='', bonusDMG=0)

    # Calculate damage for NA-1 non-reaction
    calculateAbilityDMG(
        character=huTao,
        abilityName='NA-1',
        reaction=reaction,
        buffs=buffs,
        enemy=enemy
    )

    # TEST: Level 90 Hu Tao lv.9 Charged Attack in Paramita Papilio state
    # Note: Paramita Papilio state (at lv.9) increases ATK by 5.96% of HP

    # In case we need to reset Paramita Papilio state
    huTaoNonPapilioATK = huTao.ATK
    # Set Paramita Papilio state by raising Hu Tao's ATK
    huTao.ATK += 0.0596 * huTao.HP

    huTao.setAbility(name='CA-Infused', scalingStats=[['ATK', 2.287]],
                    damageType='Pyro')

    # Paramita Papilio state grants 33% Pyro DMG Bonus below 50% HP
    buffs = Buffs(baseMult=0, baseAdd=0, bonusMult=0.33)

    reaction = Reaction(type='Vaporize', bonusDMG=0)

    # Calculate damage for CA Vaporize on level 100 enemy
    calculateAbilityDMG(
        character=huTao,
        abilityName='CA-Infused',
        reaction=reaction,
        buffs=buffs,
        enemy=enemy
    )

    del huTao
    del enemy
    del buffs
    del reaction

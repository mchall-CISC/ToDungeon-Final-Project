from dataclasses import dataclass, field
import random
from drafter import *
from datetime import datetime
from bakery import assert_equal

set_website_title("Matt's Test Website 11132026")
set_site_information(
    author="Matthew Hall",
    description="A program that tracks your 'To-Dos' and turns them into quests that you can earn rewards from completing.",
    sources="Drafter docs and my LLM.",
    planning=["plan.pdf", "design.pdf"],
    links=["https://github.com/your-username/ToDungeon-Final-Project"]
)
hide_debug_information()
set_website_framed(False)

# Global variables for the shop
POTION_COST = 20
WEAPON_ATTACK_INCREASE = 2.0
POTION_HEAL = 35

def calculate_quest_rewards(difficulty: int, level: int) -> tuple[int, int]:
    """Calculate the EXP and gold rewards for completing a quest."""

    exp_reward = difficulty * 10 + (level - 1) * 5
    gold_reward = difficulty * 5 + (level - 1) * 2 # might remove the level dependency later for gold

    return exp_reward, gold_reward

def create_seed() -> int:
    """Generate a random six-digit dungeon seed."""
    return random.randint(100000, 999999)

@dataclass
class Quest:
    """Store information about an individual player quest"""
    
    name: str
    difficulty: int
    date: int
    exp: int
    gold: int

@dataclass
class Enemy:
    """Store the information and combat stats of a dungeon enemy."""

    name: str
    level: int
    hp: int
    max_hp: int
    attack: int
    defense: int
    is_strong: bool = False
    
# Dictionary for enemy base stats (will be modified by level in the actual dungeon encounters)
# For each SEED value, ("[enemy name]", [int for attack], [int for defense])
ENEMY_BASE_STATS = {
    0: ("Bat", 2, 0),
    1: ("Slime", 1, 1),
    2: ("Ghost", 2, 2),
    3: ("Mannequin", 3, 3),
    4: ("Robot", 5, 3),
    5: ("Skeleton", 4, 1),
    6: ("Double-Edged Sword", 6, 0),
    7: ("Knight Armor", 3, 5),
    8: ("Stick", 5, 1)
}

@dataclass
class State:
    """Keep track of the player's progress and inventory."""

    # Player information.
    potion_count: int = 2
    weapon_atk: float = 5.0
    quests: list[Quest] = field(default_factory=list)
    lvl: int = 1
    gold: int = 0
    seed: int = field(default_factory=create_seed)
    exp: int = 0

    # Dungeon information.
    player_hp: int = 100
    max_player_hp: int = 100
    player_defense: int = 2
    encounter_message: str = ""
    room_count: int = 0
    dungeon_active: bool = False
    current_encounter: str = ""
    current_enemy: Enemy | None = None
    enemies_defeated: int = 0
    dungeon_exp: int = 0
    dungeon_gold: int = 0

def create_enemy(enemy_type: int, level: int,
                 strong: bool = False) -> Enemy:
    """Generate an enemy with stats determined by its type and level."""

    # Retrieve the enemy's base information.
    name, base_attack, base_defense = ENEMY_BASE_STATS[enemy_type]

    # Calculate the enemy's health based entirely on its level.
    enemy_hp = 20 + (level - 1) * 10

    # Calculate attack and defense using the enemy's base stats.
    attack = base_attack + (level - 1) * 2
    defense = base_defense + (level - 1)

    # Give Strong Enemies additional attack and defense.
    if strong:
        name = "Strong " + name
        attack += 2
        defense += 1

    # Create and return the Enemy instance.
    return Enemy(
        name,
        level,
        enemy_hp,
        enemy_hp,
        attack,
        defense,
        strong
    )

def determine_encounter(seed: int, room_number: int) -> tuple[str, int | None]:
    """Determine the encounter type using the dungeon seed and room number."""

    # The first six rooms are determined by the seed.
    if room_number <= 6:

        # Convert the seed into a string so we can access individual digits.
        seed_digits = str(seed)

        # Retrieve the digit corresponding to the current room.
        encounter_digit = int(seed_digits[room_number - 1])

        # Digits 0-8 correspond to regular enemies.
        if encounter_digit <= 8:
            return "enemy", encounter_digit

        # Digit 9 represents a randomly selected special encounter.
        else:
            special_encounter = random.choice(["bush", "chest"])
            return special_encounter, None

    # Room seven always contains a Strong Enemy.
    elif room_number == 7:

        enemy_type = random.randint(0, 8)
        return "strong_enemy", enemy_type

    # Return this if all seven rooms have already been generated.
    else:
        return "finished", None

def display_current_encounter(state: State) -> Page:
    """Display the current encounter and the player's combat status."""

    page_content = [
        Header("Dungeon Exploration"),
        "Room " + str(state.room_count) + " of 7\n",

        Header("Your Status", 2),
        "HP: " + str(state.player_hp) + "/" + str(state.max_player_hp),
        "Attack: " + str(state.weapon_atk),
        "Defense: " + str(state.player_defense),
        "Healing Potions: " + str(state.potion_count) + "\n"
    ]

    # Display the most recent combat message.
    if state.encounter_message != "":
        page_content.append(state.encounter_message)
        page_content.append("\n")

    # Display information about regular and Strong Enemies.
    if state.current_encounter == "enemy" or state.current_encounter == "strong_enemy":
        
        enemy = state.current_enemy

        page_content.extend([
           Header(enemy.name, 2),
           "Enemy Level: " + str(enemy.level),
           "Enemy HP: " + str(enemy.hp) + "/" + str(enemy.max_hp),
           "Enemy Attack: " + str(enemy.attack),
           "Enemy Defense: " + str(enemy.defense)
        ])

        # Add the player's combat actions.
        page_content.append(
            Button("Attack Enemy", "attack_enemy")
        )

        page_content.append(
            Button("Use Healing Potion", "use_potion")
        )

        # Players cannot run away from Strong Enemies.
        if not enemy.is_strong:
            page_content.append(
                Button("Run Away", "run_away")
            )

    # Display the bush encounter.
    elif state.current_encounter == "bush":

        page_content.extend([
            Header("Something in the Bush...", 2),
            "You notice something moving in a nearby bush.",
            "Perhaps there is something useful inside?\n",

            Button(
                "Investigate Bush",
                "resolve_bush",
                [Argument("decision", "investigate")]
            ),
    
            Button(
                "Leave It Alone",
                "resolve_bush",
                [Argument("decision", "leave")]
            )
        ])

    # Display the chest encounter.
    elif state.current_encounter == "chest":

        page_content.extend([
            Header("Mysterious Chest", 2),
            "You discover an unusual chest.",
            "It might contain valuable treasures...\n",

            Button(
                "Open Chest",
                "resolve_chest",
                [Argument("decision", "open")]
            ),
    
            Button(
                "Leave Chest Alone",
                "resolve_chest",
                [Argument("decision", "leave")]
            )
        ])

    page_content.append(
        Button("Return to Quest List", "index")
    )

    return Page(state, page_content)

def display_room_cleared(state: State, message: str) -> Page:
    """Display the results of defeating an enemy in a room."""

    return Page(state, [
        Header("Room Cleared!"),
        message,

        "\nEnemies Defeated: " + str(state.enemies_defeated),
        "Dungeon EXP: " + str(state.dungeon_exp),
        "Dungeon Gold: " + str(state.dungeon_gold),

        Button("Continue to Next Room", "generate_dungeon_room")
    ])

def display_dungeon_defeat(state: State) -> Page:
    """End the dungeon and display the player's defeat."""

    defeated_count = state.enemies_defeated

    state.dungeon_active = False
    state.current_enemy = None
    state.current_encounter = ""
    state.encounter_message = ""

    state.dungeon_exp = 0
    state.dungeon_gold = 0

    return Page(state, [
        Header("You Have Been Defeated!"),
        "Unfortunately, you were unable to complete the dungeon.",
        "All accumulated dungeon rewards have been lost.\n",

        "Enemies Defeated: " + str(defeated_count),
        "Your remaining HP: " + str(state.player_hp),

        Button("Return to Quest List", "index")
    ])

def display_dungeon_victory(state: State) -> Page:
    """Award dungeon rewards and display the player's victory."""

    earned_exp = state.dungeon_exp
    earned_gold = state.dungeon_gold

    state.exp += earned_exp
    state.gold += earned_gold

    # Reset dungeon rewards to prevent duplicate payouts.
    state.dungeon_exp = 0
    state.dungeon_gold = 0

    state.dungeon_active = False
    state.current_enemy = None
    state.current_encounter = ""
    state.encounter_message = ""

    exp_needed = state.lvl * 100

    leveled_up = False

    if state.exp >= exp_needed:
        state.lvl += 1
        state.exp = 0
        leveled_up = True

    page_content = [
        Header("Dungeon Victory!"),
        "Congratulations! You conquered all seven rooms!\n",

        Header("Your Rewards", 2),
        "EXP Earned: " + str(earned_exp),
        "Gold Earned: " + str(earned_gold),

        "\nEnemies Defeated: " + str(state.enemies_defeated),
        "Current Level: " + str(state.lvl),
        "Current EXP: " + str(state.exp),
        "Current Gold: " + str(state.gold)
    ]

    if leveled_up:
        page_content.append(
            "\nYou reached Level " + str(state.lvl) + "!"
        )

    page_content.append(
        Button("Return to Quest List", "index")
    )

    return Page(state, page_content)

@route
def attack_enemy(state: State) -> Page:
    """Allow the player to attack an enemy and receive retaliation."""

    # Make sure there is an active enemy to fight.
    if not state.dungeon_active or state.current_enemy is None:
        return index(state, "There is no enemy to attack!")

    enemy = state.current_enemy

    # Calculate the damage dealt by the player.
    player_damage = max(1, int(state.weapon_atk) - enemy.defense)

    # Subtract damage from the enemy's HP.
    enemy.hp = max(0, enemy.hp - player_damage)

    # Check whether the enemy has been defeated.
    if enemy.hp == 0:

        # Store the enemy's information before removing it.
        enemy_name = enemy.name
        enemy_level = enemy.level
        enemy_is_strong = enemy.is_strong

        # Increase the number of enemies defeated.
        state.enemies_defeated += 1

        # Calculate the rewards for defeating the enemy.
        reward_multiplier = 1

        if enemy_is_strong:
            reward_multiplier = 2

        exp_reward = enemy_level * 10 * reward_multiplier
        gold_reward = enemy_level * 5 * reward_multiplier

        state.dungeon_exp += exp_reward
        state.dungeon_gold += gold_reward

        # Remove the defeated enemy from the current encounter.
        state.current_enemy = None
        state.current_encounter = ""
        state.encounter_message = ""

        message = (
            "You defeated " + enemy_name + "! "
            + "You dealt " + str(player_damage) + " damage. "
            + "You earned " + str(exp_reward) + " dungeon EXP and "
            + str(gold_reward) + " dungeon Gold!"
        )

        # Check whether the seventh room's Strong Enemy was defeated.
        if state.room_count == 7 and enemy_is_strong:

            state.dungeon_active = False

            return display_dungeon_victory(state)

        # Display the results of clearing a regular room.
        return display_room_cleared(state, message)

    # The enemy survived, so it gets to retaliate.
    enemy_damage = max(1, enemy.attack - state.player_defense)

    state.player_hp = max(0, state.player_hp - enemy_damage)

    # Store a message describing what happened.
    state.encounter_message = (
        "You dealt " + str(player_damage) + " damage! "
        + enemy.name + " retaliated, dealing "
        + str(enemy_damage) + " damage to you!"
    )

    # Check whether the player has been defeated.
    if state.player_hp == 0:

        state.dungeon_active = False
        state.current_enemy = None
        state.current_encounter = ""
        state.encounter_message = ""

        # The player loses all accumulated dungeon rewards.
        state.dungeon_exp = 0
        state.dungeon_gold = 0

        return display_dungeon_defeat(state)

    # If both combatants are still alive, display the updated encounter.
    return display_current_encounter(state)

@route
def use_potion(state: State) -> Page:
    """Use a healing potion and allow the enemy to retaliate."""

    # Make sure there is an active enemy.
    if not state.dungeon_active or state.current_enemy is None:
        return index(state, "There is no enemy to fight!")

    # Check whether the player has any potions.
    if state.potion_count <= 0:

        state.encounter_message = "You don't have any healing potions!"

        return display_current_encounter(state)

    # Check whether the player actually needs healing.
    if state.player_hp >= state.max_player_hp:

        state.encounter_message = "You already have full health!"

        return display_current_encounter(state)

    # Remove one potion from the player's inventory.
    state.potion_count -= 1

    # Calculate how much health the potion restores.
    old_hp = state.player_hp

    state.player_hp = min(
        state.max_player_hp,
        state.player_hp + POTION_HEAL
    )

    actual_healing = state.player_hp - old_hp

    # Allow the enemy to retaliate.
    enemy = state.current_enemy

    enemy_damage = max(1, enemy.attack - state.player_defense)

    state.player_hp = max(0, state.player_hp - enemy_damage)

    # Display a message explaining what happened.
    state.encounter_message = (
        "You used a healing potion and restored "
        + str(actual_healing) + " HP! "
        + enemy.name + " attacked you for "
        + str(enemy_damage) + " damage!"
    )

    # Check whether the player has been defeated.
    if state.player_hp == 0:

        state.dungeon_active = False
        state.current_enemy = None
        state.current_encounter = ""
        state.encounter_message = ""

        state.dungeon_exp = 0
        state.dungeon_gold = 0

        return display_dungeon_defeat(state)

    # Display the updated encounter.
    return display_current_encounter(state)

@route
def run_away(state: State) -> Page:
    """Allow the player to escape a regular enemy encounter."""

    # Make sure there is an enemy to escape from.
    if not state.dungeon_active or state.current_enemy is None:
        return index(state, "There is no enemy to escape from!")

    # Prevent players from fleeing Strong Enemies.
    if state.current_enemy.is_strong:

        state.encounter_message = "You cannot escape a Strong Enemy!"

        return display_current_encounter(state)

    # Remember the enemy's name before removing it.
    enemy_name = state.current_enemy.name

    # Remove the current encounter.
    state.current_enemy = None
    state.current_encounter = ""
    state.encounter_message = ""

    # Allow the player to continue to the next room.
    return Page(state, [
        Header("You Escaped!"),
        "You successfully escaped from the " + enemy_name + "!",
        "You received no rewards for this encounter.\n",

        Button("Continue to Next Room", "generate_dungeon_room")
    ])

@route
def resolve_bush(state: State, decision: str) -> Page:
    """Resolve the player's decision to investigate or leave a bush."""

    # Make sure the player is actually encountering a bush.
    if not state.dungeon_active or state.current_encounter != "bush":
        return index(state, "There is no bush to investigate!")

    # Allow the player to leave the bush alone.
    if decision == "leave":

        state.current_encounter = ""
        state.current_enemy = None
        state.encounter_message = ""

        return display_room_cleared(
            state,
            "You decided to leave the bush alone."
        )

    # Investigate the bush.
    elif decision == "investigate":

        # Randomly determine the outcome.
        outcome = random.choice(["potion", "enemy"])

        # 50% chance of finding a healing potion.
        if outcome == "potion":

            state.potion_count += 1

            state.current_encounter = ""
            state.current_enemy = None
            state.encounter_message = ""

            return display_room_cleared(
                state,
                "You searched the bush and found a healing potion! "
                "You now have " + str(state.potion_count) + " potions."
            )

        # 50% chance of encountering an enemy.
        else:

            # Generate a randomly selected enemy.
            enemy_type = random.randint(0, 8)

            state.current_enemy = create_enemy(
                enemy_type,
                state.lvl
            )

            # Convert the bush encounter into an enemy encounter.
            state.current_encounter = "enemy"

            state.encounter_message = (
                "You investigated the bush, but a "
                + state.current_enemy.name
                + " jumped out! Prepare to fight!"
            )

            return display_current_encounter(state)

    # Handle an unexpected decision.
    else:
        return display_current_encounter(state)

@route
def resolve_chest(state: State, decision: str) -> Page:
    """Resolve the player's decision to open or leave a chest."""

    # Make sure the player is actually encountering a chest.
    if not state.dungeon_active or state.current_encounter != "chest":
        return index(state, "There is no chest to open!")

    # Allow the player to leave the chest alone.
    if decision == "leave":

        state.current_encounter = ""
        state.current_enemy = None
        state.encounter_message = ""

        return display_room_cleared(
            state,
            "You decided to leave the mysterious chest alone."
        )

    # Attempt to open the chest.
    elif decision == "open":

        # Generate a random number between 1 and 100.
        outcome = random.randint(1, 100)

        # 75% chance of finding two healing potions.
        if outcome <= 75:

            state.potion_count += 2

            state.current_encounter = ""
            state.current_enemy = None
            state.encounter_message = ""

            return display_room_cleared(
                state,
                "You opened the chest and discovered two healing potions! "
                "You now have " + str(state.potion_count) + " potions."
            )

        # 25% chance of encountering an animated chest.
        else:

            # Calculate damage equal to half the player's current HP.
            damage = int(state.player_hp * 0.5)

            state.player_hp -= damage

            state.current_encounter = ""
            state.current_enemy = None
            state.encounter_message = ""

            return display_room_cleared(
                state,
                "The chest suddenly came alive! It attacked you, "
                "dealing " + str(damage) + " damage! "
                "Your remaining HP is "
                + str(state.player_hp) + "."
            )

    # Handle an unexpected decision.
    else:
        return display_current_encounter(state)

@route
def index(state: State, message: str = "") -> Page:
    """Display the player's stats and current active quests."""

    # Create the initial contents of the page.
    page_content = [
        Header("Quest Log"),
        "Turn your to-do list into an adventure!\n",

        Header("Player Stats", 2),
        "Level: " + str(state.lvl) + "\n",
        "Experience: " + str(state.exp) + "\n",
        "Gold: " + str(state.gold) + "\n",
        "Healing Potions: " + str(state.potion_count) + "\n",
        "Weapon Attack: " + str(state.weapon_atk) + "\n",

        Header("Active Quests", 2)
    ]
    
    # Display a notification if one was provided.
    if message != "":
        page_content.append(message)
        page_content.append("\n")

    # Check whether the player has any active quests.
    if len(state.quests) == 0:
        page_content.append("You have no active quests!\n")

    else:
    # Display every quest in the player's quest list.
        for quest_index, quest in enumerate(state.quests):

        # Add a checkbox for completing this quest.
            page_content.append(
                RelatedCheckBox("completed_quests", str(quest_index))
            )
            page_content.append(" Complete: " + quest.name + "\n")
    
            page_content.append(Header(quest.name, 3))

            formatted_date = datetime.strptime(
                str(quest.date), "%Y%m%d"
            ).strftime("%m-%d-%y")

            page_content.append("Due Date: " + formatted_date + "\n")
            page_content.append("Difficulty: " + str(quest.difficulty) + "/10\n")

            page_content.append(
                "Rewards: " + str(quest.exp) + " EXP and "
                + str(quest.gold) + " Gold\n"
            )

    # Add a button for claiming completed quest rewards.
    page_content.append(
        Button("Complete Selected Quests", "complete_quests")
    )

        # Add a button to navigate to the Add Quest page.
    page_content.append(Button("Add a Quest", "add_quest"))

    # Add a button to navigate to the Inventory page.
    page_content.append(
        Button("View Inventory", "display_inventory",
               [Argument("previous_page", "index")])
    )

        # Only allow shopping and dungeon access when all quests are completed.
    if len(state.quests) == 0 and not state.dungeon_active:

        page_content.append(
            Button("Visit Shop", "display_shop")
        )

        page_content.append(
            Button("Enter Dungeon", "start_dungeon")
        )

    # Allow players to resume an existing dungeon.
    elif state.dungeon_active:

        page_content.append(
            Button("Resume Dungeon", "generate_dungeon_room")
        )

    return Page(state, page_content)

@route
def display_shop(state: State, message: str = "") -> Page:
    """Display the shop and its available purchases."""

    # Prevent players from shopping while quests remain.
    if len(state.quests) > 0 or state.dungeon_active:
        return index(state, "You cannot shop while quests remain or a dungeon is active!")
    
    # Calculate the current weapon upgrade price.
    weapon_upgrade_cost = int(state.weapon_atk * 10)

    page_content = [
        Header("Adventurer's Shop"),
        "Welcome, adventurer!\n",
        "Available Gold: " + str(state.gold) + "\n"
    ]

    # Display a notification if one was provided.
    if message != "":
        page_content.append(message)
        page_content.append("\n")

    page_content.extend([
        Header("Healing Potions", 2),
        "Cost: " + str(POTION_COST) + " Gold",
        "Current Potions: " + str(state.potion_count) + "\n",

        Button(
            "Buy Healing Potion",
            "purchase_item",
            [Argument("item", "potion")]
        ),

        Header("Weapon Upgrades", 2),
        "Current Attack: " + str(state.weapon_atk),
        "Upgrade Cost: " + str(weapon_upgrade_cost) + " Gold",
        "Attack Increase: +" + str(WEAPON_ATTACK_INCREASE) + "\n",

        Button(
            "Upgrade Weapon",
            "purchase_item",
            [Argument("item", "weapon")]
        ),

        "\n",
        Button("Return to Quest List", "index")
    ])

    return Page(state, page_content)

@route
def purchase_item(state: State, item: str) -> Page:
    """Process a purchase and update the player's inventory."""

    # Prevent purchases while quests remain.
    if len(state.quests) > 0 or state.dungeon_active:
        return index(state, "Complete all your quests before shopping!")

    # Determine which item the player wants to purchase.
    if item == "potion":

        # Check whether the player has sufficient gold.
        if state.gold >= POTION_COST:

            state.gold -= POTION_COST
            state.potion_count += 1

            message = "You successfully purchased a healing potion!"

        else:
            message = "You don't have enough gold for a healing potion!"

    elif item == "weapon":

        # Calculate the current weapon upgrade price.
        weapon_upgrade_cost = int(state.weapon_atk * 10)

        # Check whether the player can afford the upgrade.
        if state.gold >= weapon_upgrade_cost:

            state.gold -= weapon_upgrade_cost
            state.weapon_atk += WEAPON_ATTACK_INCREASE

            message = "Your weapon has been upgraded!"

        else:
            message = "You don't have enough gold for a weapon upgrade!"

    else:
        message = "Invalid purchase!"

    # Return to the shop and display the purchase result.
    return display_shop(state, message)
    
@route
def display_inventory(state: State, previous_page: str = "index") -> Page:
    """Display the player's current inventory and equipment."""

    page_content = [
        Header("Player Inventory"),
        "Here is everything you currently own!\n",

        Header("Character Stats", 2),
        "Level: " + str(state.lvl) + "\n",
        "Experience: " + str(state.exp) + "\n",
        "Gold: " + str(state.gold) + "\n",

        Header("Equipment", 2),
        "Weapon Attack: " + str(state.weapon_atk) + "\n",
        "Player Defense: " + str(state.player_defense) + "\n",

        Header("Consumables", 2),
        "Healing Potions: " + str(state.potion_count) + "\n",

        Button("Return to Previous Page", previous_page)
    ]

    return Page(state, page_content)

@route
def complete_quests(state: State, completed_quests: list[str]) -> Page:
    """Remove completed quests and award their EXP and gold."""

    # Convert the selected quest identifiers into integers.
    selected_indices = []

    for selected in completed_quests:
        selected_indices.append(int(selected))

    # Separate completed quests from remaining quests.
    completed = []
    remaining = []

    for quest_index, quest in enumerate(state.quests):

        if quest_index in selected_indices:
            completed.append(quest)

        else:
            remaining.append(quest)

    # Make sure the player actually selected a quest.
    if len(completed) == 0:
        return index(state, "Please select at least one completed quest!")

    # Calculate the total rewards from completed quests.
    total_exp = 0
    total_gold = 0

    for quest in completed:
        total_exp += quest.exp
        total_gold += quest.gold

    # Replace the active quest list with the remaining quests.
    state.quests = remaining

    # Add the rewards to the player's inventory.
    state.exp += total_exp
    state.gold += total_gold

    # Create a notification describing the rewards.
    message = (
        "You completed " + str(len(completed)) + " quest(s)! "
        + "You earned " + str(total_exp) + " EXP and "
        + str(total_gold) + " Gold!"
    )

    # Check whether the player has enough EXP to level up.
    exp_needed = state.lvl * 100

    if state.exp >= exp_needed:

        state.lvl += 1
        state.exp = 0

        message += " You leveled up to Level " + str(state.lvl) + "!"

    # Return to the Quest Page with the notification.
    return index(state, message)

@route
def add_quest(state: State, error_message: str = "") -> Page:
    """Display the form used to create new quests."""

    page_content = [
        Header("Add a Quest"),
        "Prepare yourself for another adventure!\n",

        Header("Quest Information", 2),

        "Quest Name:",
        TextBox("quest_name"),

        "\nDue Date (MM-DD-YY):",
        TextBox("due_date", placeholder="MM-DD-YY"),

        "\nDifficulty (1-10):",
        SelectBox("difficulty", [
            str(number) for number in range(1, 11)
        ]),

        "\n"
    ]

    # Display an error message if the player's input is invalid.
    if error_message != "":
        page_content.append(error_message)

    page_content.append(Button("Create Quest", "save_quest"))

    return Page(state, page_content)

@route
def save_quest(state: State, quest_name: str,
               due_date: str, difficulty: str) -> Page:
    """Create a quest, calculate its rewards, and save it."""

    # Check whether the player entered a quest name.
    if quest_name.strip() == "":
        return add_quest(state, "Please enter a quest name!")

    # Convert the entered date into a usable date object.
    try:
        parsed_date = datetime.strptime(due_date.strip(), "%m-%d-%y")

    except ValueError:
        return add_quest(state, "Please enter a valid date in MM-DD-YY format!")

    # Convert the date into an integer in YYYYMMDD format.
    date_number = int(parsed_date.strftime("%Y%m%d"))

    # Convert the selected difficulty into an integer.
    difficulty_number = int(difficulty)

    # Calculate the rewards using the player's current level.
    exp_reward, gold_reward = calculate_quest_rewards(
        difficulty_number, state.lvl
    )

    # Create a new Quest instance.
    new_quest = Quest(
        quest_name.strip(),
        difficulty_number,
        date_number,
        exp_reward,
        gold_reward
    )

    # Add the new quest to the player's quest list.
    state.quests.append(new_quest)

    # Sort the quests according to their due dates.
    state.quests.sort(key=lambda quest: quest.date)

    # Return the player to the Quest Page.
    return index(state)

@route
def generate_dungeon_room(state: State) -> Page:
    """Generate the next dungeon room using the current seed."""

    # Make sure the player has an active dungeon.
    if not state.dungeon_active:
        return index(state, "You must enter a dungeon first!")

    # If an encounter already exists, display it again.
    if state.current_encounter != "":
        return display_current_encounter(state)

    # Determine which room the player is entering.
    next_room = state.room_count + 1

    # Generate the encounter using the dungeon seed.
    encounter_type, enemy_type = determine_encounter(
        state.seed, next_room
    )

    # Check whether the dungeon has already ended.
    if encounter_type == "finished":
        return Page(state, [
            Header("Dungeon Complete"),
            "All seven rooms have been explored!",
            "The victory system will be implemented soon."
        ])

    # Update the player's room count.
    state.room_count = next_room

    # Store the current encounter type.
    state.current_encounter = encounter_type
    state.encounter_message = ""

    # Generate an enemy if the encounter requires one.
    if enemy_type is not None:

        state.current_enemy = create_enemy(
            enemy_type,
            state.lvl,
            encounter_type == "strong_enemy"
        )

    else:
        state.current_enemy = None

    # Display the generated encounter.
    return display_current_encounter(state)

@route
def start_dungeon(state: State) -> Page:
    """Initialize a new dungeon run and reset dungeon statistics."""

    # Make sure all quests have been completed.
    if len(state.quests) > 0:
        return index(state, "Complete all your quests before entering a dungeon!")

    # Prevent players from starting a second dungeon.
    if state.dungeon_active:
        return generate_dungeon_room(state)

    # Generate a new six-digit dungeon seed.
    state.seed = create_seed()

    # Restore the player's health.
    state.player_hp = state.max_player_hp

    # Reset dungeon progression.
    state.room_count = 0
    state.current_encounter = ""
    state.current_enemy = None
    state.encounter_message = ""
    state.enemies_defeated = 0

    # Reset dungeon rewards.
    state.dungeon_exp = 0
    state.dungeon_gold = 0

    # Mark the dungeon as active.
    state.dungeon_active = True

    # Display the dungeon entrance.
    return Page(state, [
        Header("Dungeon Entrance"),
        "Prepare yourself, adventurer!",
        "A dangerous journey lies ahead.\n",

        Header("Player Status", 2),
        "HP: " + str(state.player_hp) + "/" + str(state.max_player_hp),
        "Level: " + str(state.lvl),
        "Weapon Attack: " + str(state.weapon_atk),
        "Healing Potions: " + str(state.potion_count) + "\n",

        Header("Dungeon Information", 2),
        "Rooms: 7",
        "Encounters: 6 random rooms and 1 guaranteed Strong Enemy.\n",

        Button("Explore First Room", "generate_dungeon_room")
    ])

# ==========================================
# UNIT TESTS: CALCULATIONS AND ENEMY CREATION
# ==========================================

# calculate_quest_rewards()
assert_equal((10, 5), calculate_quest_rewards(1, 1))
assert_equal((100, 50), calculate_quest_rewards(10, 1))
assert_equal((60, 29), calculate_quest_rewards(5, 3))


# create_seed()
assert_equal(True, 100000 <= create_seed() <= 999999)
assert_equal(True, 100000 <= create_seed() <= 999999)
assert_equal(True, 100000 <= create_seed() <= 999999)


# create_enemy()
_test_bat = create_enemy(0, 1)
assert_equal(("Bat", 20, 2, 0, False),
             (_test_bat.name, _test_bat.hp, _test_bat.attack,
              _test_bat.defense, _test_bat.is_strong))

_test_slime = create_enemy(1, 3)
assert_equal(("Slime", 40, 5, 3),
             (_test_slime.name, _test_slime.hp,
              _test_slime.attack, _test_slime.defense))

_test_strong = create_enemy(7, 2, True)
assert_equal(("Strong Knight Armor", 30, 7, 7, True),
             (_test_strong.name, _test_strong.hp,
              _test_strong.attack, _test_strong.defense,
              _test_strong.is_strong))


# determine_encounter()
assert_equal(("enemy", 1), determine_encounter(123456, 1))
assert_equal("strong_enemy", determine_encounter(123456, 7)[0])

_special_test = determine_encounter(999999, 1)
assert_equal(True, _special_test in [("bush", None), ("chest", None)])

# ==========================================
# UNIT TESTS: DUNGEON DISPLAY FUNCTIONS
# ==========================================

# display_current_encounter()

_test_page = display_current_encounter(State(
    dungeon_active=True,
    current_encounter="enemy",
    current_enemy=Enemy("Bat", 1, 20, 20, 2, 0)
))
assert_equal(Page, type(_test_page))

_test_page = display_current_encounter(State(
    dungeon_active=True,
    current_encounter="bush"
))
assert_equal(Page, type(_test_page))

_test_page = display_current_encounter(State(
    dungeon_active=True,
    current_encounter="chest"
))
assert_equal(Page, type(_test_page))


# display_room_cleared()

assert_equal(Page, type(display_room_cleared(State(), "Test message")))
assert_equal(Page, type(display_room_cleared(State(), "Enemy defeated!")))
assert_equal(Page, type(display_room_cleared(State(), "Bush investigated!")))


# display_dungeon_defeat()

_test_defeat_state = State(
    dungeon_active=True,
    current_encounter="enemy",
    current_enemy=Enemy("Slime", 1, 20, 20, 1, 1),
    dungeon_exp=20,
    dungeon_gold=10
)

_test_page = display_dungeon_defeat(_test_defeat_state)

assert_equal(Page, type(_test_page))
assert_equal(False, _test_defeat_state.dungeon_active)
assert_equal((None, "", 0, 0),
             (_test_defeat_state.current_enemy,
              _test_defeat_state.current_encounter,
              _test_defeat_state.dungeon_exp,
              _test_defeat_state.dungeon_gold))


# display_dungeon_victory()

_test_victory_state = State(
    lvl=1,
    exp=90,
    gold=10,
    dungeon_exp=20,
    dungeon_gold=15,
    dungeon_active=True
)

_test_page = display_dungeon_victory(_test_victory_state)

assert_equal(Page, type(_test_page))
assert_equal((2, 0, 25),
             (_test_victory_state.lvl,
              _test_victory_state.exp,
              _test_victory_state.gold))
assert_equal((0, 0, False, None, ""),
             (_test_victory_state.dungeon_exp,
              _test_victory_state.dungeon_gold,
              _test_victory_state.dungeon_active,
              _test_victory_state.current_enemy,
              _test_victory_state.current_encounter))

# ==========================================
# UNIT TESTS: COMBAT FUNCTIONS
# ==========================================

# attack_enemy()

_test_combat_state = State(
    dungeon_active=True,
    current_encounter="enemy",
    current_enemy=Enemy("Slime", 1, 20, 20, 1, 1),
    weapon_atk=5,
    player_hp=100,
    player_defense=2
)

attack_enemy(_test_combat_state)

assert_equal(16, _test_combat_state.current_enemy.hp)
assert_equal(99, _test_combat_state.player_hp)
assert_equal("enemy", _test_combat_state.current_encounter)


_test_kill_state = State(
    dungeon_active=True,
    room_count=1,
    current_encounter="enemy",
    current_enemy=Enemy("Slime", 1, 4, 4, 1, 1),
    weapon_atk=5
)

attack_enemy(_test_kill_state)

assert_equal(None, _test_kill_state.current_enemy)
assert_equal(1, _test_kill_state.enemies_defeated)
assert_equal((10, 5),
             (_test_kill_state.dungeon_exp,
              _test_kill_state.dungeon_gold))


_test_strong_state = State(
    dungeon_active=True,
    room_count=7,
    current_encounter="strong_enemy",
    current_enemy=Enemy("Strong Bat", 1, 4, 4, 2, 0, True),
    weapon_atk=5,
    dungeon_exp=10,
    dungeon_gold=5
)

attack_enemy(_test_strong_state)

assert_equal((False, 30, 15),
             (_test_strong_state.dungeon_active,
              _test_strong_state.exp,
              _test_strong_state.gold))


# use_potion()

_test_potion_state = State(
    dungeon_active=True,
    current_encounter="enemy",
    current_enemy=Enemy("Slime", 1, 20, 20, 1, 1),
    player_hp=50,
    potion_count=2,
    player_defense=2
)

use_potion(_test_potion_state)

assert_equal(1, _test_potion_state.potion_count)
assert_equal(84, _test_potion_state.player_hp)
assert_equal(20, _test_potion_state.current_enemy.hp)


_test_no_potion = State(
    dungeon_active=True,
    current_encounter="enemy",
    current_enemy=Enemy("Bat", 1, 20, 20, 2, 0),
    player_hp=50,
    potion_count=0
)

use_potion(_test_no_potion)

assert_equal(0, _test_no_potion.potion_count)
assert_equal(50, _test_no_potion.player_hp)
assert_equal("enemy", _test_no_potion.current_encounter)


_test_full_hp = State(
    dungeon_active=True,
    current_encounter="enemy",
    current_enemy=Enemy("Bat", 1, 20, 20, 2, 0),
    player_hp=100,
    potion_count=1
)

use_potion(_test_full_hp)

assert_equal(1, _test_full_hp.potion_count)
assert_equal(100, _test_full_hp.player_hp)
assert_equal("enemy", _test_full_hp.current_encounter)


# run_away()

_test_run_state = State(
    dungeon_active=True,
    room_count=2,
    current_encounter="enemy",
    current_enemy=Enemy("Goblin", 1, 20, 20, 3, 1)
)

run_away(_test_run_state)

assert_equal("", _test_run_state.current_encounter)
assert_equal(None, _test_run_state.current_enemy)
assert_equal(2, _test_run_state.room_count)


_test_strong_run = State(
    dungeon_active=True,
    room_count=7,
    current_encounter="strong_enemy",
    current_enemy=Enemy("Strong Bat", 1, 20, 20, 4, 1, True)
)

run_away(_test_strong_run)

assert_equal("strong_enemy", _test_strong_run.current_encounter)
assert_equal(True, _test_strong_run.current_enemy.is_strong)
assert_equal(7, _test_strong_run.room_count)


_test_no_enemy = run_away(State())
assert_equal(Page, type(_test_no_enemy))
assert_equal(False, State().dungeon_active)
assert_equal(None, State().current_enemy)

# ==========================================
# UNIT TESTS: SPECIAL ENCOUNTERS
# ==========================================

# resolve_bush()

_test_bush_invalid = resolve_bush(State(), "investigate")
assert_equal(Page, type(_test_bush_invalid))
assert_equal("", State().current_encounter)
assert_equal(2, State().potion_count)


_test_bush_leave = State(
    dungeon_active=True,
    current_encounter="bush"
)

resolve_bush(_test_bush_leave, "leave")

assert_equal("", _test_bush_leave.current_encounter)
assert_equal(None, _test_bush_leave.current_enemy)
assert_equal(0, _test_bush_leave.room_count)


# Force both possible bush outcomes.
_original_choice = random.choice

random.choice = lambda options: "potion"

_test_bush_potion = State(
    dungeon_active=True,
    current_encounter="bush"
)

resolve_bush(_test_bush_potion, "investigate")

random.choice = lambda options: "enemy"

_test_bush_enemy = State(
    dungeon_active=True,
    current_encounter="bush"
)

resolve_bush(_test_bush_enemy, "investigate")

random.choice = _original_choice

assert_equal((3, "enemy", True),
             (_test_bush_potion.potion_count,
              _test_bush_enemy.current_encounter,
              _test_bush_enemy.current_enemy is not None))


# resolve_chest()

_test_chest_invalid = resolve_chest(State(), "open")
assert_equal(Page, type(_test_chest_invalid))
assert_equal("", State().current_encounter)
assert_equal(2, State().potion_count)


_test_chest_leave = State(
    dungeon_active=True,
    current_encounter="chest"
)

resolve_chest(_test_chest_leave, "leave")

assert_equal("", _test_chest_leave.current_encounter)
assert_equal(100, _test_chest_leave.player_hp)
assert_equal(0, _test_chest_leave.room_count)


# Force both possible chest outcomes.
_original_randint = random.randint

random.randint = lambda low, high: 1

_test_chest_reward = State(
    dungeon_active=True,
    current_encounter="chest",
    potion_count=2
)

resolve_chest(_test_chest_reward, "open")

random.randint = lambda low, high: 100

_test_chest_trap = State(
    dungeon_active=True,
    current_encounter="chest",
    player_hp=100
)

resolve_chest(_test_chest_trap, "open")

random.randint = _original_randint

assert_equal((4, 50),
             (_test_chest_reward.potion_count,
              _test_chest_trap.player_hp))

# ==========================================
# UNIT TESTS: WEBSITE PAGES
# ==========================================

# index()

assert_equal(Page, type(index(State())))
assert_equal(Page, type(index(State(
    quests=[Quest("Homework", 5, 20261115, 50, 25)]
))))
assert_equal(Page, type(index(State(dungeon_active=True))))


# display_shop()

assert_equal(Page, type(display_shop(State())))
assert_equal(Page, type(display_shop(State(
    quests=[Quest("Homework", 5, 20261115, 50, 25)]
))))
assert_equal(Page, type(display_shop(State(dungeon_active=True))))


# display_inventory()

assert_equal(Page, type(display_inventory(State())))
assert_equal(Page, type(display_inventory(State(), "display_shop")))
assert_equal(Page, type(display_inventory(State(gold=100))))


# add_quest()

assert_equal(Page, type(add_quest(State())))
assert_equal(Page, type(add_quest(State(), "Invalid quest name!")))
assert_equal(Page, type(add_quest(State(gold=100))))

# ==========================================
# UNIT TESTS: QUEST FUNCTIONS
# ==========================================

# purchase_item()

_test_buy_potion = State(gold=30, potion_count=2)

purchase_item(_test_buy_potion, "potion")

assert_equal(10, _test_buy_potion.gold)
assert_equal(3, _test_buy_potion.potion_count)
assert_equal(5.0, _test_buy_potion.weapon_atk)


_test_buy_weapon = State(gold=100, weapon_atk=5.0)

purchase_item(_test_buy_weapon, "weapon")

assert_equal(50, _test_buy_weapon.gold)
assert_equal(7.0, _test_buy_weapon.weapon_atk)
assert_equal(2, _test_buy_weapon.potion_count)

_test_insufficient = State(gold=10, potion_count=2)

purchase_item(_test_insufficient, "potion")

assert_equal(10, _test_insufficient.gold)
assert_equal(2, _test_insufficient.potion_count)
assert_equal(5.0, _test_insufficient.weapon_atk)


# complete_quests()

_test_complete_one = State(
    quests=[Quest("Math Homework", 3, 20261115, 30, 15)]
)

complete_quests(_test_complete_one, ["0"])

assert_equal(0, len(_test_complete_one.quests))
assert_equal(30, _test_complete_one.exp)
assert_equal(15, _test_complete_one.gold)


_test_complete_level = State(
    lvl=1,
    exp=90,
    quests=[Quest("Final Exam", 2, 20261115, 10, 5)]
)

complete_quests(_test_complete_level, ["0"])

assert_equal(2, _test_complete_level.lvl)
assert_equal(0, _test_complete_level.exp)
assert_equal(5, _test_complete_level.gold)


_test_complete_none = State(
    quests=[Quest("Homework", 5, 20261115, 50, 25)]
)

complete_quests(_test_complete_none, [])

assert_equal(1, len(_test_complete_none.quests))
assert_equal(0, _test_complete_none.exp)
assert_equal(0, _test_complete_none.gold)


# save_quest()

_test_blank = State()
_blank_page = save_quest(_test_blank, "", "11-15-26", "3")

assert_equal(Page, type(_blank_page))
assert_equal(0, len(_test_blank.quests))
assert_equal(0, _test_blank.gold)


_test_bad_date = State()
_bad_date_page = save_quest(_test_bad_date, "Homework", "13-40-26", "3")

assert_equal(Page, type(_bad_date_page))
assert_equal(0, len(_test_bad_date.quests))
assert_equal(0, _test_bad_date.exp)


_test_valid_quest = State(
    lvl=2,
    quests=[Quest("Later Task", 2, 20261201, 25, 12)]
)

save_quest(_test_valid_quest, "Earlier Task", "11-15-26", "3")

assert_equal(2, len(_test_valid_quest.quests))
assert_equal(20261115, _test_valid_quest.quests[0].date)
assert_equal((35, 17),
             (_test_valid_quest.quests[0].exp,
              _test_valid_quest.quests[0].gold))

# ==========================================
# UNIT TESTS: DUNGEON INITIALIZATION
# ==========================================

# generate_dungeon_room()

_test_inactive = generate_dungeon_room(State())

assert_equal(Page, type(_test_inactive))
assert_equal(False, State().dungeon_active)
assert_equal(0, State().room_count)


_test_existing_room = State(
    dungeon_active=True,
    room_count=3,
    current_encounter="bush"
)

_test_existing_page = generate_dungeon_room(_test_existing_room)

assert_equal(Page, type(_test_existing_page))
assert_equal(3, _test_existing_room.room_count)
assert_equal("bush", _test_existing_room.current_encounter)


_test_new_room = State(
    seed=123456,
    dungeon_active=True
)

generate_dungeon_room(_test_new_room)

assert_equal(1, _test_new_room.room_count)
assert_equal("enemy", _test_new_room.current_encounter)
assert_equal("Slime", _test_new_room.current_enemy.name)


# start_dungeon()

_test_quest_restriction = State(
    quests=[Quest("Homework", 5, 20261115, 50, 25)]
)

_test_restriction_page = start_dungeon(_test_quest_restriction)

assert_equal(Page, type(_test_restriction_page))
assert_equal(False, _test_quest_restriction.dungeon_active)
assert_equal(1, len(_test_quest_restriction.quests))


_test_new_dungeon = State(
    player_hp=30,
    room_count=4,
    dungeon_exp=20,
    dungeon_gold=10,
    current_encounter="bush"
)

start_dungeon(_test_new_dungeon)

assert_equal(True, _test_new_dungeon.dungeon_active)
assert_equal((100, 0, "", 0, 0),
             (_test_new_dungeon.player_hp,
              _test_new_dungeon.room_count,
              _test_new_dungeon.current_encounter,
              _test_new_dungeon.dungeon_exp,
              _test_new_dungeon.dungeon_gold))


_test_resume = State(
    seed=123456,
    dungeon_active=True,
    room_count=2,
    current_encounter="enemy",
    current_enemy=Enemy("Slime", 1, 20, 20, 1, 1)
)

start_dungeon(_test_resume)

assert_equal(2, _test_resume.room_count)
assert_equal(123456, _test_resume.seed)
assert_equal("Slime", _test_resume.current_enemy.name)

# ==========================================
# UNIT TESTS: DATACLASSES
# ==========================================

# Quest

_test_quest = Quest("Homework", 5, 20261115, 50, 25)

assert_equal("Homework", _test_quest.name)
assert_equal(5, _test_quest.difficulty)
assert_equal((50, 25), (_test_quest.exp, _test_quest.gold))


# Enemy

_test_enemy = Enemy("Bat", 1, 20, 20, 2, 0)

assert_equal("Bat", _test_enemy.name)
assert_equal((20, 20), (_test_enemy.hp, _test_enemy.max_hp))
assert_equal((2, 0, False),
             (_test_enemy.attack, _test_enemy.defense,
              _test_enemy.is_strong))


# State

_test_state = State()

assert_equal(2, _test_state.potion_count)
assert_equal(5.0, _test_state.weapon_atk)
assert_equal(1, _test_state.lvl)

start_server(State())

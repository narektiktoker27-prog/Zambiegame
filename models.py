from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class Player:
    user_id: int
    name: str
    location: str = "safehouse"
    health: int = 100
    infected: bool = False
    alive: bool = True
    hidden: bool = False
    inventory: List[str] = field(default_factory=lambda: ["flashlight"])
    bullets: int = 0
    special_weapon: bool = False
    medicine: bool = False
    healing_bullet: bool = False
    last_action: int = 0
    bites: int = 0


@dataclass
class Zombie:
    zid: int
    location: str
    state: str = "IDLE"
    hp: int = 1
    target_id: Optional[int] = None
    alive: bool = True
    cooldown: int = 0


@dataclass
class GameState:
    chat_id: int
    creator_id: int

    players: Dict[int, Player] = field(default_factory=dict)
    zombies: Dict[int, Zombie] = field(default_factory=dict)

    neighbors: Dict[str, List[str]] = field(default_factory=dict)
    location_names: Dict[str, str] = field(default_factory=dict)

    medicine_location: str = ""
    weapon_location: str = ""
    item_locations: Dict[str, str] = field(default_factory=dict)

    locked: Set[str] = field(default_factory=set)
    unlocked: Set[str] = field(default_factory=set)

    tasks: List[str] = field(default_factory=list)
    completed_tasks: Set[str] = field(default_factory=set)

    clues: Dict[int, List[str]] = field(default_factory=dict)

    phase: str = "LOBBY"
    started_at: float = 0.0
    tick: int = 0
    difficulty: int = 1
    events_seen: int = 0
    last_event_tick: int = 0

    medicine_found: bool = False
    weapon_found: bool = False
    cure_ready: bool = False
    cure_used: bool = False
    finalizing: bool = False

    winner: str = ""
    end_reason: str = ""

    def alive_players(self):
        return [p for p in self.players.values() if p.alive]

    def alive_humans(self):
        return [p for p in self.players.values() if p.alive and not p.infected]

    def alive_infected(self):
        return [p for p in self.players.values() if p.alive and p.infected]

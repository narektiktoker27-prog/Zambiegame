"""Offline smoke tests. No Telegram token/network is needed."""

from types import SimpleNamespace

from game_engine import GameManager
from inventory import has_item


def fake_user(uid, name):
    return SimpleNamespace(id=uid, full_name=name)


def test_two_player_start():
    manager = GameManager()
    game = manager.create(-100, 1)
    manager.join(game, fake_user(1, "A"))
    assert manager.start(game)[0] is False

    manager.join(game, fake_user(2, "B"))
    ok, _ = manager.start(game)
    assert ok
    assert len(game.players) == 2
    assert len(game.zombies) == 4
    assert game.phase == "RUNNING"


def test_objectives_are_distinct():
    manager = GameManager()
    game = manager.create(-101, 1)
    manager.join(game, fake_user(1, "A"))
    manager.join(game, fake_user(2, "B"))
    manager.start(game)
    assert game.medicine_location != game.weapon_location


def test_search_can_find_objective():
    manager = GameManager()
    game = manager.create(-102, 1)
    a = fake_user(1, "A")
    b = fake_user(2, "B")
    manager.join(game, a)
    manager.join(game, b)
    manager.start(game)

    p = game.players[1]
    p.location = game.medicine_location
    result = manager.search(game, p)
    assert game.medicine_found
    assert p.medicine
    assert has_item(p, "medicine")
    assert "բուժիչ" in result.lower()


def test_delete_isolated():
    manager = GameManager()
    manager.create(-103, 1)
    manager.create(-104, 2)
    manager.delete(-103)
    assert manager.get(-103) is None
    assert manager.get(-104) is not None


if __name__ == "__main__":
    test_two_player_start()
    test_objectives_are_distinct()
    test_search_can_find_objective()
    test_delete_isolated()
    print("ALL OFFLINE SMOKE TESTS PASSED")

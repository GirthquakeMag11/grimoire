from grim.statemachine import states


def test_state_init() -> None:
    state_1 = states.state("state_1")
    state_2 = states.state("state_2")
    assert state_1 != state_2

    state_1_dupe = states.state("state_1")
    assert state_1 != state_1_dupe

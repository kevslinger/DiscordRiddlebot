import pytest



@pytest.mark.parametrize("correct", [5, 10])
def test_pass(correct):
    assert correct == correct

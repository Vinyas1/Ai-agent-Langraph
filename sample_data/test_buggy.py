"""
Test cases for buggy_code.py — these SHOULD pass once the bugs are fixed.
Note: agent's fixed code is written to /tmp/main.py inside the sandbox,
so this imports `from main import ...`.
"""
from main import merge_intervals, is_palindrome, flatten


# ── merge_intervals ──────────────────────────────────────────────────

def test_merge_basic():
    assert merge_intervals([[1, 3], [2, 6], [8, 10]]) == [[1, 6], [8, 10]]

def test_merge_unsorted():
    assert merge_intervals([[8, 10], [1, 3], [2, 6]]) == [[1, 6], [8, 10]]

def test_merge_touching():
    assert merge_intervals([[1, 3], [3, 5]]) == [[1, 5]]

def test_merge_contained():
    assert merge_intervals([[1, 10], [2, 5], [3, 7]]) == [[1, 10]]

def test_merge_empty():
    assert merge_intervals([]) == []

def test_merge_single():
    assert merge_intervals([[1, 5]]) == [[1, 5]]


# ── is_palindrome ───────────────────────────────────────────────────

def test_palindrome_simple():
    assert is_palindrome("racecar") == True

def test_palindrome_mixed_case():
    assert is_palindrome("RaceCar") == True

def test_palindrome_with_spaces():
    assert is_palindrome("A man a plan a canal Panama") == True

def test_palindrome_with_punctuation():
    assert is_palindrome("Was it a car or a cat I saw?") == True

def test_palindrome_false():
    assert is_palindrome("hello") == False


# ── flatten ─────────────────────────────────────────────────────────

def test_flatten_basic():
    assert flatten([1, [2, [3]], 4]) == [1, 2, 3, 4]

def test_flatten_deep():
    assert flatten([[[1]], [[2]], [[3]]]) == [1, 2, 3]

def test_flatten_already_flat():
    assert flatten([1, 2, 3]) == [1, 2, 3]

def test_flatten_empty():
    assert flatten([]) == []

def test_flatten_mixed():
    assert flatten([1, [2, 3], [4, [5, 6]]]) == [1, 2, 3, 4, 5, 6]

"""
Sample buggy code — a few classic bugs for the agent to find and fix.
"""


def merge_intervals(intervals):
    """Merge overlapping intervals. e.g. [[1,3],[2,6],[8,10]] -> [[1,6],[8,10]]"""
    if not intervals:
        return []

    # Bug 1: not sorting first — breaks when input isn't pre-sorted
    merged = [intervals[0]]

    for current in intervals[1:]:
        last = merged[-1]
        # Bug 2: using > instead of >= (misses touching intervals like [1,3],[3,5])
        if current[0] > last[1]:
            merged.append(current)
        else:
            # Bug 3: using current[1] instead of max(last[1], current[1])
            last[1] = current[1]

    return merged


def is_palindrome(s):
    """Check if a string is a palindrome (ignoring case and non-alphanumeric)."""
    # Bug 4: not filtering non-alphanumeric characters
    cleaned = s.lower()
    return cleaned == cleaned[::-1]


def flatten(nested_list):
    """Flatten a nested list. e.g. [1,[2,[3]],4] -> [1,2,3,4]"""
    result = []
    for item in nested_list:
        if isinstance(item, list):
            # Bug 5: appending instead of extending (creates nested result)
            result.append(flatten(item))
        else:
            result.append(item)
    return result

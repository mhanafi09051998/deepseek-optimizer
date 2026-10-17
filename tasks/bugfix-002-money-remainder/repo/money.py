"""Bill splitting helpers."""


def split_bill(total_cents: int, people: int) -> list[int]:
    if people <= 0:
        raise ValueError("people must be positive")
    base = total_cents // people
    return [base] * people

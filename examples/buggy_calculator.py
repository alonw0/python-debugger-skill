#!/usr/bin/env python3
"""
Example buggy script for testing the Python Debugger skill.

This script has intentional bugs for you to find using the debugger.
Try to find and fix the 3 bugs!

Expected behavior:
- calculate_average([1, 2, 3, 4, 5]) should return 3.0
- calculate_total_price(items) should return 125.0 (50 + 75)
- process_user_data(users) should return ["ALICE", "BOB", "CHARLIE"]
"""


def calculate_average(numbers):
    """Bug #1: Doesn't handle empty lists"""
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)


def calculate_total_price(items):
    """Bug #2: Mutable default argument"""
    def apply_discount(price, discounts=[]):
        discounts.append(0.1)  # 10% discount accumulates!
        total_discount = sum(discounts)
        return price * (1 - total_discount)

    total = 0
    for item in items:
        total += apply_discount(item['price'])
    return total


def process_user_data(users):
    """Bug #3: Modifying list while iterating"""
    names = []
    for user in users:
        if user.get('active'):
            names.append(user['name'].upper())
        users.remove(user)  # Bug: modifying while iterating
    return names


def main():
    print("=== Bug #1: Empty list handling ===")
    try:
        result = calculate_average([])
        print(f"Average of empty list: {result}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Bug #2: Mutable default argument ===")
    items = [
        {'name': 'Widget', 'price': 50},
        {'name': 'Gadget', 'price': 75},
    ]
    result = calculate_total_price(items)
    print(f"Total price (expected 125.0): {result}")

    # Run again to see the bug compound
    result2 = calculate_total_price(items)
    print(f"Total price second run (expected 125.0): {result2}")

    print("\n=== Bug #3: Modifying while iterating ===")
    users = [
        {'name': 'Alice', 'active': True},
        {'name': 'Bob', 'active': True},
        {'name': 'Charlie', 'active': True},
    ]
    result = process_user_data(users)
    print(f"Active users (expected ['ALICE', 'BOB', 'CHARLIE']): {result}")


if __name__ == "__main__":
    main()

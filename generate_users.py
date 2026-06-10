"""
generate_users.py
─────────────────────────────────────────────
Run this script locally to create a users.json
with properly hashed passwords for production.

Usage:
    python generate_users.py

Then copy the output JSON into your Streamlit
Cloud Secrets as USER_ACCOUNTS, or save as
auth/users.json (do NOT commit this file).
─────────────────────────────────────────────
"""

import hashlib
import json
import getpass
import os


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def main():
    print("\n═══ Cardstel HR System — User Setup ═══\n")

    salt = os.environ.get("PASSWORD_SALT") or input(
        "Enter PASSWORD_SALT (must match your app's env var)\n> "
    ).strip()

    if not salt:
        print("ERROR: Salt cannot be empty.")
        return

    users = {}
    print("\nAdd users (leave username blank to stop):\n")

    while True:
        username = input("Username: ").strip().lower()
        if not username:
            break

        name  = input("Full name: ").strip()
        email = input("Email: ").strip()

        print("Available roles: admin, hr_manager, department_manager, employee")
        role  = input("Role: ").strip().lower()

        password = getpass.getpass("Password (hidden): ")
        confirm  = getpass.getpass("Confirm password: ")

        if password != confirm:
            print("❌ Passwords do not match. Skipping.\n")
            continue

        if len(password) < 8:
            print("❌ Password must be at least 8 characters. Skipping.\n")
            continue

        users[username] = {
            "password_hash": hash_password(password, salt),
            "role":  role,
            "name":  name,
            "email": email
        }
        print(f"✅ Added {username} ({role})\n")

    if not users:
        print("No users added.")
        return

    output = json.dumps(users, indent=2)
    print("\n═══ Generated users.json ═══\n")
    print(output)

    save = input("\nSave to auth/users.json? (y/n): ").strip().lower()
    if save == "y":
        os.makedirs("auth", exist_ok=True)
        with open("auth/users.json", "w") as f:
            f.write(output)
        print("✅ Saved to auth/users.json  ← DO NOT commit this file!")
    else:
        print("\nCopy the JSON above into your Streamlit Secrets as USER_ACCOUNTS.")


if __name__ == "__main__":
    main()

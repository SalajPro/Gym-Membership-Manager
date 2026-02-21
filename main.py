import json
import os
from datetime import date, datetime

DATA_FILE = "gym.json"
Owner = "Owner"


def clearscreen(delay_seconds: float = 0.8) -> None:
    try:
        import time
        time.sleep(delay_seconds)
    except Exception:
        pass
    print("\033[H\033[2J", end="")


def pause(msg: str = "Press Enter to continue...") -> None:
    try:
        input(msg)
    except (EOFError, KeyboardInterrupt):
        pass


def today_iso() -> str:
    return date.today().isoformat()


def parse_iso(d: str) -> date:
    return date.fromisoformat(d)


def now_time_str() -> str:
    return datetime.now().strftime("%H:%M:%S")


def today_ddmmyyyy() -> str:
    return datetime.now().strftime("%d/%m/%Y")


def print_header() -> None:
    print(f"Gym Membership Manager  |  Date: {today_ddmmyyyy()}  Time: {now_time_str()}")
    print("-" * 65)


def is_valid_phone(phone: str) -> bool:
    return phone.isdigit() and len(phone) == 10


def normalize_phone(phone: str) -> str:
    return "".join(ch for ch in phone if ch.isdigit())


def add_months(d: date, months: int) -> date:
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    day = d.day

    if month in (1, 3, 5, 7, 8, 10, 12):
        max_day = 31
    elif month in (4, 6, 9, 11):
        max_day = 30
    else:
        leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        max_day = 29 if leap else 28

    if day > max_day:
        day = max_day

    return date(year, month, day)


def membership_to_months(mem_type: str) -> int:
    mem_type = mem_type.strip().lower()
    if mem_type in ("monthly", "m", "1"):
        return 1
    if mem_type in ("quarterly", "q", "2"):
        return 3
    if mem_type in ("yearly", "y", "12", "annual", "3"):
        return 12
    return 0


def friendly_membership(mem_type: str) -> str:
    mem_type = mem_type.strip().lower()
    if mem_type in ("monthly", "m", "1"):
        return "Monthly"
    if mem_type in ("quarterly", "q", "2"):
        return "Quarterly"
    if mem_type in ("yearly", "y", "12", "annual", "3"):
        return "Yearly"
    return mem_type.title()


# Persistence
def load_data() -> list[dict]:
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "members" in data and isinstance(data["members"], list):
            return data["members"]
        if isinstance(data, list):
            return data
        backup_corrupt_file()
        return []
    except json.JSONDecodeError:
        backup_corrupt_file()
        return []
    except OSError:
        return []
    except Exception:
        return []


def backup_corrupt_file() -> None:
    try:
        if os.path.exists(DATA_FILE):
            bak = DATA_FILE + ".bak"
            with open(DATA_FILE, "r", encoding="utf-8", errors="ignore") as src:
                content = src.read()
            with open(bak, "w", encoding="utf-8") as dst:
                dst.write(content)
    except Exception:
        pass


def save_data(members: list[dict]) -> None:
    payload = {"members": members}
    tmp = DATA_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp, DATA_FILE)
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        raise


def find_member_index_by_phone(members: list[dict], phone: str) -> int:
    for i, m in enumerate(members):
        if m.get("phone") == phone:
            return i
    return -1


def print_member(m: dict, idx: int | None = None) -> None:
    prefix = f"[{idx}] " if idx is not None else ""
    print(
        f"{prefix}Name: {m.get('name','')}\n"
        f"    Phone: {m.get('phone','')}\n"
        f"    Type: {m.get('membership_type','')}\n"
        f"    Start: {m.get('start_date','')}\n"
        f"    Expiry: {m.get('expiry_date','')}\n"
    )


def add_member(members: list[dict]) -> None:
    clearscreen(0)
    print_header() 
    print("=== Add New Member ===")

    name = input("Enter member name: ").strip()
    if not name:
        print("Name cannot be empty.")
        pause()
        return

    raw_phone = input("Enter phone number (10 digits): ").strip()
    phone = normalize_phone(raw_phone)

    if not is_valid_phone(phone):
        print("Invalid phone number. Please enter a 10-digit number (digits only).")
        pause()
        return

    if find_member_index_by_phone(members, phone) != -1:
        print("This phone number already exists. Use Update Member to modify/renew.")
        pause()
        return

    print("Membership type: 1) Monthly  2) Quarterly  3) Yearly")
    mem_choice = input("Choose (1/2/3) or type name: ").strip()
    months = membership_to_months(mem_choice)
    if months == 0:
        months = membership_to_months(mem_choice.lower())
    if months == 0:
        print("Invalid membership type.")
        pause()
        return

    start = date.today()
    expiry = add_months(start, months)

    member = {
        "name": name,
        "phone": phone,
        "membership_type": friendly_membership(mem_choice),
        "start_date": start.isoformat(),
        "expiry_date": expiry.isoformat(),
    }

    members.append(member)
    try:
        save_data(members)
        print("\nMember added successfully")
        print_member(member)
    except Exception as e:
        print(f"\nFailed to save data: {e}")
        members.pop()

    pause()


def view_all_members(members: list[dict]) -> None:
    clearscreen(0)
    print_header()
    print("=== All Members ===")
    if not members:
        print("No members found.")
        pause()
        return

    sorted_members = sorted(members, key=lambda x: (x.get("name", "").lower(), x.get("phone", "")))
    for i, m in enumerate(sorted_members, start=1):
        print_member(m, i)
    pause()


def search_member(members: list[dict]) -> None:
    clearscreen(0)
    print_header()
    print("=== Search Member by Phone ===")
    raw_phone = input("Enter phone number: ").strip()
    phone = normalize_phone(raw_phone)

    if not phone:
        print("Phone cannot be empty.")
        pause()
        return

    exact_idx = find_member_index_by_phone(members, phone)
    if exact_idx != -1:
        print("\nFound\n")
        print_member(members[exact_idx])
        pause()
        return

    matches = [m for m in members if phone in (m.get("phone") or "")]
    if not matches:
        print("No matching member found.")
        pause()
        return

    print(f"\nFound {len(matches)} match(es):\n")
    for i, m in enumerate(matches, start=1):
        print_member(m, i)
    pause()


def show_expired(members: list[dict]) -> None:
    clearscreen(0)
    print_header()
    print("=== Expired Memberships ===")
    if not members:
        print("No members found.")
        pause()
        return

    today = date.today()
    expired = []
    for m in members:
        try:
            exp = parse_iso(m.get("expiry_date", "1900-01-01"))
            if exp < today:
                expired.append(m)
        except Exception:
            expired.append(m)

    if not expired:
        print("No expired memberships")
        pause()
        return

    expired_sorted = sorted(expired, key=lambda x: x.get("expiry_date", "0000-00-00"))
    for i, m in enumerate(expired_sorted, start=1):
        print_member(m, i)

    pause()


def update_member(members: list[dict]) -> None:
    clearscreen(0)
    print_header()
    print("=== Update Member Data ===")
    raw_phone = input("Enter existing member phone number: ").strip()
    phone = normalize_phone(raw_phone)

    idx = find_member_index_by_phone(members, phone)
    if idx == -1:
        print("Member not found.")
        pause()
        return

    member = members[idx]
    clearscreen(0)
    print_header()
    print("Current data:\n")
    print_member(member)

    print("What do you want to update?")
    print("1) Name")
    print("2) Phone")
    print("3) Membership Type (recalculate expiry from same start date)")
    print("4) Renew Membership (start date = today, expiry recalculated)")
    print("5) Cancel")
    choice = input("Enter number: ").strip()

    if choice == "1":
        new_name = input("Enter new name: ").strip()
        if not new_name:
            print("Name cannot be empty.")
            pause()
            return
        member["name"] = new_name

    elif choice == "2":
        new_phone_raw = input("Enter new phone (10 digits): ").strip()
        new_phone = normalize_phone(new_phone_raw)
        if not is_valid_phone(new_phone):
            print("Invalid phone number.")
            pause()
            return
        if new_phone != phone and find_member_index_by_phone(members, new_phone) != -1:
            print("That phone number is already used by another member.")
            pause()
            return
        member["phone"] = new_phone

    elif choice == "3":
        print("Membership type: 1) Monthly  2) Quarterly  3) Yearly")
        mem_choice = input("Choose (1/2/3) or type name: ").strip()
        months = membership_to_months(mem_choice)
        if months == 0:
            months = membership_to_months(mem_choice.lower())
        if months == 0:
            print("Invalid membership type.")
            pause()
            return

        try:
            start = parse_iso(member.get("start_date", today_iso()))
        except Exception:
            start = date.today()
            member["start_date"] = start.isoformat()

        member["membership_type"] = friendly_membership(mem_choice)
        member["expiry_date"] = add_months(start, months).isoformat()

    elif choice == "4":
        print("Membership type: 1) Monthly  2) Quarterly  3) Yearly")
        mem_choice = input("Choose (1/2/3) or type name: ").strip()
        months = membership_to_months(mem_choice)
        if months == 0:
            months = membership_to_months(mem_choice.lower())
        if months == 0:
            print("Invalid membership type.")
            pause()
            return

        start = date.today()
        member["membership_type"] = friendly_membership(mem_choice)
        member["start_date"] = start.isoformat()
        member["expiry_date"] = add_months(start, months).isoformat()

    elif choice == "5":
        print("Cancelled.")
        pause()
        return
    else:
        print("Invalid choice.")
        pause()
        return

    try:
        save_data(members)
        print("\nUpdated successfully\n")
        print_member(member)
    except Exception as e:
        print(f"\nFailed to save data: {e}")
    pause()

def main():
    members = load_data()

    while True:
        clearscreen(0)
        print_header()
        print(f"Welcome {Owner} [GYM Membership Manager]\n")
        print("1. Search Members")
        print("2. View All Members")
        print("3. Show Expired Memberships")
        print("4. Add Member")
        print("5. Update Member data")
        print("6. Exit")

        try:
            user = input("\nEnter number: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if user == "1":
            search_member(members)
        elif user == "2":
            view_all_members(members)
        elif user == "3":
            show_expired(members)
        elif user == "4":
            add_member(members)
        elif user == "5":
            update_member(members)
        elif user == "6":
            print(f"Goodbye {Owner}")
            break
        else:
            print("Invalid Input!")
            pause()


if __name__ == "__main__":
    main()
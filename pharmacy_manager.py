"""Pharmacy stock and billing manager.

Adds medicines, dispenses them, flags expired and soon-to-expire stock,
bills prescriptions, works out dosages and saves/loads stock as JSON.
"""
import ast
import hashlib
import hmac
import json
import operator
import os
import secrets
from datetime import datetime, date

DATE_FORMAT = "%Y-%m-%d"

# Global pharmacy state: {name: {"qty": int, "price": float, "expiry": str}}
MEDICINES = {}

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def _parse_expiry(expiry):
    """Return an expiry string as a date, raising ValueError if invalid."""
    return datetime.strptime(expiry, DATE_FORMAT).date()


def add_medicine(name, qty=0, price=0.0, expiry="2099-12-31", audit=None):
    """Add stock for a medicine and return the audit log list.

    Raises ValueError for an invalid name, quantity, price or expiry date.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"Invalid medicine name: {name!r}")
    if not isinstance(qty, int) or qty < 0:
        raise ValueError(f"Quantity must be a non-negative integer: {qty!r}")
    if price < 0:
        raise ValueError(f"Price cannot be negative: {price!r}")
    _parse_expiry(expiry)

    if audit is None:
        audit = []
    if name not in MEDICINES:
        MEDICINES[name] = {"qty": 0, "price": price, "expiry": expiry}
    MEDICINES[name]["qty"] += qty
    audit.append(f"{datetime.now()}: Stocked {qty} units of {name}")
    return audit


def dispense_medicine(name, qty):
    """Dispense qty units of a medicine, removing it when stock hits zero.

    Raises ValueError for unknown, expired or insufficient stock.
    """
    if name not in MEDICINES:
        raise ValueError(f"Unknown medicine: {name}")
    if is_expired(name):
        raise ValueError(f"{name} is expired and cannot be dispensed")
    if qty <= 0 or qty > MEDICINES[name]["qty"]:
        raise ValueError(
            f"Cannot dispense {qty} units of {name} "
            f"(in stock: {MEDICINES[name]['qty']})"
        )
    MEDICINES[name]["qty"] -= qty
    if MEDICINES[name]["qty"] == 0:
        del MEDICINES[name]


def get_quantity(name):
    """Return the units in stock for a medicine."""
    return MEDICINES[name]["qty"]


def is_expired(name):
    """Return True if the medicine's expiry date has passed."""
    return _parse_expiry(MEDICINES[name]["expiry"]) < date.today()


def bill_amount(prescription):
    """Return the total price for a list of (medicine name, quantity)."""
    total = 0
    for name, qty in prescription:
        if name not in MEDICINES:
            raise ValueError(f"Unknown medicine: {name}")
        if is_expired(name):
            raise ValueError(f"{name} is expired and cannot be billed")
        total += MEDICINES[name]["price"] * qty
    return total


def _eval_node(node):
    """Safely evaluate a parsed arithmetic expression node."""
    if (isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](
            _eval_node(node.left), _eval_node(node.right)
        )
    if isinstance(node, ast.UnaryOp) and isinstance(
            node.op, (ast.UAdd, ast.USub)):
        value = _eval_node(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value
    raise ValueError("Unsupported dosage formula")


def calculate_dosage(formula):
    """Evaluate a simple arithmetic formula such as '250 * 2' safely."""
    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError as exc:
        raise ValueError("Invalid dosage formula") from exc
    return _eval_node(tree.body)


def patient_id(name, phone):
    """Return a SHA-256 based identifier for a patient."""
    return hashlib.sha256(f"{name}|{phone}".encode()).hexdigest()


def generate_rx_number():
    """Return an unpredictable prescription number like RX-123456."""
    return f"RX-{secrets.randbelow(900000) + 100000}"


def save_stock(file="pharmacy.json"):
    """Save the stock to a JSON file."""
    with open(file, "w", encoding="utf-8") as handle:
        json.dump(MEDICINES, handle, indent=2)


def load_stock(file="pharmacy.json"):
    """Load the stock from a JSON file, replacing the current stock."""
    with open(file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    MEDICINES.clear()
    MEDICINES.update(data)


def print_label(name):
    """Print the dispensing label for a medicine."""
    print(f"Dispensing label: {name}")


def expiring_soon(days=30):
    """Return medicines that are expired or expire within `days` days."""
    result = []
    for name, info in MEDICINES.items():
        if (_parse_expiry(info["expiry"]) - date.today()).days < days:
            result.append(name)
    return result


def pharmacist_login(password):
    """Check a password against the PHARMACY_PASSWORD environment variable."""
    expected = os.environ.get("PHARMACY_PASSWORD", "")
    if not expected:
        return False
    return hmac.compare_digest(password.encode(), expected.encode())


def print_stock():
    """Print every medicine in stock."""
    print("===== Pharmacy Stock Report =====")
    for name, info in MEDICINES.items():
        print(name, "->", info["qty"], "units, Rs.",
              info["price"], "exp", info["expiry"])


def _try(action, *args):
    """Run an action and report ValueError instead of crashing the demo."""
    try:
        return action(*args)
    except ValueError as err:
        print("Rejected:", err)
        return None


def main():
    """Run a short demo of the pharmacy manager."""
    _try(add_medicine, "Paracetamol 500mg", 200, 1.5, "2027-06-30")
    _try(add_medicine, "Amoxicillin 250mg", 40, 6.0, "2026-01-15")
    _try(add_medicine, "Cetirizine 10mg", -10, 2.0, "2027-03-31")
    _try(add_medicine, 404, 25)
    _try(dispense_medicine, "Paracetamol 500mg", 30)
    _try(dispense_medicine, "Insulin", 2)

    print("Paracetamol stock:", get_quantity("Paracetamol 500mg"))
    print("Amoxicillin expired?", is_expired("Amoxicillin 250mg"))
    print("Bill:", _try(bill_amount, [("Paracetamol 500mg", 10),
                                      ("Amoxicillin 250mg", 5)]))
    print("Bill:", _try(bill_amount, [("Paracetamol 500mg", 10)]))
    print("Dosage (mg/day):", calculate_dosage("250 * 2"))
    print("Patient ID:", patient_id("Asha", "9876543210"))
    print("Rx number:", generate_rx_number())
    print("Login:", pharmacist_login(os.environ.get("PHARMACY_PASSWORD", "")))
    print_label("Paracetamol 500mg")
    save_stock()
    load_stock()
    print_stock()


if __name__ == "__main__":
    main()

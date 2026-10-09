"""Synthetic content generators (Data Engine §2 seed sources) — English-only.

All content is synthetic/templated (no copyrighted documents); seeded for
reproducibility.
"""
import random

COMPANIES = ["Northwind Analytics", "Bluepeak Systems", "Vantage Retail Group",
             "Helios Energy", "Cobalt Financial", "Meridian Health", "Atlas Logistics"]
DEPARTMENTS = ["Engineering", "Sales", "Operations", "Finance", "Marketing", "People Ops"]
PRODUCTS = ["Orbit CRM", "Pulse Dashboard", "Vertex Payroll", "Nimbus Storage"]
PROJECTS = ["Project Falcon", "Project Aurora", "Project Basalt", "Project Cedar"]
CITIES = ["Seattle", "Austin", "Denver", "Boston", "Portland"]
SURNAMES = ["Chen", "Garcia", "Patel", "Kim", "Okafor", "Novak", "Silva", "Nguyen"]
GIVEN = ["Wei", "Maria", "Arjun", "Jisoo", "Amara", "Petr", "Lucas", "Mei"]
TITLES = ["Senior Engineer", "Product Manager", "Analyst", "Operations Lead", "Designer"]

PALETTES = [  # hex sets drawn from design-system.md business palettes
    ("1F4E79", "2E75B6", "D6E4F0"), ("33544A", "5B8C74", "E3EFE7"),
    ("5B2C6F", "7D4E9E", "EADDF3"), ("7B3B00", "A85F00", "F5E6D3"),
]

QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def finance_series(rng: random.Random, n: int, base=120.0, drift=6.0):
    vals, v = [], base
    for _ in range(n):
        v = max(20.0, v + rng.uniform(-drift, drift * 1.3))
        vals.append(round(v, 1))
    return vals


def person(rng: random.Random, lang: str = "en-US"):
    return f"{rng.choice(GIVEN)} {rng.choice(SURNAMES)}"


def company(rng: random.Random, lang: str = "en-US"):
    return rng.choice(COMPANIES)


def department(rng: random.Random, lang: str = "en-US"):
    return rng.choice(DEPARTMENTS)


def project(rng: random.Random, lang: str = "en-US"):
    return rng.choice(PROJECTS)


def product(rng: random.Random, lang: str = "en-US"):
    return rng.choice(PRODUCTS)


def title_(rng: random.Random, lang: str = "en-US"):
    return rng.choice(TITLES)


def palette(rng: random.Random):
    return rng.choice(PALETTES)


def report_sections(rng: random.Random, lang: str, n: int):
    """n sections (title, body) for a business report."""
    titles = ["Executive Overview", "Performance Analysis", "Key Project Updates",
              "Risks and Challenges", "Next-Step Plan", "Summary and Recommendations"]
    sents = ["The business delivered steady growth this quarter, with core KPIs on target.",
             "Revenue concentration in the main product line increased and retention improved.",
             "Cross-team efficiency rose and delivery lead times shortened versus last quarter.",
             "Cost pressure and regional competition remain the principal risks to monitor.",
             "We recommend expanding channel investment and rebalancing resourcing to sustain growth."]
    rng.shuffle(titles)
    out = []
    for t in titles[:n]:
        body = " ".join(rng.sample(sents, k=min(3, len(sents))))
        out.append((t, body))
    return out


def kpi_rows(rng: random.Random, lang: str, n: int):
    """rows of (name, value, yoy) for report tables / xlsx sheets."""
    rows = []
    for _ in range(n):
        name = product(rng, lang) if rng.random() < 0.5 else department(rng, lang)
        rows.append((name, rng.randrange(120, 980), round(rng.uniform(-0.12, 0.45), 3)))
    return rows


def contract_fields(rng: random.Random, lang: str = "en-US"):
    return {
        "party_a": company(rng, lang), "party_b": company(rng, lang),
        "project": project(rng, lang),
        "amount": f"USD {rng.randrange(50, 900) * 1000:,}",
        "clauses": ["Scope of Services and Delivery", "Fees and Payment", "Intellectual Property",
                    "Confidentiality", "Liability and Termination"],
    }


def exam_items(rng: random.Random, lang: str, n: int):
    pool = [("Multiple choice", "Which of the following is NOT a basic network topology?",
             ["Bus", "Star", "Ring", "Waterfall"]),
            ("Fill in the blank", "The three basic process states are ready, running, and ____.",
             ["blocked"]),
            ("Calculation", "A $240 item is discounted 20%, then reduced by $20. Final price?",
             ["$172"]),
            ("Short answer", "State the ACID properties of database transactions.", [])]
    subject = rng.choice(["Computer Networks", "Operating Systems", "Data Structures", "Calculus"])
    items, seen = [], set()
    while len(items) < min(n, len(pool)):
        idx = rng.randrange(len(pool))
        if idx in seen:
            continue
        seen.add(idx)
        items.append(pool[idx])
    return subject, items

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

RANDOM_SEED = 42
NUM_USERS = 10_000

START_DATE = datetime(2026, 1, 1)
END_DATE = datetime(2026, 6, 30)

NUM_PRODUCTS = 100

# ============================================================
# SESSION CONFIGURATION
# ============================================================

MIN_SESSIONS_PER_USER = 1
MAX_SESSIONS_PER_USER = 8


# ============================================================
# FUNNEL BEHAVIOR
# ============================================================

BASE_PROBABILITIES = {
    "search": 0.60,
    "view_product": 0.85,
    "add_to_cart": 0.30,
    "checkout_start": 0.55,
    "purchase": 0.70,
}


# ============================================================
# PRODUCT ANALYTICS DIMENSIONS
# ============================================================

COUNTRIES = [
    "India",
    "United States",
    "United Kingdom",
    "Canada",
    "Germany",
    "Australia",
]

DEVICES = [
    "web",
    "mobile",
    "tablet",
]

TRAFFIC_SOURCES = [
    "organic",
    "paid_search",
    "social",
    "email",
    "referral",
]

CATEGORIES = [
    "Electronics",
    "Clothing",
    "Home",
    "Beauty",
    "Sports",
    "Books",
    "Toys",
    "Grocery",
    "Accessories",
    "Furniture",
]

EVENT_TYPES = [
    "app_open",
    "signup",
    "login",
    "search",
    "view_product",
    "add_to_cart",
    "remove_from_cart",
    "checkout_start",
    "purchase",
    "logout",
]


# ============================================================
# OUTPUT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

RAW_EVENTS_FILE = RAW_DATA_DIR / "raw_events.csv"


# ============================================================
# RANDOM NUMBER GENERATOR
# ============================================================

rng = np.random.default_rng(RANDOM_SEED)

# ============================================================
# PRODUCT GENERATION
# ============================================================

def generate_products(num_products=NUM_PRODUCTS):
    """
    Generate a synthetic product catalog.
    """

    products = []

    for i in range(1, num_products + 1):
        product_id = f"P{i:04d}"

        category = rng.choice(CATEGORIES)

        price = round(
            rng.uniform(10, 10_000),
            2
        )

        products.append(
            {
                "product_id": product_id,
                "category": category,
                "price": price,
            }
        )

    return pd.DataFrame(products)


# ============================================================
# USER GENERATION
# ============================================================

def generate_users(num_users=NUM_USERS):
    """
    Generate a synthetic user base.
    """

    users = []

    for i in range(1, num_users + 1):
        user_id = f"U{i:05d}"

        signup_date = START_DATE + pd.to_timedelta(
            rng.integers(
                0,
                (END_DATE - START_DATE).days + 1
            ),
            unit="D"
        )

        device = rng.choice(
            DEVICES,
            p=[0.45, 0.45, 0.10]
        )

        country = rng.choice(
            COUNTRIES,
            p=[0.40, 0.20, 0.10, 0.10, 0.10, 0.10]
        )

        traffic_source = rng.choice(
            TRAFFIC_SOURCES,
            p=[0.35, 0.25, 0.15, 0.15, 0.10]
        )

        experiment_group = rng.choice(
            ["control", "treatment"],
            p=[0.50, 0.50]
        )

        users.append(
            {
                "user_id": user_id,
                "signup_date": signup_date,
                "device": device,
                "country": country,
                "traffic_source": traffic_source,
                "experiment_group": experiment_group,
            }
        )

    return pd.DataFrame(users)

# ============================================================
# SESSION GENERATION
# ============================================================

def generate_session_id(session_number):
    """
    Generate a unique session ID.
    """

    return f"S{session_number:07d}"

def generate_session_start(signup_date):
    """
    Generate a session start timestamp on or after signup.
    """

    signup_timestamp = pd.Timestamp(signup_date)

    max_days = max(
        0,
        (END_DATE - signup_timestamp.to_pydatetime()).days
    )

    days_after_signup = rng.integers(
        0,
        max_days + 1
    )

    session_start = (
        signup_timestamp
        + pd.Timedelta(days=int(days_after_signup))
        + pd.Timedelta(
            minutes=int(
                rng.integers(0, 24 * 60)
            )
        )
    )

    return session_start



def get_behavior_adjustments(user):
    """
    Adjust funnel probabilities based on user characteristics.
    """

    adjustments = {
        "search": 0.0,
        "view_product": 0.0,
        "add_to_cart": 0.0,
        "checkout_start": 0.0,
        "purchase": 0.0,
    }

    # --------------------------------------------------------
    # Device effect
    # --------------------------------------------------------

    if user["device"] == "mobile":
        adjustments["add_to_cart"] -= 0.04
        adjustments["purchase"] -= 0.03

    elif user["device"] == "web":
        adjustments["add_to_cart"] += 0.02
        adjustments["purchase"] += 0.02

    # --------------------------------------------------------
    # Traffic source effect
    # --------------------------------------------------------

    if user["traffic_source"] == "organic":
        adjustments["purchase"] += 0.04

    elif user["traffic_source"] == "email":
        adjustments["purchase"] += 0.06

    elif user["traffic_source"] == "social":
        adjustments["purchase"] -= 0.04

    # --------------------------------------------------------
    # A/B test effect
    # --------------------------------------------------------

    if user["experiment_group"] == "treatment":
        adjustments["add_to_cart"] += 0.03
        adjustments["checkout_start"] += 0.02
        adjustments["purchase"] += 0.02

    return adjustments

# ============================================================
# PROBABILITY HELPER
# ============================================================

def adjusted_probability(base_probability, adjustment):
    """
    Apply an adjustment while keeping probability between 0 and 1.
    """

    probability = base_probability + adjustment

    return max(
        0.0,
        min(1.0, probability)
    )

# ============================================================
# SESSION EVENT GENERATION
# ============================================================

def generate_session_events(
    user,
    session_id,
    session_start,
    products,
):
    """
    Generate a realistic sequence of events for one session.
    """

    events = []

    adjustments = get_behavior_adjustments(user)

    def probability(event_name):
        return adjusted_probability(
            BASE_PROBABILITIES[event_name],
            adjustments[event_name],
        )

    # --------------------------------------------------------
    # 1. App open
    # --------------------------------------------------------

    current_time = session_start

    events.append(
        {
            "user_id": user["user_id"],
            "timestamp": current_time,
            "session_id": session_id,
            "event_name": "app_open",
            "product_id": None,
            "category": None,
            "price": None,
            "quantity": None,
            "device": user["device"],
            "country": user["country"],
            "traffic_source": user["traffic_source"],
            "experiment_group": user["experiment_group"],
        }
    )

    # --------------------------------------------------------
    # 2. Search
    # --------------------------------------------------------

    did_search = rng.random() < probability("search")

    if did_search:
        current_time += pd.Timedelta(
            minutes=int(rng.integers(1, 5))
        )

        events.append(
            {
                "user_id": user["user_id"],
                "timestamp": current_time,
                "session_id": session_id,
                "event_name": "search",
                "product_id": None,
                "category": None,
                "price": None,
                "quantity": None,
                "device": user["device"],
                "country": user["country"],
                "traffic_source": user["traffic_source"],
                "experiment_group": user["experiment_group"],
            }
        )

    # --------------------------------------------------------
    # 3. Product view
    # --------------------------------------------------------

    did_view_product = rng.random() < probability("view_product")

    if not did_view_product:
        return events

    current_time += pd.Timedelta(
        minutes=int(rng.integers(1, 5))
    )

    product = products.iloc[
        rng.integers(0, len(products))
    ]

    events.append(
        {
            "user_id": user["user_id"],
            "timestamp": current_time,
            "session_id": session_id,
            "event_name": "view_product",
            "product_id": product["product_id"],
            "category": product["category"],
            "price": product["price"],
            "quantity": None,
            "device": user["device"],
            "country": user["country"],
            "traffic_source": user["traffic_source"],
            "experiment_group": user["experiment_group"],
        }
    )

    # --------------------------------------------------------
    # 4. Add to cart
    # --------------------------------------------------------

    did_add_to_cart = rng.random() < probability("add_to_cart")

    if not did_add_to_cart:
        return events

    current_time += pd.Timedelta(
        minutes=int(rng.integers(1, 5))
    )

    quantity = int(
        rng.choice(
            [1, 2, 3],
            p=[0.75, 0.20, 0.05],
        )
    )

    events.append(
        {
            "user_id": user["user_id"],
            "timestamp": current_time,
            "session_id": session_id,
            "event_name": "add_to_cart",
            "product_id": product["product_id"],
            "category": product["category"],
            "price": product["price"],
            "quantity": quantity,
            "device": user["device"],
            "country": user["country"],
            "traffic_source": user["traffic_source"],
            "experiment_group": user["experiment_group"],
        }
    )

    # --------------------------------------------------------
    # 5. Checkout
    # --------------------------------------------------------

    did_checkout = rng.random() < probability("checkout_start")

    if not did_checkout:
        return events

    current_time += pd.Timedelta(
        minutes=int(rng.integers(1, 5))
    )

    events.append(
        {
            "user_id": user["user_id"],
            "timestamp": current_time,
            "session_id": session_id,
            "event_name": "checkout_start",
            "product_id": product["product_id"],
            "category": product["category"],
            "price": product["price"],
            "quantity": quantity,
            "device": user["device"],
            "country": user["country"],
            "traffic_source": user["traffic_source"],
            "experiment_group": user["experiment_group"],
        }
    )

    # --------------------------------------------------------
    # 6. Purchase
    # --------------------------------------------------------

    did_purchase = rng.random() < probability("purchase")

    if not did_purchase:
        return events

    current_time += pd.Timedelta(
        minutes=int(rng.integers(1, 5))
    )

    events.append(
        {
            "user_id": user["user_id"],
            "timestamp": current_time,
            "session_id": session_id,
            "event_name": "purchase",
            "product_id": product["product_id"],
            "category": product["category"],
            "price": product["price"],
            "quantity": quantity,
            "device": user["device"],
            "country": user["country"],
            "traffic_source": user["traffic_source"],
            "experiment_group": user["experiment_group"],
        }
    )

    return events

# ============================================================
# GENERATE ALL USER EVENTS
# ============================================================

def generate_all_events(users, products):
    """
    Generate sessions and events for all users.
    """

    all_events = []
    session_number = 1

    for _, user in users.iterrows():

        # ----------------------------------------------------
        # Determine number of sessions for this user
        # ----------------------------------------------------

        num_sessions = int(
            rng.integers(
                MIN_SESSIONS_PER_USER,
                MAX_SESSIONS_PER_USER + 1,
            )
        )

        # ----------------------------------------------------
        # Generate sessions
        # ----------------------------------------------------

        for _ in range(num_sessions):

            session_id = generate_session_id(
                session_number
            )

            session_start = generate_session_start(
                user["signup_date"]
            )

            session_events = generate_session_events(
                user=user,
                session_id=session_id,
                session_start=session_start,
                products=products,
            )

            all_events.extend(session_events)

            session_number += 1

    return pd.DataFrame(all_events)

if __name__ == "__main__":

    print("Generating product catalog...")
    products = generate_products()

    print("Generating users...")
    users = generate_users()

    print("Generating user events...")
    events = generate_all_events(
        users=users,
        products=products,
    )

    # --------------------------------------------------------
    # Sort events
    # --------------------------------------------------------

    events = events.sort_values(
        ["user_id", "timestamp", "session_id"]
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # Save raw data
    # --------------------------------------------------------

    events.to_csv(
        RAW_EVENTS_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # Validation summary
    # --------------------------------------------------------

    print()
    print("DATA GENERATION COMPLETE")
    print("========================")
    print(f"Users:  {users['user_id'].nunique():,}")
    print(f"Events: {len(events):,}")
    print(f"Sessions: {events['session_id'].nunique():,}")

    print()
    print("EVENT COUNTS")
    print("============")
    print(
        events["event_name"]
        .value_counts()
        .to_string()
    )

    print()
    print("RAW DATA SAVED TO:")
    print(RAW_EVENTS_FILE)
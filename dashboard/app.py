import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="ShopFlow Product Analytics",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# DATABASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "product_analytics.db"


@st.cache_data
def load_data():
    connection = sqlite3.connect(DB_PATH)

    query = """
    SELECT *
    FROM events
    """

    data = pd.read_sql_query(query, connection)

    connection.close()

    return data


df = load_data()


# ============================================================
# PAGE TITLE
# ============================================================

st.title("📊 ShopFlow Product Analytics")

st.markdown(
    """
    **E-commerce product analytics dashboard**

    Analyze funnel conversion, revenue, user behavior,
    retention, and experimentation.
    """
)


# ============================================================
# DATA SUMMARY
# ============================================================

total_users = df["user_id"].nunique()
total_events = len(df)
total_purchases = (df["event_name"] == "purchase").sum()

purchase_data = df[df["event_name"] == "purchase"].copy()

total_revenue = (
    purchase_data["price"] * purchase_data["quantity"]
).sum()

unique_purchasers = purchase_data["user_id"].nunique()

overall_conversion = (
    unique_purchasers / total_users * 100
)


# ============================================================
# KPI CARDS
# ============================================================

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Users",
        f"{total_users:,}"
    )

with col2:
    st.metric(
        "Events",
        f"{total_events:,}"
    )

with col3:
    st.metric(
        "Purchases",
        f"{total_purchases:,}"
    )

with col4:
    st.metric(
        "Revenue",
        f"${total_revenue:,.0f}"
    )

with col5:
    st.metric(
        "Purchase Conversion",
        f"{overall_conversion:.2f}%"
    )

# ============================================================
# FUNNEL ANALYSIS
# ============================================================

st.divider()

st.subheader("🛒 Conversion Funnel")

funnel_data = pd.DataFrame({
    "Stage": [
        "App Open",
        "View Product",
        "Add to Cart",
        "Checkout Start",
        "Purchase"
    ],
    "Users": [
        df.loc[df["event_name"] == "app_open", "user_id"].nunique(),
        df.loc[df["event_name"] == "view_product", "user_id"].nunique(),
        df.loc[df["event_name"] == "add_to_cart", "user_id"].nunique(),
        df.loc[df["event_name"] == "checkout_start", "user_id"].nunique(),
        df.loc[df["event_name"] == "purchase", "user_id"].nunique()
    ]
})

# Calculate conversion and drop-off
funnel_data["Conversion from Previous (%)"] = (
    funnel_data["Users"]
    .div(funnel_data["Users"].shift(1))
    .mul(100)
)

funnel_data["Drop-off Users"] = (
    funnel_data["Users"].shift(1) - funnel_data["Users"]
)

funnel_data["Drop-off (%)"] = (
    funnel_data["Drop-off Users"]
    .div(funnel_data["Users"].shift(1))
    .mul(100)
)


# ------------------------------------------------------------
# Funnel chart
# ------------------------------------------------------------

st.bar_chart(
    funnel_data.set_index("Stage")["Users"],
    horizontal=True
)


# ------------------------------------------------------------
# Funnel metrics
# ------------------------------------------------------------

st.dataframe(
    funnel_data.style.format({
        "Users": "{:,.0f}",
        "Conversion from Previous (%)": "{:.2f}%",
        "Drop-off Users": "{:,.0f}",
        "Drop-off (%)": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)
# ============================================================
# PROJECT OVERVIEW
# ============================================================

st.divider()

st.subheader("Project Overview")

st.write(
    """
    This dashboard analyzes the ShopFlow e-commerce customer journey
    from product discovery through purchase. It combines funnel
    analysis, acquisition performance, revenue analytics, retention,
    and A/B testing to identify product growth opportunities.
    """
)


# ============================================================
# KEY FINDINGS
# ============================================================

st.subheader("Key Findings")

col1, col2 = st.columns(2)

with col1:

    st.markdown(
        """
        **🛒 Funnel**

        Overall purchase conversion is **37.56%**.

        The largest funnel drop-off occurs between
        **product view and add to cart**.
        """
    )

    st.markdown(
        """
        **📱 Device**

        Mobile conversion is **34.01%**, compared with
        **40.60% on web**.
        """
    )

with col2:

    st.markdown(
        """
        **🧪 Experiment**

        Treatment conversion is **40.88%** compared with
        **34.17% for control**, a **19.65% relative lift**.
        """
    )

    st.markdown(
        """
        **💰 Revenue**

        Total purchase revenue is approximately
        **$30.21M**.
        """
    )


# ============================================================
# DATA PREVIEW
# ============================================================

with st.expander("View event data"):

    st.dataframe(
        df.head(100),
        use_container_width=True
    )
# ============================================================
# DEVICE PERFORMANCE
# ============================================================

st.divider()

st.subheader("📱 Conversion by Device")

device_funnel = (
    df.groupby("device")
    .apply(
        lambda x: pd.Series({
            "Users": x["user_id"].nunique(),
            "Purchasers": x.loc[
                x["event_name"] == "purchase",
                "user_id"
            ].nunique()
        }),
        include_groups=False
    )
    .reset_index()
)

device_funnel["Conversion (%)"] = (
    device_funnel["Purchasers"]
    / device_funnel["Users"]
    * 100
)

device_funnel = device_funnel.sort_values(
    "Conversion (%)",
    ascending=False
)


# ------------------------------------------------------------
# Device conversion chart
# ------------------------------------------------------------

st.bar_chart(
    device_funnel.set_index("device")["Conversion (%)"],
    horizontal=True
)


# ------------------------------------------------------------
# Device metrics table
# ------------------------------------------------------------

st.dataframe(
    device_funnel.style.format({
        "Users": "{:,.0f}",
        "Purchasers": "{:,.0f}",
        "Conversion (%)": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)

# ============================================================
# REVENUE & ACQUISITION
# ============================================================

st.divider()

st.subheader("💰 Revenue & Acquisition")


# ============================================================
# REVENUE KPIs
# ============================================================

purchase_df = df[df["event_name"] == "purchase"].copy()

purchase_df["revenue"] = (
    purchase_df["price"] * purchase_df["quantity"]
)

total_revenue = purchase_df["revenue"].sum()

average_order_value = (
    purchase_df["revenue"].sum()
    / len(purchase_df)
)

revenue_per_purchaser = (
    purchase_df["revenue"].sum()
    / purchase_df["user_id"].nunique()
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Revenue",
        f"${total_revenue:,.0f}"
    )

with col2:
    st.metric(
        "Average Order Value",
        f"${average_order_value:,.2f}"
    )

with col3:
    st.metric(
        "Revenue per Purchaser",
        f"${revenue_per_purchaser:,.2f}"
    )


# ============================================================
# REVENUE BY TRAFFIC SOURCE
# ============================================================

st.subheader("Revenue by Traffic Source")

source_revenue = (
    purchase_df
    .groupby("traffic_source")
    .agg(
        Purchases=("user_id", "size"),
        Unique_Purchasers=("user_id", "nunique"),
        Revenue=("revenue", "sum")
    )
    .reset_index()
)

source_revenue["AOV"] = (
    source_revenue["Revenue"]
    / source_revenue["Purchases"]
)

source_revenue["Revenue_per_Purchaser"] = (
    source_revenue["Revenue"]
    / source_revenue["Unique_Purchasers"]
)

source_revenue = source_revenue.sort_values(
    "Revenue",
    ascending=False
)


st.bar_chart(
    source_revenue.set_index("traffic_source")["Revenue"],
    horizontal=True
)

st.dataframe(
    source_revenue.style.format({
        "Purchases": "{:,.0f}",
        "Unique_Purchasers": "{:,.0f}",
        "Revenue": "${:,.2f}",
        "AOV": "${:,.2f}",
        "Revenue_per_Purchaser": "${:,.2f}"
    }),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# REVENUE BY CATEGORY
# ============================================================

st.subheader("Revenue by Product Category")

category_revenue = (
    purchase_df
    .groupby("category")
    .agg(
        Purchases=("user_id", "size"),
        Unique_Purchasers=("user_id", "nunique"),
        Revenue=("revenue", "sum")
    )
    .reset_index()
)

category_revenue["AOV"] = (
    category_revenue["Revenue"]
    / category_revenue["Purchases"]
)

category_revenue = category_revenue.sort_values(
    "Revenue",
    ascending=False
)


st.bar_chart(
    category_revenue.set_index("category")["Revenue"],
    horizontal=True
)

st.dataframe(
    category_revenue.style.format({
        "Purchases": "{:,.0f}",
        "Unique_Purchasers": "{:,.0f}",
        "Revenue": "${:,.2f}",
        "AOV": "${:,.2f}"
    }),
    use_container_width=True,
    hide_index=True
)

# ============================================================
# RETENTION ANALYSIS
# ============================================================

st.divider()

st.subheader("🔄 User Retention")

# First activity date for each user
first_activity = (
    df.groupby("user_id")["timestamp"]
    .min()
    .reset_index()
)

first_activity["first_date"] = pd.to_datetime(
    first_activity["timestamp"]
).dt.date


# Unique user activity dates
activity_dates = df[["user_id", "timestamp"]].copy()

activity_dates["activity_date"] = pd.to_datetime(
    activity_dates["timestamp"]
).dt.date

activity_dates = activity_dates[
    ["user_id", "activity_date"]
].drop_duplicates()


# Maximum date available in dataset
max_date = activity_dates["activity_date"].max()


# ------------------------------------------------------------
# Calculate D1 / D7 / D30 retention
# ------------------------------------------------------------

retention_results = []

for days in [1, 7, 30]:

    first_activity["target_date"] = (
        pd.to_datetime(first_activity["first_date"])
        + pd.Timedelta(days=days)
    ).dt.date

    eligible = first_activity[
        first_activity["target_date"] <= max_date
    ].copy()

    retained = eligible.merge(
        activity_dates,
        left_on=["user_id", "target_date"],
        right_on=["user_id", "activity_date"],
        how="inner"
    )["user_id"].nunique()

    eligible_users = eligible["user_id"].nunique()

    retention_rate = (
        retained / eligible_users * 100
        if eligible_users > 0
        else 0
    )

    retention_results.append({
        "Metric": f"D{days}",
        "Eligible Users": eligible_users,
        "Retained Users": retained,
        "Retention (%)": retention_rate
    })


retention_df = pd.DataFrame(retention_results)


# ------------------------------------------------------------
# Retention metrics
# ------------------------------------------------------------

col1, col2, col3 = st.columns(3)

for col, metric in zip(
    [col1, col2, col3],
    ["D1", "D7", "D30"]
):

    row = retention_df[
        retention_df["Metric"] == metric
    ].iloc[0]

    with col:
        st.metric(
            f"{metric} Retention",
            f"{row['Retention (%)']:.2f}%"
        )


st.bar_chart(
    retention_df.set_index("Metric")["Retention (%)"]
)

st.dataframe(
    retention_df.style.format({
        "Eligible Users": "{:,.0f}",
        "Retained Users": "{:,.0f}",
        "Retention (%)": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# A/B TESTING
# ============================================================

st.subheader("🧪 A/B Test Results")

experiment = (
    df.groupby("experiment_group")
    .agg(
        Users=("user_id", "nunique")
    )
    .reset_index()
)

purchasers = (
    df[df["event_name"] == "purchase"]
    .groupby("experiment_group")["user_id"]
    .nunique()
    .reset_index(name="Purchasers")
)

experiment = experiment.merge(
    purchasers,
    on="experiment_group",
    how="left"
)

experiment["Conversion (%)"] = (
    experiment["Purchasers"]
    / experiment["Users"]
    * 100
)


# ------------------------------------------------------------
# Calculate lift
# ------------------------------------------------------------

control_rate = experiment.loc[
    experiment["experiment_group"] == "control",
    "Conversion (%)"
].iloc[0]

treatment_rate = experiment.loc[
    experiment["experiment_group"] == "treatment",
    "Conversion (%)"
].iloc[0]

absolute_lift = treatment_rate - control_rate

relative_lift = (
    absolute_lift / control_rate * 100
)


# ------------------------------------------------------------
# Display experiment metrics
# ------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Control Conversion",
        f"{control_rate:.2f}%"
    )

with col2:
    st.metric(
        "Treatment Conversion",
        f"{treatment_rate:.2f}%"
    )

with col3:
    st.metric(
        "Absolute Lift",
        f"+{absolute_lift:.2f} pp"
    )

with col4:
    st.metric(
        "Relative Lift",
        f"+{relative_lift:.2f}%"
    )


st.bar_chart(
    experiment.set_index("experiment_group")["Conversion (%)"]
)


st.dataframe(
    experiment.style.format({
        "Users": "{:,.0f}",
        "Purchasers": "{:,.0f}",
        "Conversion (%)": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)


st.info(
    "The treatment group shows a 6.71 percentage-point "
    "conversion improvement over control. The statistical "
    "significance test is documented in src/analyze_ab_test.py."
)
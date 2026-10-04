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

    data = pd.read_sql_query(
        "SELECT * FROM events",
        connection
    )

    connection.close()

    data["timestamp"] = pd.to_datetime(
        data["timestamp"]
    )

    return data


df = load_data()


# ============================================================
# COMMON CALCULATIONS
# ============================================================

purchase_df = df[
    df["event_name"] == "purchase"
].copy()

purchase_df["revenue"] = (
    purchase_df["price"] * purchase_df["quantity"]
)

total_users = df["user_id"].nunique()
total_events = len(df)
total_purchases = len(purchase_df)
unique_purchasers = purchase_df["user_id"].nunique()

total_revenue = purchase_df["revenue"].sum()

average_order_value = (
    total_revenue / total_purchases
)

revenue_per_purchaser = (
    total_revenue / unique_purchasers
)

purchase_conversion = (
    unique_purchasers / total_users * 100
)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.title("📊 ShopFlow")

st.sidebar.markdown(
    "### Product Analytics"
)

page = st.sidebar.radio(
    "Navigate",
    [
        "Overview",
        "Funnel",
        "Revenue",
        "Retention",
        "Experimentation"
    ]
)

st.sidebar.divider()

st.sidebar.caption(
    "ShopFlow is a fictional e-commerce product "
    "used for portfolio analysis."
)


# ============================================================
# PAGE HEADER
# ============================================================

st.title("ShopFlow Product Analytics")

st.caption(
    "E-commerce product analytics dashboard"
)


# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":

    st.header("Executive Overview")

    st.markdown(
        """
        Analyze the ShopFlow customer journey from product
        discovery through purchase using funnel analytics,
        acquisition performance, revenue, retention, and
        experimentation.
        """
    )

    st.divider()

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

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
            "Conversion",
            f"{purchase_conversion:.2f}%"
        )

    st.divider()

    # --------------------------------------------------------
    # KEY FINDINGS
    # --------------------------------------------------------

    st.header("Key Findings")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("🛒 Funnel")

        st.write(
            f"Overall purchase conversion is "
            f"**{purchase_conversion:.2f}%**."
        )

        st.write(
            "The largest funnel drop-off occurs between "
            "**product view and add to cart**."
        )

        st.subheader("📱 Device")

        st.write(
            "Mobile conversion is **34.01%**, compared "
            "with **40.60%** on web."
        )

    with col2:

        st.subheader("🧪 Experiment")

        st.write(
            "Treatment conversion is **40.88%** compared "
            "with **34.17%** for control."
        )

        st.write(
            "This represents a **19.65% relative lift**."
        )

        st.subheader("💰 Revenue")

        st.write(
            f"Total purchase revenue is approximately "
            f"**${total_revenue:,.2f}**."
        )

    st.divider()

    st.header("Project Scope")

    st.markdown(
        """
        This project demonstrates:

        - SQL analytics
        - ETL pipeline development
        - SQLite data modeling
        - Funnel and conversion analysis
        - User segmentation
        - Revenue analytics
        - Cohort retention
        - A/B testing and statistical significance
        - Streamlit dashboard development
        """
    )


# ============================================================
# FUNNEL
# ============================================================

elif page == "Funnel":

    st.header("🛒 Conversion Funnel")

    funnel_data = pd.DataFrame({
        "Stage": [
            "App Open",
            "View Product",
            "Add to Cart",
            "Checkout Start",
            "Purchase"
        ],
        "Users": [
            df.loc[
                df["event_name"] == "app_open",
                "user_id"
            ].nunique(),

            df.loc[
                df["event_name"] == "view_product",
                "user_id"
            ].nunique(),

            df.loc[
                df["event_name"] == "add_to_cart",
                "user_id"
            ].nunique(),

            df.loc[
                df["event_name"] == "checkout_start",
                "user_id"
            ].nunique(),

            df.loc[
                df["event_name"] == "purchase",
                "user_id"
            ].nunique()
        ]
    })

    funnel_data["Conversion from Previous (%)"] = (
        funnel_data["Users"]
        .div(funnel_data["Users"].shift(1))
        .mul(100)
    )

    funnel_data["Drop-off Users"] = (
        funnel_data["Users"].shift(1)
        - funnel_data["Users"]
    )

    funnel_data["Drop-off (%)"] = (
        funnel_data["Drop-off Users"]
        .div(funnel_data["Users"].shift(1))
        .mul(100)
    )

    # --------------------------------------------------------
    # Funnel chart
    # --------------------------------------------------------

    st.bar_chart(
        funnel_data.set_index("Stage")["Users"],
        horizontal=True
    )

    # --------------------------------------------------------
    # Funnel table
    # --------------------------------------------------------

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

    st.divider()

    # --------------------------------------------------------
    # DEVICE FUNNEL
    # --------------------------------------------------------

    st.header("📱 Conversion by Device")

    device_data = []

    for device, group in df.groupby("device"):

        users = group["user_id"].nunique()

        purchasers = group.loc[
            group["event_name"] == "purchase",
            "user_id"
        ].nunique()

        device_data.append({
            "Device": device,
            "Users": users,
            "Purchasers": purchasers,
            "Conversion (%)": (
                purchasers / users * 100
            )
        })

    device_df = pd.DataFrame(device_data)

    device_df = device_df.sort_values(
        "Conversion (%)",
        ascending=False
    )

    st.bar_chart(
        device_df.set_index("Device")["Conversion (%)"],
        horizontal=True
    )

    st.dataframe(
        device_df.style.format({
            "Users": "{:,.0f}",
            "Purchasers": "{:,.0f}",
            "Conversion (%)": "{:.2f}%"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.info(
        "Mobile conversion is 34.01%, compared with "
        "40.60% on web — a 6.59 percentage-point gap."
    )


# ============================================================
# REVENUE
# ============================================================

elif page == "Revenue":

    st.header("💰 Revenue & Acquisition")

    # --------------------------------------------------------
    # Revenue KPIs
    # --------------------------------------------------------

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

    st.divider()

    # --------------------------------------------------------
    # Revenue by Traffic Source
    # --------------------------------------------------------

    st.header("📣 Revenue by Traffic Source")

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

    source_revenue["Revenue per Purchaser"] = (
        source_revenue["Revenue"]
        / source_revenue["Unique_Purchasers"]
    )

    source_revenue = source_revenue.sort_values(
        "Revenue",
        ascending=False
    )

    st.bar_chart(
        source_revenue.set_index(
            "traffic_source"
        )["Revenue"],
        horizontal=True
    )

    st.dataframe(
        source_revenue.style.format({
            "Purchases": "{:,.0f}",
            "Unique_Purchasers": "{:,.0f}",
            "Revenue": "${:,.2f}",
            "AOV": "${:,.2f}",
            "Revenue per Purchaser": "${:,.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # --------------------------------------------------------
    # Revenue by Category
    # --------------------------------------------------------

    st.header("🛍️ Revenue by Product Category")

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
        category_revenue.set_index(
            "category"
        )["Revenue"],
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
# RETENTION
# ============================================================

elif page == "Retention":

    st.header("🔄 User Retention")

    first_activity = (
        df.groupby("user_id")["timestamp"]
        .min()
        .reset_index()
    )

    first_activity["first_date"] = (
        first_activity["timestamp"].dt.date
    )

    activity_dates = df[
        ["user_id", "timestamp"]
    ].copy()

    activity_dates["activity_date"] = (
        activity_dates["timestamp"].dt.date
    )

    activity_dates = activity_dates[
        ["user_id", "activity_date"]
    ].drop_duplicates()

    max_date = activity_dates["activity_date"].max()

    retention_results = []

    for days in [1, 7, 30]:

        first_activity["target_date"] = (
            pd.to_datetime(
                first_activity["first_date"]
            )
            + pd.Timedelta(days=days)
        ).dt.date

        eligible = first_activity[
            first_activity["target_date"] <= max_date
        ].copy()

        retained = eligible.merge(
            activity_dates,
            left_on=[
                "user_id",
                "target_date"
            ],
            right_on=[
                "user_id",
                "activity_date"
            ],
            how="inner"
        )["user_id"].nunique()

        eligible_users = (
            eligible["user_id"].nunique()
        )

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

    retention_df = pd.DataFrame(
        retention_results
    )

    # --------------------------------------------------------
    # Retention KPIs
    # --------------------------------------------------------

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
        retention_df.set_index(
            "Metric"
        )["Retention (%)"]
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

    st.info(
        "Retention is calculated only among users who have "
        "enough observation time for each measurement point."
    )


# ============================================================
# EXPERIMENTATION
# ============================================================

elif page == "Experimentation":

    st.header("🧪 A/B Test Results")

    experiment = (
        df.groupby("experiment_group")
        .agg(
            Users=("user_id", "nunique")
        )
        .reset_index()
    )

    purchasers = (
        purchase_df
        .groupby("experiment_group")["user_id"]
        .nunique()
        .reset_index(
            name="Purchasers"
        )
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

    control_rate = experiment.loc[
        experiment["experiment_group"] == "control",
        "Conversion (%)"
    ].iloc[0]

    treatment_rate = experiment.loc[
        experiment["experiment_group"] == "treatment",
        "Conversion (%)"
    ].iloc[0]

    absolute_lift = (
        treatment_rate - control_rate
    )

    relative_lift = (
        absolute_lift
        / control_rate
        * 100
    )

    # --------------------------------------------------------
    # Experiment KPIs
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Control",
            f"{control_rate:.2f}%"
        )

    with col2:
        st.metric(
            "Treatment",
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

    st.divider()

    st.bar_chart(
        experiment.set_index(
            "experiment_group"
        )["Conversion (%)"]
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

    st.success(
        "The treatment increased conversion by "
        "6.71 percentage points (19.65% relative lift). "
        "The statistical test in src/analyze_ab_test.py "
        "found the result statistically significant."
    )
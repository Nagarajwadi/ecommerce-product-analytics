import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
from src.experimentation import (
    difference_confidence_interval,
    two_proportion_z_test,
)

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
    # Read-only connection protects the local analytics database.
    readonly_uri = f"{DB_PATH.resolve().as_uri()}?mode=ro"
    with sqlite3.connect(readonly_uri, uri=True) as connection:
        data = pd.read_sql_query("SELECT * FROM events", connection)

    data["timestamp"] = pd.to_datetime(data["timestamp"])
    return data


@st.cache_data
def load_sql_result(relative_path: str) -> pd.DataFrame:
    """Run a repository SQL analysis using a read-only SQLite connection."""
    query_path = BASE_DIR / relative_path
    query = query_path.read_text(encoding="utf-8")
    readonly_uri = f"{DB_PATH.resolve().as_uri()}?mode=ro"
    with sqlite3.connect(readonly_uri, uri=True) as connection:
        return pd.read_sql_query(query, connection)


df = load_data()
funnel_sql = load_sql_result("sql/sequential_funnel.sql")
segment_sql = load_sql_result("sql/segment_conversion.sql")
engagement_sql = load_sql_result("sql/engagement_conversion.sql")


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
        "Segmentation",
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
            "The largest drop-off is calculated from the "
            "ordered session funnel on the Funnel page."
        )

        st.subheader("📱 Segmentation")

        device_segments = segment_sql[
            segment_sql["segment_type"] == "device"
        ].sort_values("conversion_pct", ascending=False)

        if not device_segments.empty:
            best_device = device_segments.iloc[0]
            st.write(
                f"Highest observed device conversion: **{best_device['segment']}** "
                f"({best_device['conversion_pct']:.2f}%)."
            )
            st.caption(
                "Descriptive user-level comparison; device is assigned from "
                "each user's earliest observed event."
            )

    with col2:

        st.subheader("🧪 Experiment")

        st.write(
            "See the Experimentation page for conversion by assignment group."
        )

        st.caption(
            "These synthetic results are educational and should not be "
            "interpreted causally without validating assignment and exposure."
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

    stage_labels = {
        "app_open": "App Open",
        "view_product": "View Product",
        "add_to_cart": "Add to Cart",
        "checkout_start": "Checkout Start",
        "purchase": "Purchase",
    }
    funnel_data = funnel_sql.copy()
    funnel_data["Stage"] = funnel_data["stage"].map(stage_labels)
    funnel_data = funnel_data.rename(columns={
        "sessions": "Sessions",
        "conversion_from_previous_pct": "Conversion from Previous (%)",
        "drop_off_sessions": "Drop-off Sessions",
        "drop_off_pct": "Drop-off (%)",
        "conversion_from_entry_pct": "Conversion from Entry (%)",
    })

    # --------------------------------------------------------
    # Funnel chart
    # --------------------------------------------------------

    st.caption(
        "This is an ordered, session-level funnel. A session advances only "
        "when each event occurs strictly after the previous stage in the same "
        "session. One user may contribute multiple sessions."
    )

    st.bar_chart(
        funnel_data.set_index("Stage")["Sessions"],
        horizontal=True
    )

    # --------------------------------------------------------
    # Funnel table
    # --------------------------------------------------------

    st.dataframe(
        funnel_data[[
            "Stage", "Sessions", "Conversion from Previous (%)",
            "Drop-off Sessions", "Drop-off (%)", "Conversion from Entry (%)"
        ]].style.format({
            "Sessions": "{:,.0f}",
            "Conversion from Previous (%)": "{:.2f}%",
            "Drop-off Sessions": "{:,.0f}",
            "Drop-off (%)": "{:.2f}%",
            "Conversion from Entry (%)": "{:.2f}%"
        }, na_rep="—"),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # --------------------------------------------------------
    # DEVICE FUNNEL
    # --------------------------------------------------------

    st.header("📱 Conversion by Device")

    device_df = segment_sql[
        segment_sql["segment_type"] == "device"
    ][["segment", "users", "purchasers", "non_purchasers", "conversion_pct"]]
    device_df = device_df.rename(columns={
        "segment": "Device",
        "users": "Users",
        "purchasers": "Purchasers",
        "non_purchasers": "Non-purchasers",
        "conversion_pct": "Conversion (%)",
    }).sort_values("Conversion (%)", ascending=False)

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

    st.caption(
        "Each user is assigned to the device from their earliest observed event. "
        "These are descriptive comparisons, not causal estimates."
    )


# ============================================================
# SEGMENTATION
# ============================================================

elif page == "Segmentation":

    st.header("🧭 User Conversion Segmentation")
    st.caption(
        "Each user is counted once per dimension and assigned to the device "
        "and traffic source on their earliest observed event. Results are "
        "descriptive; traffic source is not a verified campaign attribution."
    )

    for segment_type, heading in [
        ("device", "Conversion by Device"),
        ("traffic_source", "Conversion by Traffic Source"),
    ]:
        st.subheader(heading)
        segment_df = segment_sql[
            segment_sql["segment_type"] == segment_type
        ][["segment", "users", "purchasers", "non_purchasers", "conversion_pct"]]
        segment_df = segment_df.rename(columns={
            "segment": "Segment",
            "users": "Users",
            "purchasers": "Purchasers",
            "non_purchasers": "Non-purchasers",
            "conversion_pct": "Conversion (%)",
        }).sort_values("Conversion (%)", ascending=False)

        if segment_df.empty:
            st.info("No segment data is available.")
            continue

        st.bar_chart(segment_df.set_index("Segment")["Conversion (%)"], horizontal=True)
        st.dataframe(
            segment_df.style.format({
                "Users": "{:,.0f}",
                "Purchasers": "{:,.0f}",
                "Non-purchasers": "{:,.0f}",
                "Conversion (%)": "{:.2f}%",
            }),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    st.subheader("Conversion by Engagement")
    st.caption(
        "Engagement is proxied by the number of distinct sessions observed per user. "
        "This is descriptive; users with longer observation windows may accumulate more sessions."
    )
    engagement_df = engagement_sql.rename(columns={
        "segment": "Engagement Segment",
        "users": "Users",
        "purchasers": "Purchasers",
        "non_purchasers": "Non-purchasers",
        "conversion_pct": "Conversion (%)",
        "avg_sessions_per_user": "Avg. Sessions per User",
    })
    st.bar_chart(
        engagement_df.set_index("Engagement Segment")["Conversion (%)"],
        horizontal=True,
    )
    st.dataframe(
        engagement_df.style.format({
            "Users": "{:,.0f}",
            "Purchasers": "{:,.0f}",
            "Non-purchasers": "{:,.0f}",
            "Conversion (%)": "{:.2f}%",
            "Avg. Sessions per User": "{:.2f}",
        }),
        use_container_width=True,
        hide_index=True,
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

    # --------------------------------------------------------
    # COHORT RETENTION
    # --------------------------------------------------------

    st.divider()
    st.subheader("📅 Cohort Retention by First Observed Activity")

    cohort_sql_path = BASE_DIR / "sql" / "retention_cohorts.sql"
    cohort_query = cohort_sql_path.read_text(encoding="utf-8")

    # Open a separate read-only connection; this view never writes to SQLite.
    readonly_uri = f"{DB_PATH.resolve().as_uri()}?mode=ro"
    with sqlite3.connect(readonly_uri, uri=True) as cohort_connection:
        cohort_df = pd.read_sql_query(cohort_query, cohort_connection)

    if cohort_df.empty:
        st.warning("No cohort retention results are available.")
    else:
        chart_columns = [
            "d1_retention_pct",
            "d7_retention_pct",
            "d30_retention_pct",
        ]
        st.line_chart(
            cohort_df.set_index("cohort_month")[chart_columns]
        )

        display_columns = [
            "cohort_month",
            "cohort_users",
            "d1_eligible_users",
            "d1_users",
            "d1_retention_pct",
            "d7_eligible_users",
            "d7_users",
            "d7_retention_pct",
            "d30_eligible_users",
            "d30_users",
            "d30_retention_pct",
        ]
        display_cohorts = cohort_df[display_columns].copy()
        display_cohorts = display_cohorts.rename(columns={
            "cohort_month": "Cohort Month",
            "cohort_users": "Cohort Users",
            "d1_eligible_users": "D1 Eligible",
            "d1_users": "D1 Retained",
            "d1_retention_pct": "D1 Retention (%)",
            "d7_eligible_users": "D7 Eligible",
            "d7_users": "D7 Retained",
            "d7_retention_pct": "D7 Retention (%)",
            "d30_eligible_users": "D30 Eligible",
            "d30_users": "D30 Retained",
            "d30_retention_pct": "D30 Retention (%)",
        })

        st.dataframe(
            display_cohorts.style.format({
                "Cohort Users": "{:,.0f}",
                "D1 Eligible": "{:,.0f}",
                "D1 Retained": "{:,.0f}",
                "D1 Retention (%)": "{:.2f}%",
                "D7 Eligible": "{:,.0f}",
                "D7 Retained": "{:,.0f}",
                "D7 Retention (%)": "{:.2f}%",
                "D30 Eligible": "{:,.0f}",
                "D30 Retained": "{:,.0f}",
                "D30 Retention (%)": "{:.2f}%",
            }, na_rep="Not mature"),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Cohorts use first observed activity, not signup date. "
            "D1/D7/D30 measure activity on the exact day. Each rate "
            "uses only users with enough observation time; 'Not mature' "
            "means no eligible users are available for that horizon."
        )


# ============================================================
# EXPERIMENTATION
# ============================================================


elif page == "Experimentation":

    st.header("🧪 A/B Test Results")

    # Count users assigned to each observed experiment group.
    experiment = (
        df.dropna(subset=["experiment_group"])
        .groupby("experiment_group")
        .agg(Users=("user_id", "nunique"))
        .reset_index()
    )

    purchasers = (
        purchase_df.dropna(subset=["experiment_group"])
        .groupby("experiment_group")["user_id"]
        .nunique()
        .reset_index(name="Purchasers")
    )

    experiment = experiment.merge(
        purchasers,
        on="experiment_group",
        how="left",
    )
    experiment["Purchasers"] = experiment["Purchasers"].fillna(0)

    experiment["Conversion (%)"] = (
        experiment["Purchasers"]
        / experiment["Users"]
        * 100
    )

    st.dataframe(
        experiment.style.format({
            "Users": "{:,.0f}",
            "Purchasers": "{:,.0f}",
            "Conversion (%)": "{:.2f}%",
        }),
        use_container_width=True,
        hide_index=True,
    )

    required_groups = {"control", "treatment"}
    observed_groups = set(experiment["experiment_group"].astype(str))

    missing_groups = required_groups - observed_groups
    unknown_groups = observed_groups - required_groups
    missing_assignments = int(df["experiment_group"].isna().sum())

    if missing_assignments:
        st.warning(
            f"{missing_assignments:,} event rows have no experiment-group "
            "assignment and are excluded from this comparison."
        )

    if unknown_groups:
        st.warning(
            "Unexpected experiment groups found: "
            + ", ".join(sorted(unknown_groups))
            + ". Review assignments before interpreting results."
        )

    if missing_groups:
        st.warning(
            "Cannot calculate the experiment comparison. Missing group(s): "
            + ", ".join(sorted(missing_groups))
        )
    else:
        control = experiment.loc[
            experiment["experiment_group"] == "control"
        ].iloc[0]

        treatment = experiment.loc[
            experiment["experiment_group"] == "treatment"
        ].iloc[0]

        control_users = int(control["Users"])
        control_purchasers = int(control["Purchasers"])
        treatment_users = int(treatment["Users"])
        treatment_purchasers = int(treatment["Purchasers"])

        if control_users == 0 or treatment_users == 0:
            st.warning(
                "Both experiment groups must contain users to calculate "
                "conversion and statistical significance."
            )
        else:
            result = two_proportion_z_test(
                control_purchasers,
                control_users,
                treatment_purchasers,
                treatment_users,
            )

            ci_lower, ci_upper = difference_confidence_interval(
                control_purchasers,
                control_users,
                treatment_purchasers,
                treatment_users,
            )

            control_rate = result["control_rate"] * 100
            treatment_rate = result["treatment_rate"] * 100
            absolute_lift = result["absolute_lift"] * 100
            relative_lift = result["relative_lift"] * 100
            p_value = result["p_value"]

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Control", f"{control_rate:.2f}%")
            col2.metric("Treatment", f"{treatment_rate:.2f}%")
            col3.metric(
                "Absolute Lift",
                f"{absolute_lift:+.2f} pp",
            )
            col4.metric(
                "Relative Lift",
                f"{relative_lift:+.2f}%"
                if pd.notna(relative_lift)
                else "N/A",
            )

            st.caption(
                f"Two-sided z-test p-value: {p_value:.6g} | "
                f"Z-score: {result['z_score']:.3f}"
            )

            st.caption(
                "95% confidence interval for absolute lift: "
                f"[{ci_lower * 100:+.2f}, {ci_upper * 100:+.2f}] "
                "percentage points."
            )

            st.bar_chart(
                experiment.set_index("experiment_group")["Conversion (%)"]
            )

            if p_value < 0.05:
                st.info(
                    "The observed conversion difference is statistically "
                    "significant at the 0.05 level. Statistical significance "
                    "does not establish practical importance or prove "
                    "causality on its own."
                )
            else:
                st.info(
                    "The observed conversion difference is not statistically "
                    "significant at the 0.05 level. This does not prove "
                    "that the groups are equivalent."
                )

            st.caption(
                "Interpretation note: this project uses synthetic data. "
                "The comparison is illustrative, not evidence of a real "
                "product effect. Causal interpretation requires valid "
                "random assignment, a suitable analysis design, and "
                "consistent outcome measurement."
            )
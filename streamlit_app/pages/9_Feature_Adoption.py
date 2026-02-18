"""
Page 9 — Feature Adoption
Per-app feature usage and platform-wide feature adoption analysis.
Which features are most used, most engaged with, and how adoption trends over time.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Feature Adoption | KLIQ", page_icon="📊", layout="wide")

import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import require_auth, logout_button
from kliq_ui_kit import (
    inject_css,
    register_plotly_template,
    section_header,
    GREEN,
    DARK,
    IVORY,
    NEUTRAL,
    TANGERINE,
    LIME,
    ALPINE,
    BG_CARD,
    SHADOW_CARD,
    CARD_RADIUS,
    CHART_SEQUENCE,
)
from data import (
    load_feature_adoption_platform,
    load_feature_adoption_per_app,
    load_feature_monthly_trend,
    load_total_coach_apps,
    load_feature_frequency,
    FEATURE_LABELS,
)

inject_css()
register_plotly_template()
require_auth()
logout_button()

# ── Header ──
st.title("Feature Adoption")
st.caption("Which features are most used per app and across the platform")
st.markdown("---")

# ── Load data ──
with st.spinner("Loading feature data from BigQuery..."):
    platform_df = load_feature_adoption_platform()
    per_app_df = load_feature_adoption_per_app()
    trend_df = load_feature_monthly_trend()
    total_coach_apps = load_total_coach_apps()
    freq_df = load_feature_frequency()


def label(event_name):
    return FEATURE_LABELS.get(event_name, event_name.replace("_", " ").title())


# ═══════════════════════════════════════════════════════════════
#  SECTION 1: PLATFORM-WIDE FEATURE ADOPTION
# ═══════════════════════════════════════════════════════════════
st.markdown(
    section_header("Platform-Wide Feature Adoption", "All apps combined"),
    unsafe_allow_html=True,
)

# ── KPI cards ──
total_events = platform_df["total_events"].sum()
total_features = len(platform_df)
total_apps = platform_df["apps_using"].max() if not platform_df.empty else 0

_card = """
<div style="
    background:{bg}; padding:20px; border-radius:{r}px;
    color:{fg}; text-align:center;
    box-shadow:{shadow};
">
    <p style="margin:0;font-size:11px;font-weight:600;letter-spacing:0.04em;text-transform:uppercase;opacity:0.7;">{label}</p>
    <h2 style="margin:6px 0;font-size:1.8rem;font-weight:700;line-height:1.1;">{value}</h2>
    <p style="margin:0;font-size:12px;opacity:0.75;">{desc}</p>
</div>
"""

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        _card.format(
            bg=GREEN,
            fg=IVORY,
            r=CARD_RADIUS,
            shadow=SHADOW_CARD,
            label="Total Events",
            value=f"{total_events:,.0f}",
            desc="All-time across platform",
        ),
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        _card.format(
            bg=DARK,
            fg=IVORY,
            r=CARD_RADIUS,
            shadow=SHADOW_CARD,
            label="Distinct Features",
            value=f"{total_features:,}",
            desc="Unique event types tracked",
        ),
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        _card.format(
            bg=TANGERINE,
            fg=IVORY,
            r=CARD_RADIUS,
            shadow=SHADOW_CARD,
            label="Apps Tracked",
            value=f"{total_apps:,}",
            desc="Apps with any events",
        ),
        unsafe_allow_html=True,
    )
with c4:
    # Most adopted feature (by app count, excluding app_opened)
    non_open = platform_df[platform_df["event_name"] != "app_opened"]
    if not non_open.empty:
        top_feat = non_open.sort_values("apps_using", ascending=False).iloc[0]
        st.markdown(
            _card.format(
                bg=ALPINE,
                fg=IVORY,
                r=CARD_RADIUS,
                shadow=SHADOW_CARD,
                label="Most Adopted Feature",
                value=label(top_feat["event_name"]),
                desc=f"Used by {top_feat['apps_using']:,.0f} apps",
            ),
            unsafe_allow_html=True,
        )

st.markdown("")

# ── Feature categories ──
FEATURE_CATEGORIES = {
    "Engagement": [
        "app_opened",
        "visits_community_page",
        "visits_blog",
        "visits_library_page",
        "visits_program_page",
        "visits_program_detail_page",
        "visits_nutrition_page",
        "visits_course_blog",
    ],
    "Content Consumption": [
        "engage_with_blog_post",
        "completes_program_workout",
        "starts_library_video",
        "completes_library_video",
        "ends_library_video",
        "engages_with_recipe",
        "starts_past_session",
        "ends_past_session",
        "completes_past_session",
        "starts_program",
        "completes_program",
    ],
    "Community": [
        "like_on_community_post",
        "replies_on_community",
        "post_on_community",
        "post_on_community_feed_with_photo",
        "post_on_community_feed_with_voice_notes",
        "saved_post",
        "commented_in_live_session",
        "post_comment_in_past_session",
    ],
    "Live Sessions": [
        "live_session_created",
        "live_session_joined",
    ],
    "Revenue": [
        "user_subscribed",
        "recurring_payment",
        "purchase_success",
        "start_purchase",
        "checkout_completion",
        "cancels_subscription",
        "purchase_cancelled",
        "promo_code_used_talent",
    ],
    "Coach Tools": [
        "create_module",
        "edit_module",
        "publish_module",
        "creates_program",
        "publishes_program",
    ],
    "Other": [
        "favourited_session_video",
        "favourites_recipe",
        "favourites_library",
        "connects_health_device",
        "completed_1_to_1_session",
        "1_to_1_session_schedule",
    ],
}

# ── Top 25 features bar chart ──
col_chart, col_table = st.columns([3, 2])

with col_chart:
    top25 = platform_df.head(25).copy()
    top25["feature"] = top25["event_name"].map(label)
    fig = px.bar(
        top25,
        x="total_events",
        y="feature",
        orientation="h",
        color="apps_using",
        color_continuous_scale=["#e8f5e9", GREEN],
        labels={
            "total_events": "Total Events",
            "feature": "",
            "apps_using": "Apps Using",
        },
        title="Top 25 Features by Total Events",
    )
    fig.update_layout(
        yaxis=dict(autorange="reversed", categoryorder="total ascending"),
        height=650,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("**Feature Adoption Table**")
    display_df = platform_df.copy()
    display_df["Feature"] = display_df["event_name"].map(label)
    display_df = display_df.rename(
        columns={
            "total_events": "Total Events",
            "apps_using": "Apps Using",
            "months_active": "Months Active",
            "first_seen": "First Seen",
            "last_seen": "Last Seen",
        }
    )
    display_df["Total Events"] = display_df["Total Events"].apply(lambda x: f"{x:,.0f}")
    display_df["Apps Using"] = display_df["Apps Using"].apply(lambda x: f"{x:,.0f}")
    st.dataframe(
        display_df[
            [
                "Feature",
                "Total Events",
                "Apps Using",
                "Months Active",
                "First Seen",
                "Last Seen",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        height=650,
    )

# ── Feature adoption by category ──
st.markdown("")
st.markdown(
    section_header("Feature Adoption by Category", "Grouped by feature type"),
    unsafe_allow_html=True,
)

cat_data = []
for cat, events in FEATURE_CATEGORIES.items():
    cat_rows = platform_df[platform_df["event_name"].isin(events)]
    if not cat_rows.empty:
        cat_data.append(
            {
                "Category": cat,
                "Features": len(cat_rows),
                "Total Events": cat_rows["total_events"].sum(),
                "Avg Apps Using": cat_rows["apps_using"].mean(),
                "Top Feature": label(cat_rows.iloc[0]["event_name"]),
                "Top Feature Events": cat_rows.iloc[0]["total_events"],
            }
        )

if cat_data:
    cat_df = pd.DataFrame(cat_data).sort_values("Total Events", ascending=False)

    col_pie, col_bar = st.columns(2)
    with col_pie:
        fig_pie = px.pie(
            cat_df,
            values="Total Events",
            names="Category",
            title="Events by Category",
            color_discrete_sequence=CHART_SEQUENCE,
            hole=0.4,
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        fig_bar = px.bar(
            cat_df,
            x="Category",
            y="Avg Apps Using",
            color="Category",
            color_discrete_sequence=CHART_SEQUENCE,
            title="Avg Apps Using Features (by Category)",
        )
        fig_bar.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.dataframe(cat_df, use_container_width=True, hide_index=True)

# ── Coach Uptake % ──
st.markdown("")
st.markdown(
    section_header(
        "Coach Uptake by Feature",
        f"% of {total_coach_apps:,} total coach apps using each feature",
    ),
    unsafe_allow_html=True,
)

if not platform_df.empty and total_coach_apps > 0:
    uptake_df = platform_df[platform_df["event_name"] != "app_opened"].copy()
    uptake_df["feature"] = uptake_df["event_name"].map(label)
    uptake_df["uptake_pct"] = (uptake_df["apps_using"] / total_coach_apps * 100).round(
        1
    )
    uptake_df = uptake_df.sort_values("uptake_pct", ascending=False)

    # Top uptake cards
    top_uptake = uptake_df.head(8)
    cols = st.columns(4)
    for i, (_, row) in enumerate(top_uptake.iterrows()):
        with cols[i % 4]:
            pct = row["uptake_pct"]
            bg = GREEN if pct >= 30 else (ALPINE if pct >= 15 else TANGERINE)
            st.markdown(
                _card.format(
                    bg=bg,
                    fg=IVORY,
                    r=CARD_RADIUS,
                    shadow=SHADOW_CARD,
                    label=row["feature"][:25],
                    value=f"{pct:.1f}%",
                    desc=f"{row['apps_using']:,.0f} of {total_coach_apps:,} apps",
                ),
                unsafe_allow_html=True,
            )
        if i == 3:
            st.markdown("")
            cols = st.columns(4)

    st.markdown("")

    col_uptake_pie, col_uptake_bar = st.columns(2)
    with col_uptake_pie:
        # Pie: top 10 features by uptake
        pie_data = uptake_df.head(10)
        fig_uptake_pie = px.pie(
            pie_data,
            values="uptake_pct",
            names="feature",
            title="Top 10 Features by Coach Uptake %",
            color_discrete_sequence=CHART_SEQUENCE,
            hole=0.4,
        )
        fig_uptake_pie.update_traces(textinfo="label+percent", textposition="outside")
        fig_uptake_pie.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig_uptake_pie, use_container_width=True)

    with col_uptake_bar:
        # Bar: all features uptake %
        bar_data = uptake_df.head(20)
        fig_uptake_bar = px.bar(
            bar_data,
            x="uptake_pct",
            y="feature",
            orientation="h",
            color="uptake_pct",
            color_continuous_scale=["#ffccbc", GREEN],
            labels={"uptake_pct": "Coach Uptake %", "feature": ""},
            title="Coach Uptake % (Top 20 Features)",
        )
        fig_uptake_bar.update_layout(
            yaxis=dict(autorange="reversed", categoryorder="total ascending"),
            height=450,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_uptake_bar, use_container_width=True)

    # Full uptake table
    uptake_table = uptake_df[
        ["feature", "apps_using", "uptake_pct", "total_events"]
    ].rename(
        columns={
            "feature": "Feature",
            "apps_using": "Apps Using",
            "uptake_pct": "Uptake %",
            "total_events": "Total Events",
        }
    )
    uptake_table["Apps Using"] = uptake_table["Apps Using"].apply(lambda x: f"{x:,.0f}")
    uptake_table["Total Events"] = uptake_table["Total Events"].apply(
        lambda x: f"{x:,.0f}"
    )
    uptake_table["Uptake %"] = uptake_table["Uptake %"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(uptake_table, use_container_width=True, hide_index=True)

# ── Avg Time Between Feature Usage ──
st.markdown("")
st.markdown(
    section_header(
        "Feature Usage Frequency",
        "Average days between usage — how often coaches/users engage with each feature",
    ),
    unsafe_allow_html=True,
)

if not freq_df.empty:
    freq_display = freq_df.copy()
    freq_display["feature"] = freq_display["event_name"].map(label)
    freq_display = freq_display[freq_display["event_name"] != "app_opened"]

    # Top frequency cards (most frequent = lowest avg days)
    top_freq = freq_display.head(8)
    freq_cols = st.columns(4)
    for i, (_, row) in enumerate(top_freq.iterrows()):
        with freq_cols[i % 4]:
            days = row["avg_days_between"]
            bg = GREEN if days <= 3 else (ALPINE if days <= 7 else TANGERINE)
            st.markdown(
                _card.format(
                    bg=bg,
                    fg=IVORY,
                    r=CARD_RADIUS,
                    shadow=SHADOW_CARD,
                    label=row["feature"][:25],
                    value=f"{days:.1f} days",
                    desc=f"{row['apps_with_repeat']:,} apps with repeat usage",
                ),
                unsafe_allow_html=True,
            )
        if i == 3:
            st.markdown("")
            freq_cols = st.columns(4)

    st.markdown("")

    col_freq_chart, col_freq_table = st.columns([3, 2])
    with col_freq_chart:
        chart_data = freq_display.head(25)
        fig_freq = px.bar(
            chart_data,
            x="avg_days_between",
            y="feature",
            orientation="h",
            color="avg_days_between",
            color_continuous_scale=[GREEN, "#ffccbc"],
            labels={"avg_days_between": "Avg Days Between", "feature": ""},
            title="Avg Days Between Feature Usage (Top 25)",
        )
        fig_freq.update_layout(
            yaxis=dict(autorange="reversed", categoryorder="total ascending"),
            height=600,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_freq, use_container_width=True)

    with col_freq_table:
        st.markdown("**Feature Frequency Table**")
        freq_table = freq_display[
            ["feature", "avg_days_between", "avg_weeks_between", "apps_with_repeat"]
        ].rename(
            columns={
                "feature": "Feature",
                "avg_days_between": "Avg Days",
                "avg_weeks_between": "Avg Weeks",
                "apps_with_repeat": "Apps w/ Repeat",
            }
        )
        freq_table["Apps w/ Repeat"] = freq_table["Apps w/ Repeat"].apply(
            lambda x: f"{x:,}"
        )
        st.dataframe(freq_table, use_container_width=True, hide_index=True, height=600)

# ── Monthly trend ──
st.markdown("")
st.markdown(
    section_header("Feature Trends Over Time", "Monthly event volume for key features"),
    unsafe_allow_html=True,
)

if not trend_df.empty:
    # Exclude app_opened (too dominant) for better visibility
    trend_filtered = trend_df[trend_df["event_name"] != "app_opened"].copy()
    trend_filtered["feature"] = trend_filtered["event_name"].map(label)

    # Let user pick features
    all_features = sorted(trend_filtered["feature"].unique())
    default_features = [
        f
        for f in [
            "Community Page Visits",
            "Blog Engagement",
            "Workout Completions",
            "Live Session Joins",
            "New Subscriptions",
            "Recurring Payments",
        ]
        if f in all_features
    ]

    selected = st.multiselect(
        "Select features to compare",
        options=all_features,
        default=default_features[:6],
    )

    if selected:
        plot_data = trend_filtered[trend_filtered["feature"].isin(selected)]
        fig_trend = px.line(
            plot_data,
            x="month",
            y="event_count",
            color="feature",
            title="Monthly Feature Usage",
            labels={"event_count": "Events", "month": "Month", "feature": "Feature"},
            color_discrete_sequence=CHART_SEQUENCE,
        )
        fig_trend.update_layout(height=450)
        st.plotly_chart(fig_trend, use_container_width=True)

        # Apps active per feature over time
        fig_apps = px.line(
            plot_data,
            x="month",
            y="apps_active",
            color="feature",
            title="Apps Actively Using Feature (Monthly)",
            labels={
                "apps_active": "Active Apps",
                "month": "Month",
                "feature": "Feature",
            },
            color_discrete_sequence=CHART_SEQUENCE,
        )
        fig_apps.update_layout(height=400)
        st.plotly_chart(fig_apps, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
#  SECTION 2: PER-APP FEATURE USAGE
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    section_header("Per-App Feature Usage", "Select an app to see its feature profile"),
    unsafe_allow_html=True,
)

if not per_app_df.empty:
    apps = sorted(per_app_df["app"].unique())
    selected_app = st.selectbox("Select App", apps, index=0)

    app_data = per_app_df[per_app_df["app"] == selected_app].copy()
    app_data["feature"] = app_data["event_name"].map(label)
    app_data = app_data.sort_values("event_count", ascending=False)

    # KPI row for selected app
    total_app_events = app_data["event_count"].sum()
    features_used = len(app_data)
    top_feature = app_data.iloc[0]["feature"] if not app_data.empty else "N/A"
    avg_months = app_data["months_used"].mean() if not app_data.empty else 0

    ac1, ac2, ac3, ac4 = st.columns(4)
    with ac1:
        st.markdown(
            _card.format(
                bg=GREEN,
                fg=IVORY,
                r=CARD_RADIUS,
                shadow=SHADOW_CARD,
                label="Total Events",
                value=f"{total_app_events:,.0f}",
                desc=selected_app,
            ),
            unsafe_allow_html=True,
        )
    with ac2:
        st.markdown(
            _card.format(
                bg=DARK,
                fg=IVORY,
                r=CARD_RADIUS,
                shadow=SHADOW_CARD,
                label="Features Used",
                value=f"{features_used:,}",
                desc="Distinct feature types",
            ),
            unsafe_allow_html=True,
        )
    with ac3:
        st.markdown(
            _card.format(
                bg=TANGERINE,
                fg=IVORY,
                r=CARD_RADIUS,
                shadow=SHADOW_CARD,
                label="Top Feature",
                value=top_feature[:20],
                desc=(
                    f"{app_data.iloc[0]['event_count']:,.0f} events"
                    if not app_data.empty
                    else ""
                ),
            ),
            unsafe_allow_html=True,
        )
    with ac4:
        st.markdown(
            _card.format(
                bg=ALPINE,
                fg=IVORY,
                r=CARD_RADIUS,
                shadow=SHADOW_CARD,
                label="Avg Feature Lifespan",
                value=f"{avg_months:.1f} mo",
                desc="Months per feature",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("")

    # Two columns: bar chart + heatmap-style table
    col_app_chart, col_app_detail = st.columns([3, 2])

    with col_app_chart:
        # Top 20 features for this app
        top20 = app_data.head(20)
        fig_app = px.bar(
            top20,
            x="event_count",
            y="feature",
            orientation="h",
            color="months_used",
            color_continuous_scale=["#fff3e0", TANGERINE],
            labels={
                "event_count": "Events",
                "feature": "",
                "months_used": "Months Used",
            },
            title=f"Top 20 Features — {selected_app}",
        )
        fig_app.update_layout(
            yaxis=dict(autorange="reversed", categoryorder="total ascending"),
            height=550,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_app, use_container_width=True)

    with col_app_detail:
        st.markdown(f"**All Features — {selected_app}**")
        detail_df = app_data[["feature", "event_count", "months_used"]].rename(
            columns={
                "feature": "Feature",
                "event_count": "Events",
                "months_used": "Months Used",
            }
        )
        detail_df["Events/Month"] = (
            (detail_df["Events"] / detail_df["Months Used"].clip(lower=1))
            .round(0)
            .astype(int)
        )
        detail_df["Events"] = detail_df["Events"].apply(lambda x: f"{x:,}")
        detail_df["Events/Month"] = detail_df["Events/Month"].apply(lambda x: f"{x:,}")
        st.dataframe(detail_df, use_container_width=True, hide_index=True, height=550)

    # ── Feature category breakdown for this app ──
    st.markdown("")
    st.markdown(f"**Feature Category Breakdown — {selected_app}**")

    app_cat_data = []
    for cat, events in FEATURE_CATEGORIES.items():
        cat_rows = app_data[app_data["event_name"].isin(events)]
        if not cat_rows.empty:
            app_cat_data.append(
                {
                    "Category": cat,
                    "Events": cat_rows["event_count"].sum(),
                    "Features Used": len(cat_rows),
                    "Top Feature": cat_rows.iloc[0]["feature"],
                }
            )

    if app_cat_data:
        app_cat_df = pd.DataFrame(app_cat_data).sort_values("Events", ascending=False)

        fig_app_cat = px.bar(
            app_cat_df,
            x="Category",
            y="Events",
            color="Category",
            color_discrete_sequence=CHART_SEQUENCE,
            title=f"Events by Category — {selected_app}",
            text="Events",
        )
        fig_app_cat.update_layout(height=350, showlegend=False)
        fig_app_cat.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        st.plotly_chart(fig_app_cat, use_container_width=True)

    # ── Compare this app to platform average ──
    st.markdown("")
    st.markdown(f"**{selected_app} vs Platform Average**")

    # Build comparison: for each feature the app uses, show app count vs platform avg
    if not platform_df.empty:
        platform_avg = (
            platform_df.set_index("event_name")["total_events"]
            / platform_df.set_index("event_name")["apps_using"]
        )
        compare_rows = []
        for _, row in app_data.head(15).iterrows():
            evt = row["event_name"]
            app_count = row["event_count"]
            plat_avg = platform_avg.get(evt, 0)
            if plat_avg > 0:
                compare_rows.append(
                    {
                        "Feature": row["feature"],
                        "App Events": app_count,
                        "Platform Avg": round(plat_avg),
                        "vs Avg": f"{(app_count / plat_avg - 1) * 100:+.0f}%",
                    }
                )

        if compare_rows:
            compare_df = pd.DataFrame(compare_rows)

            fig_compare = go.Figure()
            fig_compare.add_trace(
                go.Bar(
                    name=selected_app,
                    x=compare_df["Feature"],
                    y=compare_df["App Events"],
                    marker_color=GREEN,
                )
            )
            fig_compare.add_trace(
                go.Bar(
                    name="Platform Average",
                    x=compare_df["Feature"],
                    y=compare_df["Platform Avg"],
                    marker_color=NEUTRAL,
                )
            )
            fig_compare.update_layout(
                barmode="group",
                title=f"{selected_app} vs Platform Average (Top 15 Features)",
                height=400,
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig_compare, use_container_width=True)

            st.dataframe(compare_df, use_container_width=True, hide_index=True)

# ── Raw data expander ──
st.markdown("---")
with st.expander("Raw Data: Platform Feature Adoption"):
    st.dataframe(platform_df, use_container_width=True, hide_index=True)

with st.expander("Raw Data: Per-App Feature Usage"):
    st.dataframe(per_app_df, use_container_width=True, hide_index=True)

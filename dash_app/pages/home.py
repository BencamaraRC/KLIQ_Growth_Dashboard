"""
Home — KLIQ Command Centre
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kliq_ui import (
    GREEN,
    DARK,
    IVORY,
    TANGERINE,
    NEUTRAL,
    CARD_RADIUS,
    SHADOW_CARD,
    kpi_card,
    section_header,
)

dash.register_page(
    __name__, path="/", name="Command Centre", title="KLIQ Command Centre"
)


def _hero_card(bg, fg, label, value, desc):
    return html.Div(
        [
            html.P(
                label,
                style={
                    "margin": "0",
                    "fontSize": "12px",
                    "fontWeight": "600",
                    "letterSpacing": "0.04em",
                    "textTransform": "uppercase",
                    "opacity": "0.7",
                    "color": fg,
                },
            ),
            html.H2(
                value,
                style={
                    "margin": "8px 0",
                    "fontSize": "2rem",
                    "fontWeight": "700",
                    "lineHeight": "1.1",
                    "color": fg,
                },
            ),
            html.P(
                desc,
                style={
                    "margin": "0",
                    "fontSize": "13px",
                    "opacity": "0.75",
                    "color": fg,
                },
            ),
        ],
        style={
            "background": bg,
            "padding": "24px",
            "borderRadius": f"{CARD_RADIUS}px",
            "textAlign": "center",
            "boxShadow": SHADOW_CARD,
        },
    )


layout = html.Div(
    [
        html.H1(
            "KLIQ Command Centre",
            style={
                "fontSize": "20px",
                "fontWeight": "700",
                "color": DARK,
                "marginBottom": "4px",
            },
        ),
        html.Hr(),
        # Hero cards
        dbc.Row(
            [
                dbc.Col(
                    _hero_card(
                        GREEN,
                        IVORY,
                        "Navigate Using The Sidebar",
                        "11 Pages",
                        "Growth + Outreach",
                    ),
                    md=3,
                ),
                dbc.Col(
                    _hero_card(
                        GREEN,
                        IVORY,
                        "Live From BigQuery",
                        "54 Tables",
                        "Real-time data",
                    ),
                    md=3,
                ),
                dbc.Col(
                    _hero_card(
                        GREEN,
                        IVORY,
                        "Integrations",
                        "Meta + Apple + Play",
                        "Ads, analytics & store data",
                    ),
                    md=3,
                ),
                dbc.Col(
                    _hero_card(
                        TANGERINE,
                        DARK,
                        "Prospect Outreach",
                        "Email + SMS",
                        "Automated sequences",
                    ),
                    md=3,
                ),
            ],
            className="mb-4",
        ),
        # Data Status panel
        section_header(
            "🩺 Data Source Status", "Live health check of all data sources"
        ),
        dcc.Loading(
            html.Div(id="home-data-status"),
            type="circle",
        ),
        dcc.Interval(id="home-status-trigger", interval=1000, max_intervals=1),
        # Growth Dashboard section
        section_header("📊 Growth Dashboard", "Analytics & performance tracking"),
        html.Div(
            dbc.Table(
                [
                    html.Thead(html.Tr([html.Th("Page"), html.Th("Description")])),
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Td(html.Strong("1 — Acquisition")),
                                    html.Td(
                                        "Signups, new customers, country breakdown, website traffic, GA4 sessions, signup funnel, device breakdown"
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(html.Strong("2 — Activation")),
                                    html.Td(
                                        "Onboarding steps, content created & published, cohort retention, retention curve"
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(html.Strong("3 — Coach Snapshot")),
                                    html.Td(
                                        "Total GMV, paid to KLIQ, hosting fee, currency, months active, KLIQ fee %, GMV timeline, MAU/DAU"
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(html.Strong("4 — Coach Deep Dive")),
                                    html.Td(
                                        "Growth stages, top coaches by GMV, GMV timeline, retention curve, feature impact"
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(html.Strong("5 — App Health")),
                                    html.Td(
                                        "MAU/DAU, user overview, engagement, subscriptions, device breakdown, user location"
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(html.Strong("6 — GMV Table")),
                                    html.Td(
                                        "Per-coach monthly GMV revenue, total GMV, avg LTV per app"
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(html.Strong("7 — IAP Payouts")),
                                    html.Td(
                                        "Apple/Google sales, platform fees, KLIQ fee, coach payout per app per month"
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(html.Strong("8 — Leads & Sales")),
                                    html.Td(
                                        "Meta Ads leads, demo calls, acquisition funnel, revenue, cancellations"
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(html.Strong("9 — Growth Strategy")),
                                    html.Td(
                                        "Clusters, retention, LTV, paid ad ROI simulator, growth ladder, revenue projections"
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                bordered=True,
                hover=True,
                responsive=True,
                size="sm",
                style={"fontSize": "13px"},
            ),
            style={
                "background": "#FFFFFF",
                "borderRadius": f"{CARD_RADIUS}px",
                "boxShadow": SHADOW_CARD,
                "padding": "16px",
                "marginBottom": "24px",
            },
        ),
        # Outreach section
        section_header("📧 Prospect Outreach", "Email sequences & prospect management"),
        html.Div(
            dbc.Table(
                [
                    html.Thead(html.Tr([html.Th("Section"), html.Th("Description")])),
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Td(html.Strong("Feature Adoption")),
                                    html.Td(
                                        "Per-app feature usage, platform-wide adoption, category breakdown, monthly trends"
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(html.Strong("Outreach")),
                                    html.Td(
                                        "Email draft queue, prospect management, sent message history, phone import, cheat sheet generator"
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                bordered=True,
                hover=True,
                responsive=True,
                size="sm",
                style={"fontSize": "13px"},
            ),
            style={
                "background": "#FFFFFF",
                "borderRadius": f"{CARD_RADIUS}px",
                "boxShadow": SHADOW_CARD,
                "padding": "16px",
            },
        ),
    ]
)


@callback(
    Output("home-data-status", "children"),
    Input("home-status-trigger", "n_intervals"),
)
def update_data_status(_):
    """Check all data sources and display their status."""
    from data import query, T, _cache

    checks = []

    # ── BigQuery Tables ──
    bq_tables = {
        "d1_leads_sales": "Leads & Sales",
        "d1_meta_ads": "Meta Ads",
        "d1_tiktok_ads": "TikTok Ads",
        "d1_coach_growth_stages": "Coach Growth Stages",
        "d1_coach_gmv_timeline": "Coach GMV Timeline",
        "d1_growth_metrics": "Growth Metrics",
        "d1_activation_score": "Activation Score",
        "d1_unified_revenue": "Unified Revenue",
        "d2_app_lookup": "App Lookup",
        "d2_engagement": "App Engagement",
        "d2_subscriptions_revenue": "Subscriptions",
        "d1_coach_summary": "Coach Summary",
    }

    bq_rows = []
    for table, label in bq_tables.items():
        try:
            df = query(f"SELECT COUNT(*) AS cnt FROM {T(table)}")
            cnt = int(df.iloc[0]["cnt"]) if not df.empty else 0
            ok = cnt > 0
            bq_rows.append(
                html.Tr(
                    [
                        html.Td("✅" if ok else "⚠️", style={"width": "30px"}),
                        html.Td(label, style={"fontWeight": "600"}),
                        html.Td(
                            table,
                            style={
                                "fontFamily": "monospace",
                                "fontSize": "12px",
                                "color": NEUTRAL,
                            },
                        ),
                        html.Td(f"{cnt:,} rows"),
                        html.Td(
                            html.Span(
                                "OK", style={"color": "#15803D", "fontWeight": "600"}
                            )
                            if ok
                            else html.Span(
                                "EMPTY", style={"color": "#DC2626", "fontWeight": "600"}
                            )
                        ),
                    ]
                )
            )
        except Exception as e:
            bq_rows.append(
                html.Tr(
                    [
                        html.Td("❌"),
                        html.Td(label, style={"fontWeight": "600"}),
                        html.Td(
                            table, style={"fontFamily": "monospace", "fontSize": "12px"}
                        ),
                        html.Td("—"),
                        html.Td(
                            html.Span(
                                f"ERROR: {str(e)[:60]}",
                                style={"color": "#DC2626", "fontSize": "11px"},
                            )
                        ),
                    ]
                )
            )

    checks.append(
        html.Div(
            [
                html.H6(
                    "📊 BigQuery Tables",
                    style={"fontWeight": "700", "marginBottom": "8px"},
                ),
                dbc.Table(
                    [
                        html.Thead(
                            html.Tr(
                                [
                                    html.Th("", style={"width": "30px"}),
                                    html.Th("Source"),
                                    html.Th("Table"),
                                    html.Th("Data"),
                                    html.Th("Status"),
                                ]
                            )
                        ),
                        html.Tbody(bq_rows),
                    ],
                    bordered=True,
                    hover=True,
                    size="sm",
                    style={"fontSize": "13px"},
                ),
            ],
            style={
                "background": "#FFFFFF",
                "borderRadius": f"{CARD_RADIUS}px",
                "boxShadow": SHADOW_CARD,
                "padding": "16px",
                "marginBottom": "16px",
            },
        )
    )

    # ── Environment Variables ──
    env_keys = {
        "META_ACCESS_TOKEN": "Meta API Token",
        "META_AD_ACCOUNT_ID": "Meta Ad Account ID",
        "META_PAGE_ID": "Meta Page ID",
        "BREVO_API_KEY": "Brevo (Email) API Key",
        "TWILIO_ACCOUNT_SID": "Twilio Account SID",
        "TWILIO_AUTH_TOKEN": "Twilio Auth Token",
        "CALENDLY_API_TOKEN": "Calendly API Token",
    }
    env_rows = []
    for key, label in env_keys.items():
        val = os.getenv(key, "")
        is_set = bool(val)
        env_rows.append(
            html.Tr(
                [
                    html.Td("✅" if is_set else "❌", style={"width": "30px"}),
                    html.Td(label, style={"fontWeight": "600"}),
                    html.Td(
                        key,
                        style={
                            "fontFamily": "monospace",
                            "fontSize": "12px",
                            "color": NEUTRAL,
                        },
                    ),
                    html.Td(
                        html.Span(
                            "Set", style={"color": "#15803D", "fontWeight": "600"}
                        )
                        if is_set
                        else html.Span(
                            "Missing", style={"color": "#DC2626", "fontWeight": "600"}
                        )
                    ),
                ]
            )
        )

    checks.append(
        html.Div(
            [
                html.H6(
                    "🔑 Environment Variables",
                    style={"fontWeight": "700", "marginBottom": "8px"},
                ),
                dbc.Table(
                    [
                        html.Thead(
                            html.Tr(
                                [
                                    html.Th("", style={"width": "30px"}),
                                    html.Th("Integration"),
                                    html.Th("Variable"),
                                    html.Th("Status"),
                                ]
                            )
                        ),
                        html.Tbody(env_rows),
                    ],
                    bordered=True,
                    hover=True,
                    size="sm",
                    style={"fontSize": "13px"},
                ),
            ],
            style={
                "background": "#FFFFFF",
                "borderRadius": f"{CARD_RADIUS}px",
                "boxShadow": SHADOW_CARD,
                "padding": "16px",
                "marginBottom": "16px",
            },
        )
    )

    # ── Cache Status ──
    cache_rows = []
    for key, cache_entry in sorted(_cache.items()):
        ts, df = cache_entry[0], cache_entry[1]
        age_min = round((datetime.utcnow().timestamp() - ts) / 60, 1)
        rows = len(df) if hasattr(df, "__len__") else 0
        cache_rows.append(
            html.Tr(
                [
                    html.Td("🟢" if rows > 0 else "🔴", style={"width": "30px"}),
                    html.Td(key, style={"fontFamily": "monospace", "fontSize": "12px"}),
                    html.Td(f"{rows:,} rows"),
                    html.Td(f"{age_min} min ago"),
                ]
            )
        )

    if cache_rows:
        checks.append(
            html.Div(
                [
                    html.H6(
                        "⚡ Data Cache",
                        style={"fontWeight": "700", "marginBottom": "8px"},
                    ),
                    html.P(
                        f"Cache TTL: 10 minutes · {len(_cache)} items cached",
                        style={
                            "fontSize": "12px",
                            "color": NEUTRAL,
                            "marginBottom": "8px",
                        },
                    ),
                    dbc.Table(
                        [
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th("", style={"width": "30px"}),
                                        html.Th("Key"),
                                        html.Th("Data"),
                                        html.Th("Age"),
                                    ]
                                )
                            ),
                            html.Tbody(cache_rows),
                        ],
                        bordered=True,
                        hover=True,
                        size="sm",
                        style={"fontSize": "13px"},
                    ),
                ],
                style={
                    "background": "#FFFFFF",
                    "borderRadius": f"{CARD_RADIUS}px",
                    "boxShadow": SHADOW_CARD,
                    "padding": "16px",
                    "marginBottom": "16px",
                },
            )
        )

    # ── Credits & Balance ──
    credit_rows = []
    try:
        from health_monitor import check_credits

        credit_results = check_credits()
        for cr in credit_results:
            name = cr["name"]
            status = cr["status"]
            detail = cr["detail"]
            if status == "OK":
                icon = "✅"
                color = "#15803D"
            elif status == "WARN":
                icon = "⚠️"
                color = "#D97706"
            elif status == "FAIL":
                icon = "❌"
                color = "#DC2626"
            else:
                icon = "⏭"
                color = NEUTRAL
            credit_rows.append(
                html.Tr(
                    [
                        html.Td(icon, style={"width": "30px"}),
                        html.Td(name, style={"fontWeight": "600"}),
                        html.Td(detail, style={"fontSize": "13px"}),
                        html.Td(
                            html.Span(
                                status,
                                style={"color": color, "fontWeight": "600"},
                            )
                        ),
                    ]
                )
            )
    except Exception as e:
        credit_rows.append(
            html.Tr([html.Td("❌"), html.Td(f"Error: {str(e)[:80]}", colSpan=3)])
        )

    checks.append(
        html.Div(
            [
                html.H6(
                    "💳 Credits & Balance",
                    style={"fontWeight": "700", "marginBottom": "8px"},
                ),
                dbc.Table(
                    [
                        html.Thead(
                            html.Tr(
                                [
                                    html.Th("", style={"width": "30px"}),
                                    html.Th("Service"),
                                    html.Th("Detail"),
                                    html.Th("Status"),
                                ]
                            )
                        ),
                        html.Tbody(credit_rows),
                    ],
                    bordered=True,
                    hover=True,
                    size="sm",
                    style={"fontSize": "13px"},
                ),
            ],
            style={
                "background": "#FFFFFF",
                "borderRadius": f"{CARD_RADIUS}px",
                "boxShadow": SHADOW_CARD,
                "padding": "16px",
                "marginBottom": "16px",
            },
        )
    )

    # ── Outreach & Calendly Conversion ──
    _outreach_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "prospect-outreach",
    )
    if not os.path.isdir(_outreach_dir):
        _outreach_dir = "/app/prospect-outreach"
    if _outreach_dir not in sys.path:
        sys.path.insert(0, _outreach_dir)

    outreach_rows = []
    try:
        from tracker import get_all_prospects, get_sent_history
        from config import DRY_RUN as _dr
        import autopilot as _ap

        prospects = get_all_prospects()
        sent = get_sent_history()
        emails_sent = len([s for s in sent if s.get("channel") == "email"])
        sms_sent = len([s for s in sent if s.get("channel") == "sms"])
        run_log = _ap.get_run_log()
        last_cycle = run_log[0]["ts"] if run_log else "—"

        outreach_rows.append(
            dbc.Row(
                [
                    dbc.Col(
                        kpi_card(
                            "Prospects Synced", f"{len(prospects):,}", "In local DB"
                        ),
                        md=2,
                    ),
                    dbc.Col(
                        kpi_card("Emails Sent", f"{emails_sent:,}", "Via Brevo"), md=2
                    ),
                    dbc.Col(kpi_card("SMS Sent", f"{sms_sent:,}", "Via Twilio"), md=2),
                    dbc.Col(
                        kpi_card("Total Messages", f"{len(sent):,}", "All channels"),
                        md=2,
                    ),
                    dbc.Col(
                        kpi_card(
                            "DRY_RUN",
                            "OFF" if not _dr else "ON",
                            "Live" if not _dr else "Test mode",
                            GREEN if not _dr else TANGERINE,
                        ),
                        md=2,
                    ),
                    dbc.Col(
                        kpi_card(
                            "Last Cycle",
                            (
                                last_cycle.split(" ")[1]
                                if " " in str(last_cycle)
                                else str(last_cycle)
                            ),
                            last_cycle.split(" ")[0] if " " in str(last_cycle) else "",
                        ),
                        md=2,
                    ),
                ],
                className="mb-3",
            )
        )

        # Recent autopilot activity table
        if run_log:
            log_rows = []
            for entry in run_log[:10]:
                ok = entry.get("ok", True)
                log_rows.append(
                    html.Tr(
                        [
                            html.Td("✅" if ok else "❌", style={"width": "30px"}),
                            html.Td(
                                entry.get("action", ""),
                                style={"fontWeight": "600", "fontSize": "12px"},
                            ),
                            html.Td(
                                entry.get("detail", ""), style={"fontSize": "12px"}
                            ),
                            html.Td(
                                entry.get("ts", ""),
                                style={"fontSize": "11px", "color": NEUTRAL},
                            ),
                        ]
                    )
                )
            outreach_rows.append(
                dbc.Table(
                    [
                        html.Thead(
                            html.Tr(
                                [
                                    html.Th("", style={"width": "30px"}),
                                    html.Th("Action"),
                                    html.Th("Detail"),
                                    html.Th("Time"),
                                ]
                            )
                        ),
                        html.Tbody(log_rows),
                    ],
                    bordered=True,
                    hover=True,
                    size="sm",
                    style={"fontSize": "13px"},
                )
            )
    except Exception as e:
        outreach_rows.append(
            html.P(
                f"Outreach data unavailable: {str(e)[:100]}",
                style={"color": NEUTRAL, "fontSize": "12px"},
            )
        )

    # Calendly conversion
    calendly_rows = []
    try:
        from calendly_tracker import (
            get_booking_stats as _get_stats,
            is_configured as _cal_configured,
        )

        if _cal_configured():
            stats = _get_stats()
            total_bk = stats.get("total_bookings", 0)
            matched = stats.get("matched_total", 0)
            unmatched = stats.get("unmatched_total", 0)
            conv_rate = stats.get("outreach_conversion_rate", 0)
            unique_rcpt = stats.get("total_unique_outreach", 0)
            by_type = stats.get("by_event_type", [])

            calendly_rows.append(
                dbc.Row(
                    [
                        dbc.Col(
                            kpi_card("Total Bookings", f"{total_bk:,}", "All Calendly"),
                            md=2,
                        ),
                        dbc.Col(
                            kpi_card(
                                "From Outreach",
                                f"{matched:,}",
                                "Matched to campaigns",
                                GREEN if matched > 0 else None,
                            ),
                            md=2,
                        ),
                        dbc.Col(
                            kpi_card(
                                "Organic / Other", f"{unmatched:,}", "Not from outreach"
                            ),
                            md=2,
                        ),
                        dbc.Col(
                            kpi_card(
                                "Conversion %",
                                f"{conv_rate:.1f}%",
                                f"of {unique_rcpt:,} recipients",
                                GREEN if conv_rate > 0 else None,
                            ),
                            md=2,
                        ),
                        dbc.Col(
                            kpi_card("Event Types", f"{len(by_type)}", "Active types"),
                            md=2,
                        ),
                    ],
                    className="mb-3",
                )
            )

            # Event type breakdown
            if by_type:
                type_rows = []
                for et in by_type:
                    slug = et.get("event_type_slug", "unknown")
                    cnt = et.get("cnt", 0)
                    m = et.get("matched", 0)
                    u = et.get("unmatched", 0)
                    type_rows.append(
                        html.Tr(
                            [
                                html.Td(
                                    slug,
                                    style={"fontWeight": "600", "fontSize": "12px"},
                                ),
                                html.Td(f"{cnt:,}"),
                                html.Td(
                                    f"{m:,}",
                                    style={"color": "#15803D" if m > 0 else NEUTRAL},
                                ),
                                html.Td(f"{u:,}"),
                            ]
                        )
                    )
                calendly_rows.append(
                    dbc.Table(
                        [
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th("Event Type"),
                                        html.Th("Total"),
                                        html.Th("From Outreach"),
                                        html.Th("Organic"),
                                    ]
                                )
                            ),
                            html.Tbody(type_rows),
                        ],
                        bordered=True,
                        hover=True,
                        size="sm",
                        style={"fontSize": "13px"},
                    )
                )
        else:
            calendly_rows.append(
                html.P(
                    "Calendly API not configured — add CALENDLY_API_TOKEN to enable.",
                    style={"color": NEUTRAL, "fontSize": "12px"},
                )
            )
    except Exception as e:
        calendly_rows.append(
            html.P(
                f"Calendly data unavailable: {str(e)[:100]}",
                style={"color": NEUTRAL, "fontSize": "12px"},
            )
        )

    checks.append(
        html.Div(
            [
                html.H6(
                    "📧 Outreach Activity",
                    style={"fontWeight": "700", "marginBottom": "8px"},
                ),
                *outreach_rows,
            ],
            style={
                "background": "#FFFFFF",
                "borderRadius": f"{CARD_RADIUS}px",
                "boxShadow": SHADOW_CARD,
                "padding": "16px",
                "marginBottom": "16px",
            },
        )
    )

    checks.append(
        html.Div(
            [
                html.H6(
                    "📅 Calendly Conversion",
                    style={"fontWeight": "700", "marginBottom": "8px"},
                ),
                *calendly_rows,
            ],
            style={
                "background": "#FFFFFF",
                "borderRadius": f"{CARD_RADIUS}px",
                "boxShadow": SHADOW_CARD,
                "padding": "16px",
                "marginBottom": "16px",
            },
        )
    )

    # Overall status badge
    bq_ok = all(os.getenv(k, "") for k in ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"])
    ts_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    checks.insert(
        0,
        html.P(
            f"Last checked: {ts_str}",
            style={"fontSize": "12px", "color": NEUTRAL, "marginBottom": "12px"},
        ),
    )

    return html.Div(checks)

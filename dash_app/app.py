"""
KLIQ Command Centre · Dash App
Multi-page dashboard with Flask-Login authentication.
"""

import os
import dash
from dash import html, dcc, Input, Output, State, callback, no_update, page_container
import dash_bootstrap_components as dbc
from flask import Flask, session, redirect, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from auth import authenticate, register_user, is_admin, SECRET_KEY, _get_db
from kliq_ui import (
    GREEN,
    DARK,
    IVORY,
    NEUTRAL,
    BG_PAGE,
    BG_CARD,
    BORDER,
    SHADOW_CARD,
    CARD_RADIUS,
    TANGERINE,
    kpi_card,
)

# ── Flask Server ──
server = Flask(__name__)
server.secret_key = SECRET_KEY


# ── Health Check (must be registered before Dash takes over routing) ──
@server.route("/health")
def health_check():
    """JSON health check — validates BQ tables, env vars, and integrations."""
    import json
    from datetime import datetime

    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "ok",
        "checks": {},
    }
    any_fail = False

    # 1. Environment variables
    env_checks = {
        "META_ACCESS_TOKEN": bool(os.getenv("META_ACCESS_TOKEN", "")),
        "META_AD_ACCOUNT_ID": bool(os.getenv("META_AD_ACCOUNT_ID", "")),
        "META_PAGE_ID": bool(os.getenv("META_PAGE_ID", "")),
        "BREVO_API_KEY": bool(os.getenv("BREVO_API_KEY", "")),
        "TWILIO_ACCOUNT_SID": bool(os.getenv("TWILIO_ACCOUNT_SID", "")),
        "TWILIO_AUTH_TOKEN": bool(os.getenv("TWILIO_AUTH_TOKEN", "")),
        "CALENDLY_API_TOKEN": bool(os.getenv("CALENDLY_API_TOKEN", "")),
    }
    results["checks"]["env_vars"] = env_checks

    # 2. BigQuery connectivity + key tables
    try:
        import sys as _s

        _dash_dir = os.path.dirname(os.path.abspath(__file__))
        if _dash_dir not in _s.path:
            _s.path.insert(0, _dash_dir)
        from data import query, T

        bq_tables = {
            "d1_leads_sales": None,
            "d1_meta_ads": None,
            "d1_tiktok_ads": None,
            "d1_coach_growth_stages": None,
            "d1_coach_gmv_timeline": None,
            "d1_growth_metrics": None,
            "d1_activation_score": None,
            "d1_unified_revenue": None,
            "d2_app_lookup": None,
        }
        for table in bq_tables:
            try:
                df = query(f"SELECT 1 FROM {T(table)} LIMIT 1")
                bq_tables[table] = {
                    "ok": not df.empty,
                    "rows": "1+" if not df.empty else "0",
                }
            except Exception as e:
                bq_tables[table] = {"ok": False, "error": str(e)[:200]}
                any_fail = True
        results["checks"]["bigquery"] = bq_tables
    except Exception as e:
        results["checks"]["bigquery"] = {"error": str(e)[:200]}
        any_fail = True

    # 3. Meta API
    try:
        from fb_insights import get_account_summary

        summary = get_account_summary(days_back=7)
        results["checks"]["meta_api"] = {
            "ok": bool(summary),
            "has_data": bool(summary),
            "detail": (
                "Connected" if summary else "No data returned (token may be expired)"
            ),
        }
        if not summary:
            any_fail = True
    except Exception as e:
        results["checks"]["meta_api"] = {"ok": False, "error": str(e)[:200]}
        any_fail = True

    if any_fail:
        results["status"] = "degraded"
    return json.dumps(results, indent=2), 200, {"Content-Type": "application/json"}


# ── Flask-Login ──
login_manager = LoginManager()
login_manager.init_app(server)


class User(UserMixin):
    def __init__(self, email, full_name):
        self.id = email
        self.email = email
        self.full_name = full_name


@login_manager.user_loader
def load_user(email):
    from auth import _get_db

    conn = _get_db()
    row = conn.execute(
        "SELECT full_name, status FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    if row and row[1] == "approved":
        return User(email, row[0])
    return None


# ── Dash App ──
app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,
    pages_folder="pages",
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="KLIQ Command Centre",
    update_title=None,
)

# ── Global CSS ──
app.index_string = (
    """<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&display=swap');
        * { font-family: 'Sora', sans-serif; -webkit-font-smoothing: antialiased; }
        body { margin: 0; background: """
    + BG_PAGE
    + """; color: """
    + DARK
    + """; }
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: """
    + BORDER
    + """; border-radius: 10px; }
        .sidebar .nav-link { color: rgba(255,253,250,0.88) !important; font-size: 14px; font-weight: 500;
                     padding: 10px 16px; border-radius: 8px; transition: all 0.15s ease; }
        .nav-icon { font-size: 20px; vertical-align: middle; }
        .sidebar .nav-link:hover { color: """
    + IVORY
    + """ !important; background: rgba(255,253,250,0.08); }
        .sidebar .nav-link.active { color: """
    + IVORY
    + """ !important; background: rgba(255,253,250,0.12);
                            font-weight: 600; }
        .nav-tabs .nav-link { color: #000 !important; font-size: 13px; font-weight: 500; }
        .nav-tabs .nav-link.active { color: #000 !important; font-weight: 600; }
        .sidebar-section { font-size: 11px; font-weight: 600; letter-spacing: 0.06em;
                           text-transform: uppercase; color: rgba(255,253,250,0.5);
                           padding: 16px 16px 6px; margin-top: 8px; }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>"""
)

# ── Page registry ──
NAV_ITEMS = [
    {"label": "Command Centre", "href": "/", "icon": "📊"},
    {"section": "Growth Dashboard"},
    {"label": "Acquisition", "href": "/acquisition", "icon": "📈"},
    {"label": "Activation", "href": "/activation", "icon": "🚀"},
    {"label": "Coach Snapshot", "href": "/coach-snapshot", "icon": "👤"},
    {"label": "Coach Deep Dive", "href": "/coach-deep-dive", "icon": "🔍"},
    {"label": "App Health", "href": "/app-health", "icon": "💚"},
    {"label": "GMV Table", "href": "/gmv-table", "icon": "💰"},
    {"label": "IAP Payouts", "href": "/iap-payouts", "icon": "🧾"},
    {"label": "Leads & Sales", "href": "/leads-sales", "icon": "📣"},
    {"label": "Growth Strategy", "href": "/growth-strategy", "icon": "🎯"},
    {"section": "Platform"},
    {"label": "Feature Adoption", "href": "/feature-adoption", "icon": "⚡"},
    {"label": "Outreach", "href": "/outreach", "icon": "📧"},
]


def build_sidebar():
    nav_children = []
    for item in NAV_ITEMS:
        if "section" in item:
            nav_children.append(html.Div(item["section"], className="sidebar-section"))
        else:
            nav_children.append(
                dbc.NavLink(
                    [
                        html.Span(
                            item["icon"],
                            className="nav-icon",
                            style={"marginRight": "10px"},
                        ),
                        html.Span(item["label"], style={"verticalAlign": "middle"}),
                    ],
                    href=item["href"],
                    active="exact",
                )
            )

    return html.Div(
        [
            # Logo
            html.Div(
                html.H1(
                    "KLIQ",
                    style={
                        "color": IVORY,
                        "fontSize": "24px",
                        "fontWeight": "700",
                        "margin": "0",
                        "letterSpacing": "0.02em",
                    },
                ),
                style={"padding": "20px 16px 12px"},
            ),
            html.Hr(style={"borderColor": "rgba(255,253,250,0.1)", "margin": "0 16px"}),
            # Nav
            dbc.Nav(nav_children, vertical=True, pills=True, style={"padding": "8px"}),
            # User info at bottom (static elements, updated by callback)
            html.Div(
                [
                    html.P(
                        id="sidebar-user-name",
                        style={
                            "color": IVORY,
                            "fontWeight": "600",
                            "fontSize": "13px",
                            "margin": "0 0 2px",
                        },
                    ),
                    html.P(
                        id="sidebar-user-email",
                        style={
                            "color": "rgba(255,253,250,0.5)",
                            "fontSize": "11px",
                            "margin": "0 0 8px",
                        },
                    ),
                    dbc.Button(
                        "Sign Out",
                        id="logout-btn",
                        size="sm",
                        color="outline-light",
                        className="w-100",
                        style={"fontSize": "12px", "borderRadius": "6px"},
                    ),
                ],
                id="sidebar-user-info",
                style={
                    "position": "absolute",
                    "bottom": "16px",
                    "left": "16px",
                    "right": "16px",
                    "display": "none",
                },
            ),
        ],
        className="sidebar",
        style={
            "width": "240px",
            "minHeight": "100vh",
            "background": GREEN,
            "position": "fixed",
            "top": "0",
            "left": "0",
            "zIndex": "100",
            "overflowY": "auto",
        },
    )


def build_login_page():
    return html.Div(
        [
            html.Div(
                [
                    html.H1(
                        "KLIQ",
                        style={
                            "fontSize": "32px",
                            "fontWeight": "700",
                            "color": GREEN,
                            "textAlign": "center",
                            "marginBottom": "4px",
                        },
                    ),
                    html.P(
                        "Growth Dashboard",
                        style={
                            "textAlign": "center",
                            "color": NEUTRAL,
                            "fontSize": "14px",
                            "marginBottom": "32px",
                        },
                    ),
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4(
                                    "Sign In",
                                    style={
                                        "fontWeight": "700",
                                        "color": DARK,
                                        "marginBottom": "20px",
                                    },
                                ),
                                dbc.Label(
                                    "Email",
                                    style={"fontWeight": "600", "fontSize": "13px"},
                                ),
                                dbc.Input(
                                    id="login-email",
                                    type="email",
                                    placeholder="you@company.com",
                                    className="mb-3",
                                ),
                                dbc.Label(
                                    "Password",
                                    style={"fontWeight": "600", "fontSize": "13px"},
                                ),
                                dbc.Input(
                                    id="login-password",
                                    type="password",
                                    placeholder="Password",
                                    className="mb-3",
                                ),
                                dbc.Button(
                                    "Sign In",
                                    id="login-btn",
                                    color="dark",
                                    className="w-100 mb-3",
                                    style={
                                        "background": GREEN,
                                        "border": "none",
                                        "fontWeight": "600",
                                        "borderRadius": "8px",
                                        "padding": "10px",
                                    },
                                ),
                                html.Div(
                                    id="login-error",
                                    style={"color": "#DC2626", "fontSize": "13px"},
                                ),
                                html.Hr(),
                                html.P(
                                    "Don't have an account?",
                                    style={
                                        "fontSize": "13px",
                                        "color": NEUTRAL,
                                        "textAlign": "center",
                                    },
                                ),
                                dbc.Button(
                                    "Request Access",
                                    id="show-register-btn",
                                    color="outline-secondary",
                                    className="w-100",
                                    size="sm",
                                    style={"borderRadius": "8px", "fontWeight": "600"},
                                ),
                            ]
                        ),
                        style={
                            "maxWidth": "400px",
                            "margin": "0 auto",
                            "borderRadius": f"{CARD_RADIUS}px",
                            "boxShadow": SHADOW_CARD,
                            "border": f"1px solid {BORDER}",
                        },
                    ),
                    # Registration form (hidden by default)
                    html.Div(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H4(
                                        "Request Access",
                                        style={
                                            "fontWeight": "700",
                                            "color": DARK,
                                            "marginBottom": "20px",
                                        },
                                    ),
                                    dbc.Label(
                                        "Full Name",
                                        style={"fontWeight": "600", "fontSize": "13px"},
                                    ),
                                    dbc.Input(
                                        id="reg-name", type="text", className="mb-3"
                                    ),
                                    dbc.Label(
                                        "Email",
                                        style={"fontWeight": "600", "fontSize": "13px"},
                                    ),
                                    dbc.Input(
                                        id="reg-email", type="email", className="mb-3"
                                    ),
                                    dbc.Label(
                                        "Password",
                                        style={"fontWeight": "600", "fontSize": "13px"},
                                    ),
                                    dbc.Input(
                                        id="reg-password",
                                        type="password",
                                        className="mb-3",
                                    ),
                                    dbc.Button(
                                        "Submit",
                                        id="register-btn",
                                        color="dark",
                                        className="w-100",
                                        style={
                                            "background": GREEN,
                                            "border": "none",
                                            "fontWeight": "600",
                                            "borderRadius": "8px",
                                            "padding": "10px",
                                        },
                                    ),
                                    html.Div(
                                        id="register-msg",
                                        className="mt-2",
                                        style={"fontSize": "13px"},
                                    ),
                                ]
                            ),
                            style={
                                "maxWidth": "400px",
                                "margin": "16px auto 0",
                                "borderRadius": f"{CARD_RADIUS}px",
                                "boxShadow": SHADOW_CARD,
                                "border": f"1px solid {BORDER}",
                            },
                        ),
                        id="register-section",
                        style={"display": "none"},
                    ),
                ],
                style={"maxWidth": "480px", "margin": "80px auto", "padding": "0 16px"},
            ),
        ],
        style={"minHeight": "100vh", "background": BG_PAGE},
    )


# ── Main Layout ──
# Both login and dashboard are always in the DOM; we toggle visibility via CSS.
# This prevents page_container from being destroyed/recreated on navigation.
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="auth-store", storage_type="session"),
        # Login page (shown when not authenticated)
        html.Div(
            build_login_page(),
            id="login-container",
            style={"display": "block"},
        ),
        # Dashboard (hidden until authenticated)
        html.Div(
            [
                build_sidebar(),
                html.Div(
                    page_container,
                    style={
                        "marginLeft": "240px",
                        "padding": "24px 32px",
                        "minHeight": "100vh",
                        "background": BG_PAGE,
                    },
                ),
            ],
            id="dashboard-container",
            style={"display": "none"},
        ),
    ]
)


@callback(
    Output("login-container", "style"),
    Output("dashboard-container", "style"),
    Input("auth-store", "data"),
)
def toggle_auth_view(auth_data):
    if auth_data and auth_data.get("authenticated"):
        return {"display": "none"}, {"display": "block"}
    return {"display": "block"}, {"display": "none"}


@callback(
    Output("auth-store", "data"),
    Output("login-error", "children"),
    Input("login-btn", "n_clicks"),
    Input("logout-btn", "n_clicks"),
    State("login-email", "value"),
    State("login-password", "value"),
    prevent_initial_call=True,
)
def handle_auth(login_clicks, logout_clicks, email, password):
    triggered = dash.ctx.triggered_id
    if triggered == "logout-btn":
        return {"authenticated": False}, ""
    if triggered == "login-btn":
        if not email or not password:
            return no_update, "Please enter both email and password."
        success, status, full_name = authenticate(email, password)
        if not success:
            return no_update, "Invalid email or password."
        if status == "pending":
            return no_update, "Your account is pending admin approval."
        if status == "rejected":
            return no_update, "Your access request has been declined."
        if status == "approved":
            return {
                "authenticated": True,
                "email": email.strip().lower(),
                "name": full_name,
            }, ""
        return no_update, "Unknown error."
    return no_update, no_update


@callback(
    Output("register-section", "style"),
    Input("show-register-btn", "n_clicks"),
    prevent_initial_call=True,
)
def show_register(n):
    return {"display": "block"}


@callback(
    Output("register-msg", "children"),
    Input("register-btn", "n_clicks"),
    State("reg-name", "value"),
    State("reg-email", "value"),
    State("reg-password", "value"),
    prevent_initial_call=True,
)
def handle_register(n, name, email, password):
    if not name or not email or not password:
        return html.Span("Please fill in all fields.", style={"color": "#DC2626"})
    if len(password) < 6:
        return html.Span(
            "Password must be at least 6 characters.", style={"color": "#DC2626"}
        )
    ok, msg = register_user(email, password, name)
    color = "#15803D" if ok else "#DC2626"
    return html.Span(msg, style={"color": color})


@callback(
    Output("sidebar-user-info", "style"),
    Output("sidebar-user-name", "children"),
    Output("sidebar-user-email", "children"),
    Input("auth-store", "data"),
)
def update_sidebar_user(auth_data):
    if not auth_data or not auth_data.get("authenticated"):
        return (
            {
                "display": "none",
                "position": "absolute",
                "bottom": "16px",
                "left": "16px",
                "right": "16px",
            },
            "",
            "",
        )
    return (
        {
            "display": "block",
            "position": "absolute",
            "bottom": "16px",
            "left": "16px",
            "right": "16px",
        },
        f"\U0001f464 {auth_data.get('name', '')}",
        auth_data.get("email", ""),
    )


# ── Autopilot Background Scheduler ──
def _start_autopilot():
    """Start the outreach autopilot in a background thread."""
    import sys as _sys

    _this = os.path.dirname(os.path.abspath(__file__))
    _candidates = [
        os.path.join(os.path.dirname(_this), "prospect-outreach"),
        os.path.join(os.path.dirname(os.path.dirname(_this)), "prospect-outreach"),
        "/app/prospect-outreach",
    ]
    _outreach_dir = next((p for p in _candidates if os.path.isdir(p)), None)
    if _outreach_dir:
        if _outreach_dir not in _sys.path:
            _sys.path.insert(0, _outreach_dir)
        try:
            import autopilot

            autopilot.start()
            print(f"[APP] Autopilot scheduler started (dir={_outreach_dir})")
        except Exception as e:
            print(f"[APP] Autopilot failed to start: {e}")
    else:
        print("[APP] prospect-outreach not found — autopilot disabled")


_start_autopilot()


# ── Background BQ Table Refresh ──
def _start_bq_refresh():
    """Refresh key BQ dashboard tables on a schedule (background thread)."""
    import threading
    import time as _time

    REFRESH_INTERVAL_H = int(os.environ.get("BQ_REFRESH_HOURS", "6"))

    def _refresh_loop():
        # Wait 60s after boot before first refresh (let app start cleanly)
        _time.sleep(60)
        while True:
            try:
                import sys as _s

                _this = os.path.dirname(os.path.abspath(__file__))
                _root = os.path.dirname(_this)
                if _root not in _s.path:
                    _s.path.insert(0, _root)
                from refresh_dashboard import refresh_d1_activation_score

                print(f"[BQ REFRESH] Running refresh_d1_activation_score...")
                refresh_d1_activation_score()
                print(f"[BQ REFRESH] Done. Next refresh in {REFRESH_INTERVAL_H}h.")
            except Exception as e:
                print(f"[BQ REFRESH] Error: {e}")
            _time.sleep(REFRESH_INTERVAL_H * 3600)

    t = threading.Thread(target=_refresh_loop, daemon=True)
    t.start()
    print(f"[APP] BQ refresh scheduler started (every {REFRESH_INTERVAL_H}h)")


_start_bq_refresh()


# ── Health Monitor ──
def _start_health_monitor():
    """Start the hourly health monitor in a background thread."""
    try:
        import health_monitor

        health_monitor.start()
        print("[APP] Health monitor started")
    except Exception as e:
        print(f"[APP] Health monitor failed to start: {e}")


_start_health_monitor()


@server.route("/health-monitor/run")
def run_health_monitor():
    """Manually trigger a health check and send email."""
    import json

    try:
        import health_monitor

        results = health_monitor.run_once()
        return (
            json.dumps(
                {
                    "status": "sent",
                    "total_issues": results["total_issues"],
                    "bq_failures": len(results["bq_failures"]),
                    "api_failures": len(results["api_failures"]),
                },
                indent=2,
            ),
            200,
            {"Content-Type": "application/json"},
        )
    except Exception as e:
        return json.dumps({"error": str(e)}), 500, {"Content-Type": "application/json"}


@server.route("/send-test")
def send_test_email():
    """Manually send a welcome email to a prospect by email address.
    Usage: /send-test?email=camaralondon+1984@gmail.com&name=Ben
    """
    import json as _json

    try:
        import sys as _s

        _outreach_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "prospect-outreach"
        )
        if not os.path.isdir(_outreach_dir):
            _outreach_dir = "/app/prospect-outreach"
        if _outreach_dir not in _s.path:
            _s.path.insert(0, _outreach_dir)

        from flask import request

        to_email = request.args.get("email", "")
        name = request.args.get("name", "Coach")
        tpl = request.args.get("template", "welcome")

        if not to_email:
            return (
                _json.dumps({"error": "email param required"}),
                400,
                {"Content-Type": "application/json"},
            )

        from sequences import render_email
        from email_sender import send_email

        first_name = name.split()[0] if name else "Coach"
        ctx = {"first_name": first_name, "name": name}
        subject, html_body = render_email(tpl, ctx)
        msg_id = send_email(to_email, subject, html_body)

        return (
            _json.dumps(
                {
                    "status": "sent" if msg_id else "failed",
                    "to": to_email,
                    "template": tpl,
                    "message_id": msg_id,
                },
                indent=2,
            ),
            200,
            {"Content-Type": "application/json"},
        )

    except Exception as e:
        return _json.dumps({"error": str(e)}), 500, {"Content-Type": "application/json"}


# ── Startup Validation ──
def _startup_validation():
    """Run on boot to log which data sources are healthy."""
    print("=" * 60)
    print("[STARTUP] KLIQ Dashboard — Data Source Validation")
    print("=" * 60)

    # Env vars
    env_keys = [
        "META_ACCESS_TOKEN",
        "META_AD_ACCOUNT_ID",
        "META_PAGE_ID",
        "BREVO_API_KEY",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
    ]
    for k in env_keys:
        val = os.getenv(k, "")
        status = "✅ SET" if val else "❌ MISSING"
        print(f"  {k}: {status}")

    # BigQuery
    try:
        import sys as _s

        _dash_dir = os.path.dirname(os.path.abspath(__file__))
        if _dash_dir not in _s.path:
            _s.path.insert(0, _dash_dir)
        from data import query, T

        test_tables = [
            "d1_leads_sales",
            "d1_meta_ads",
            "d1_tiktok_ads",
            "d1_coach_growth_stages",
            "d1_unified_revenue",
            "d2_app_lookup",
        ]
        for t in test_tables:
            try:
                df = query(f"SELECT COUNT(*) AS cnt FROM {T(t)}")
                cnt = int(df.iloc[0]["cnt"]) if not df.empty else 0
                print(f"  BQ {t}: ✅ {cnt:,} rows")
            except Exception as e:
                print(f"  BQ {t}: ❌ {e}")
    except Exception as e:
        print(f"  BQ connection: ❌ {e}")

    print("=" * 60)


_startup_validation()


# ── Run ──
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.environ.get("DEBUG", "false").lower() == "true",
    )

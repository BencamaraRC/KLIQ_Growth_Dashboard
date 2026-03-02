"""
Page 12 — Prospect Outreach
Full outreach admin: FB Campaigns, Email Queue, SMS Queue, Prospects,
Sent History, Import Phones, Cheat Sheets, Sync from BigQuery.
All send functionality (individual + bulk) is fully integrated.
"""

import os
import sys
import json
import io
import csv
import base64
import dash
from dash import (
    html,
    dcc,
    callback,
    Input,
    Output,
    State,
    dash_table,
    no_update,
    ctx,
    ALL,
    MATCH,
)
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime, timezone

# Add prospect-outreach to path
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_OUTREACH_CANDIDATES = [
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(_THIS_DIR))),
        "prospect-outreach",
    ),
    os.path.join(os.path.dirname(os.path.dirname(_THIS_DIR)), "prospect-outreach"),
    "/app/prospect-outreach",
]
_OUTREACH_DIR = next(
    (p for p in _OUTREACH_CANDIDATES if os.path.isdir(p)), _OUTREACH_CANDIDATES[0]
)
if _OUTREACH_DIR not in sys.path:
    sys.path.insert(0, _OUTREACH_DIR)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kliq_ui import (
    DARK,
    NEUTRAL,
    GREEN,
    TANGERINE,
    IVORY,
    BG_CARD,
    SHADOW_CARD,
    CARD_RADIUS,
    kpi_card,
    metric_card,
    section_header,
    card_wrapper,
)

# Try to import outreach modules — graceful fallback if not available
_OUTREACH_AVAILABLE = False
_import_error = ""
try:
    from config import DRY_RUN, CHEAT_SHEET_OUTPUT_DIR
    from tracker import (
        get_all_prospects,
        get_prospect,
        upsert_prospect,
        update_prospect_deal,
        get_sent_history,
        already_sent,
        record_sent,
        upsert_fb_lead,
        get_fb_leads,
        fb_already_sent,
        record_fb_sent,
    )
    from data_pipeline import (
        fetch_new_signups,
        fetch_prospect_profile,
        fetch_all_phones,
        has_returned_after_signup,
    )
    from sequences import render_sms, render_email, SMS_TEMPLATES, EMAIL_CONFIG
    from email_sender import send_email
    from sms_sender import send_sms
    from cheat_sheet import generate_cheat_sheet
    from task_progress import get_task_progress
    import autopilot as _autopilot
    from gsheet_leads import (
        sync_sheet_leads as _sync_gsheet,
        fetch_sheet_leads as _fetch_gsheet,
    )
    from calendly_tracker import (
        sync_calendly_bookings as _sync_calendly,
        get_booking_stats as _get_booking_stats,
        get_all_bookings as _get_all_bookings,
        is_configured as _calendly_configured,
        mark_converted as _mark_converted,
        update_call_status as _update_call_status,
    )
    from dedup_guard import (
        email_already_delivered as _email_delivered,
        sms_already_delivered as _sms_delivered,
        email_was_opened as _email_was_opened,
    )
    from fb_insights import (
        get_campaign_insights as _fb_campaign_insights,
        get_demographic_insights as _fb_demo_insights,
        get_placement_insights as _fb_placement_insights,
        get_device_insights as _fb_device_insights,
        get_hourly_insights as _fb_hourly_insights,
        get_country_insights as _fb_country_insights,
        get_account_summary as _fb_account_summary,
        get_all_leads as _fb_all_leads,
        parse_lead_fields as _fb_parse_lead,
        extract_action_value as _fb_action_val,
    )

    _OUTREACH_AVAILABLE = True
except ImportError as e:
    DRY_RUN = True
    CHEAT_SHEET_OUTPUT_DIR = ""
    SMS_TEMPLATES = {}
    _import_error = str(e)

dash.register_page(__name__, path="/outreach", name="Outreach", title="Outreach — KLIQ")


# ── Smart dedup: local DB + external API fallback ──
def _smart_already_sent(app_id, step, channel, recipient=None):
    """Check local DB first; if empty, check Brevo/Twilio APIs."""
    if not _OUTREACH_AVAILABLE:
        return False
    if already_sent(app_id, step, channel):
        return True
    # Fallback: check external APIs (survives DB resets)
    try:
        if channel == "email" and recipient:
            if _email_delivered(recipient):
                record_sent(app_id, step, channel, recipient, "dedup_brevo")
                return True
        elif channel == "sms" and recipient:
            if _sms_delivered(recipient):
                record_sent(app_id, step, channel, recipient, "dedup_twilio")
                return True
    except Exception:
        pass
    return False


def _smart_fb_already_sent(email, campaign, channel, phone=None):
    """Check local DB first; if empty, check Brevo/Twilio APIs for FB leads."""
    if not _OUTREACH_AVAILABLE:
        return False
    if fb_already_sent(email, campaign, channel):
        return True
    try:
        if channel == "email" and email:
            if _email_delivered(email):
                record_fb_sent(email, campaign, channel, email, "dedup_brevo")
                return True
        elif channel == "sms" and phone:
            if _sms_delivered(phone):
                record_fb_sent(email, campaign, channel, phone, "dedup_twilio")
                return True
    except Exception:
        pass
    return False


# ── Styles ──
_CARD_STYLE = {
    "background": IVORY,
    "border": f"2px solid {DARK}",
    "borderRadius": "10px",
    "padding": "18px 22px",
    "marginBottom": "14px",
    "boxShadow": f"3px 3px 0 {DARK}",
}
_BADGE_STYLE = {
    "display": "inline-block",
    "background": "#F9FFED",
    "border": f"1.5px solid {DARK}",
    "borderRadius": "20px",
    "padding": "2px 12px",
    "fontSize": "0.82em",
    "fontWeight": "600",
    "color": DARK,
    "marginRight": "6px",
}
_SENT_BADGE = {
    "display": "inline-block",
    "background": "#d4edda",
    "border": "1px solid #155724",
    "borderRadius": "14px",
    "padding": "2px 12px",
    "fontSize": "0.8em",
    "color": "#155724",
    "fontWeight": "600",
}


def _enrich_prospect(p):
    enriched = dict(p)
    if enriched.get("profile_json"):
        try:
            full = json.loads(enriched["profile_json"])
            enriched.update(full)
        except (json.JSONDecodeError, TypeError):
            pass
    return enriched


def _pick_email_template(prospect):
    app_id = prospect["application_id"]
    email = prospect.get("email", "")
    for key in ["welcome", "cheat_sheet", "no_activity_7d"]:
        if not _smart_already_sent(app_id, key, "email", email):
            return key
    return None


_EXT_CACHE = {"data": None, "ts": None}


def _get_external_send_counts():
    """Fetch aggregate send counts from Brevo + Twilio APIs. Cached for 10 min."""
    import logging

    log = logging.getLogger("outreach.stats")

    # Return cache if fresh (10 min)
    if _EXT_CACHE["data"] and _EXT_CACHE["ts"]:
        age = (datetime.now(timezone.utc) - _EXT_CACHE["ts"]).total_seconds()
        if age < 600:
            return _EXT_CACHE["data"]

    email_count = 0
    unique_email_recipients = set()
    sms_count = 0
    unique_phones = set()

    # Brevo: count outreach emails (last 7 days) by querying delivered
    # events filtered to the outreach sender address (ben@joinkliq.io).
    try:
        from config import BREVO_API_KEY, BREVO_FROM_EMAIL

        if BREVO_API_KEY:
            import requests as _req
            from datetime import timedelta

            end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            start = (datetime.now(timezone.utc) - timedelta(days=7)).strftime(
                "%Y-%m-%d"
            )
            headers = {"accept": "application/json", "api-key": BREVO_API_KEY}
            sender = BREVO_FROM_EMAIL or "ben@joinkliq.io"
            offset = 0
            while True:
                resp = _req.get(
                    "https://api.brevo.com/v3/smtp/statistics/events",
                    headers=headers,
                    params={
                        "startDate": start,
                        "endDate": end,
                        "limit": 50,
                        "offset": offset,
                        "event": "delivered",
                    },
                    timeout=15,
                )
                if resp.status_code != 200:
                    log.warning(
                        f"Brevo events API {resp.status_code}: {resp.text[:200]}"
                    )
                    break
                events = resp.json().get("events", [])
                if not events:
                    break
                for ev in events:
                    if ev.get("from") == sender:
                        email_count += 1
                        unique_email_recipients.add(ev.get("email", ""))
                offset += 50
                if offset >= 2500:
                    break
            log.info(
                f"Brevo outreach emails (7d): {email_count}, "
                f"{len(unique_email_recipients)} unique recipients"
            )
        else:
            log.warning("BREVO_API_KEY not set")
    except Exception as e:
        log.error(f"Brevo stats error: {e}")

    # Twilio: recent SMS count
    try:
        from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN

        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            from twilio.rest import Client
            from datetime import timedelta

            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            after = datetime.now(timezone.utc) - timedelta(days=90)
            messages = client.messages.list(date_sent_after=after, limit=500)
            outbound = [
                m for m in messages if m.direction in ("outbound-api", "outbound-call")
            ]
            sms_count = len(outbound)
            unique_phones = set(m.to for m in outbound)
            log.info(f"Twilio stats: {sms_count} SMS, {len(unique_phones)} unique")
        else:
            log.warning("Twilio credentials not set")
    except Exception as e:
        log.error(f"Twilio stats error: {e}")

    result = {
        "email_count": email_count,
        "sms_count": sms_count,
        "unique_phones": len(unique_phones),
        "unique_email_recipients": len(unique_email_recipients),
    }
    _EXT_CACHE["data"] = result
    _EXT_CACHE["ts"] = datetime.now(timezone.utc)
    return result


def _not_available():
    return html.Div(
        [
            dbc.Alert(
                [
                    html.H5("Outreach Module Not Available", className="alert-heading"),
                    html.P(
                        f"The prospect-outreach module could not be loaded. "
                        f"Ensure the prospect-outreach directory exists at: {_OUTREACH_DIR}"
                    ),
                    html.P(
                        f"Import error: {_import_error}", style={"fontSize": "12px"}
                    ),
                ],
                color="warning",
            ),
        ]
    )


# ═══════════════════════════════════════════════════════════════
# LAYOUT
# ═══════════════════════════════════════════════════════════════
layout = html.Div(
    [
        html.H1(
            "📧 Prospect Outreach",
            style={"fontSize": "20px", "fontWeight": "700", "color": DARK},
        ),
        html.P(id="outreach-mode-label", style={"fontSize": "13px"}),
        html.Hr(),
        # Stats
        dbc.Row(id="outreach-stats", className="mb-3"),
        # Tab navigation
        dbc.Tabs(
            id="outreach-tabs",
            active_tab="fb_campaigns",
            children=[
                dbc.Tab(
                    label="📣 FB Campaigns",
                    tab_id="fb_campaigns",
                    label_style={"color": "#000"},
                    active_label_style={"color": "#000"},
                ),
                dbc.Tab(
                    label="📧 Email Queue",
                    tab_id="email_queue",
                    label_style={"color": "#000"},
                    active_label_style={"color": "#000"},
                ),
                dbc.Tab(
                    label="📱 SMS Queue",
                    tab_id="sms_queue",
                    label_style={"color": "#000"},
                    active_label_style={"color": "#000"},
                ),
                dbc.Tab(
                    label="👥 Prospects",
                    tab_id="prospects",
                    label_style={"color": "#000"},
                    active_label_style={"color": "#000"},
                ),
                dbc.Tab(
                    label="📨 Sent Messages",
                    tab_id="sent",
                    label_style={"color": "#000"},
                    active_label_style={"color": "#000"},
                ),
                dbc.Tab(
                    label="📥 Import Phones",
                    tab_id="import_phones",
                    label_style={"color": "#000"},
                    active_label_style={"color": "#000"},
                ),
                dbc.Tab(
                    label="📄 Cheat Sheets",
                    tab_id="cheat_sheets",
                    label_style={"color": "#000"},
                    active_label_style={"color": "#000"},
                ),
                dbc.Tab(
                    label="🔄 Sync",
                    tab_id="sync",
                    label_style={"color": "#000"},
                    active_label_style={"color": "#000"},
                ),
                dbc.Tab(
                    label="🤖 Autopilot",
                    tab_id="autopilot",
                    label_style={"color": "#000"},
                    active_label_style={"color": "#000"},
                ),
                dbc.Tab(
                    label="📊 Conversions",
                    tab_id="conversions",
                    label_style={"color": "#000"},
                    active_label_style={"color": "#000"},
                ),
                dbc.Tab(
                    label="📈 Ad Performance",
                    tab_id="ad_performance",
                    label_style={"color": "#000"},
                    active_label_style={"color": "#000"},
                ),
                dbc.Tab(
                    label="🧑 Lead Insights",
                    tab_id="lead_insights",
                    label_style={"color": "#000"},
                    active_label_style={"color": "#000"},
                ),
            ],
        ),
        html.Div(id="outreach-tab-content", className="mt-3"),
        # Hidden stores and components
        dcc.Store(id="outreach-refresh", data=0),
        dcc.Store(id="outreach-action-result", data=""),
        dcc.Download(id="outreach-download"),
        # Action components (hidden)
        html.Div(id="outreach-action-output", style={"display": "none"}),
    ]
)


# ═══════════════════════════════════════════════════════════════
# MAIN CALLBACK — Stats + Tab Content
# ═══════════════════════════════════════════════════════════════
@callback(
    Output("outreach-mode-label", "children"),
    Output("outreach-stats", "children"),
    Output("outreach-tab-content", "children"),
    Input("outreach-tabs", "active_tab"),
    Input("outreach-refresh", "data"),
)
def update_outreach(active_tab, _refresh):
    if not _OUTREACH_AVAILABLE:
        return "Module not available", [], _not_available()

    mode_label = "🟢 LIVE" if not DRY_RUN else "🟡 DRY RUN"

    # Stats — local DB + external API fallback
    try:
        all_sent = get_sent_history()
        email_sent = [h for h in all_sent if h.get("channel") == "email"]
        sms_sent = [h for h in all_sent if h.get("channel") == "sms"]
        fb_email_sent = [
            h for h in email_sent if h.get("sequence_step", "").startswith("fb_")
        ]
        fb_sms_sent = [
            h for h in sms_sent if h.get("sequence_step", "").startswith("fb_")
        ]
        prospects = get_all_prospects()
    except Exception:
        all_sent, email_sent, sms_sent, fb_email_sent, fb_sms_sent, prospects = (
            [],
            [],
            [],
            [],
            [],
            [],
        )

    # Merge local DB counts with external API counts.
    # Brevo events (7d, filtered by sender) = persistent outreach email count.
    # Twilio API = persistent SMS count. Local DB rebuilds after redeploys.
    n_email = len(email_sent)
    n_sms = len(sms_sent)
    n_total = len(all_sent)
    n_unique = len(set(h.get("recipient", "") for h in all_sent))
    try:
        ext = _get_external_send_counts()
        n_email = max(n_email, ext["email_count"])
        n_sms = max(n_sms, ext["sms_count"])
        n_total = n_email + n_sms
        n_unique = max(
            n_unique,
            ext["unique_phones"] + ext.get("unique_email_recipients", 0),
        )
    except Exception:
        pass

    stats = [
        dbc.Col(metric_card("Emails Sent", f"{n_email:,}"), md=2),
        dbc.Col(metric_card("SMS Sent", f"{n_sms:,}"), md=2),
        dbc.Col(metric_card("FB Emails", f"{len(fb_email_sent):,}"), md=2),
        dbc.Col(metric_card("FB SMS", f"{len(fb_sms_sent):,}"), md=2),
        dbc.Col(metric_card("Total Messages", f"{n_total:,}"), md=2),
        dbc.Col(metric_card("Unique Recipients", f"{n_unique:,}"), md=2),
    ]

    # Tab content
    renderers = {
        "fb_campaigns": _render_fb_campaigns,
        "email_queue": lambda: _render_email_queue(prospects),
        "sms_queue": _render_sms_queue,
        "prospects": lambda: _render_prospects(prospects),
        "sent": lambda: _render_sent_history(all_sent),
        "import_phones": _render_import_phones,
        "cheat_sheets": lambda: _render_cheat_sheets(prospects),
        "sync": _render_sync,
        "autopilot": _render_autopilot,
        "conversions": _render_conversions,
        "ad_performance": _render_ad_performance,
        "lead_insights": _render_lead_insights,
    }
    renderer = renderers.get(
        active_tab, lambda: html.P("Select a tab", style={"color": NEUTRAL})
    )
    try:
        content = renderer()
    except Exception as exc:
        import traceback

        traceback.print_exc()
        content = dbc.Alert(
            f"Error loading tab '{active_tab}': {exc}",
            color="danger",
        )

    return f"Mode: {mode_label}", stats, content


# ═══════════════════════════════════════════════════════════════
# 📣  FB CAMPAIGNS
# ═══════════════════════════════════════════════════════════════
def _render_fb_campaigns():
    try:
        re_leads = get_fb_leads(campaign="fb_reengagement")
        new_leads = get_fb_leads(campaign="fb_new_lead")
    except Exception:
        re_leads, new_leads = [], []

    # Re-engagement stats
    re_email_pending = [
        l
        for l in re_leads
        if not _smart_fb_already_sent(l["email"], "fb_reengagement", "email")
    ]
    re_sms_pending = [
        l
        for l in re_leads
        if l.get("phone")
        and not _smart_fb_already_sent(
            l["email"], "fb_reengagement", "sms", l.get("phone")
        )
    ]
    re_email_done = len(re_leads) - len(re_email_pending)
    re_sms_done = len([l for l in re_leads if l.get("phone")]) - len(re_sms_pending)

    # New leads stats — 12h rule
    now = datetime.now(timezone.utc)
    cutoff_12h = now - pd.Timedelta(hours=12)

    def _fb_new_eligible(lead):
        ld = lead.get("lead_date")
        if not ld or ld in ("None", ""):
            return True
        try:
            return pd.to_datetime(ld, utc=True) <= cutoff_12h
        except Exception:
            return True

    nl_eligible = [l for l in new_leads if _fb_new_eligible(l)]
    nl_waiting = [l for l in new_leads if not _fb_new_eligible(l)]
    nl_email_pending = [
        l
        for l in nl_eligible
        if not _smart_fb_already_sent(l["email"], "fb_new_lead", "email")
    ]
    nl_sms_pending = [
        l
        for l in nl_eligible
        if l.get("phone")
        and not _smart_fb_already_sent(l["email"], "fb_new_lead", "sms", l.get("phone"))
    ]

    # Build lead tables
    re_rows = []
    for l in re_leads:
        es = _smart_fb_already_sent(l["email"], "fb_reengagement", "email")
        ss = (
            _smart_fb_already_sent(l["email"], "fb_reengagement", "sms", l.get("phone"))
            if l.get("phone")
            else None
        )
        re_rows.append(
            {
                "Name": f"{l.get('first_name', '')} {l.get('last_name', '')}",
                "Email": l.get("email", ""),
                "Phone": l.get("phone", "—"),
                "Email": "✅" if es else "⏳",
                "SMS": ("✅" if ss else "⏳") if l.get("phone") else "—",
                "id": l.get("id", ""),
            }
        )

    nl_rows = []
    for l in nl_eligible:
        es = _smart_fb_already_sent(l["email"], "fb_new_lead", "email")
        ss = (
            _smart_fb_already_sent(l["email"], "fb_new_lead", "sms", l.get("phone"))
            if l.get("phone")
            else None
        )
        ld = l.get("lead_date", "")
        try:
            ld = pd.to_datetime(ld).strftime("%d %b %Y %H:%M")
        except Exception:
            pass
        # Compute auto-send time (lead_date + 12h)
        sends_at = "—"
        raw_ld = l.get("lead_date", "")
        if raw_ld and raw_ld not in ("None", ""):
            try:
                sends_at_dt = pd.to_datetime(raw_ld, utc=True) + pd.Timedelta(hours=12)
                if sends_at_dt <= now:
                    sends_at = "Ready now"
                else:
                    sends_at = sends_at_dt.strftime("%d %b %H:%M UTC")
            except Exception:
                pass
        nl_rows.append(
            {
                "Name": f"{l.get('first_name', '')} {l.get('last_name', '')}",
                "Email": l.get("email", ""),
                "Phone": l.get("phone", "—"),
                "Lead Date": ld,
                "Sends At": (
                    sends_at
                    if not (es and (ss if l.get("phone") else True))
                    else "✅ Done"
                ),
                "Email": "✅" if es else "⏳",
                "SMS": ("✅" if ss else "⏳") if l.get("phone") else "—",
            }
        )

    sections = [
        section_header("📣 Facebook Lead Campaigns"),
        html.P(
            "Two automated flows: Re-Engagement (old leads → KLIQ Concierge) "
            "and New Leads (fresh leads → Partner Program shortlist, 12h delay).",
            style={"color": NEUTRAL, "fontSize": "13px"},
        ),
        # CSV Import
        card_wrapper(
            [
                html.P(
                    "📥 Import Facebook Leads (CSV)",
                    style={"fontWeight": "700", "color": DARK, "marginBottom": "8px"},
                ),
                html.P(
                    "Upload a CSV with columns: first_name, last_name, email, phone (optional).",
                    style={"color": NEUTRAL, "fontSize": "12px", "marginBottom": "8px"},
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label(
                                    "Campaign",
                                    style={"fontSize": "12px", "fontWeight": "600"},
                                ),
                                dbc.RadioItems(
                                    id="fb-import-campaign",
                                    options=[
                                        {
                                            "label": "Re-Engagement",
                                            "value": "fb_reengagement",
                                        },
                                        {"label": "New Leads", "value": "fb_new_lead"},
                                    ],
                                    value="fb_reengagement",
                                    inline=True,
                                    style={"fontSize": "13px"},
                                ),
                            ],
                            md=4,
                        ),
                        dbc.Col(
                            [
                                dcc.Upload(
                                    id="fb-csv-upload",
                                    children=dbc.Button(
                                        "📁 Choose CSV File",
                                        color="secondary",
                                        size="sm",
                                        className="w-100",
                                    ),
                                    accept=".csv",
                                ),
                            ],
                            md=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Button(
                                    "Import Leads",
                                    id="fb-import-btn",
                                    color="dark",
                                    size="sm",
                                    className="w-100",
                                ),
                            ],
                            md=2,
                        ),
                        dbc.Col(
                            [
                                html.Div(id="fb-import-status"),
                            ],
                            md=3,
                        ),
                    ]
                ),
            ]
        ),
        # Google Sheet Sync
        card_wrapper(
            [
                html.P(
                    "📊 Sync from Google Sheet",
                    style={"fontWeight": "700", "color": DARK, "marginBottom": "8px"},
                ),
                html.P(
                    f"Auto-pull FB leads from the connected Google Sheet. "
                    f"The autopilot also syncs every cycle automatically.",
                    style={"color": NEUTRAL, "fontSize": "12px", "marginBottom": "8px"},
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Button(
                                    "🔄 Sync Google Sheet Now",
                                    id="fb-gsheet-sync-btn",
                                    color="success",
                                    size="sm",
                                    className="w-100",
                                ),
                            ],
                            md=3,
                        ),
                        dbc.Col(
                            [
                                html.Div(id="fb-gsheet-sync-status"),
                            ],
                            md=6,
                        ),
                    ]
                ),
            ]
        ),
        # ── Re-Engagement ──
        html.H5(
            "🔁 Re-Engagement Campaign", style={"marginTop": "16px", "color": DARK}
        ),
        html.P(
            "Old FB leads who never acted. KLIQ Concierge: dedicated VA, 15hrs/week, $500/mo.",
            style={"color": NEUTRAL, "fontSize": "12px"},
        ),
        dbc.Row(
            [
                dbc.Col(metric_card("Total Leads", f"{len(re_leads):,}"), md=2),
                dbc.Col(
                    metric_card("Email Pending", f"{len(re_email_pending):,}"), md=2
                ),
                dbc.Col(metric_card("SMS Pending", f"{len(re_sms_pending):,}"), md=2),
                dbc.Col(
                    metric_card("Sent (Email/SMS)", f"{re_email_done}/{re_sms_done}"),
                    md=2,
                ),
            ],
            className="mb-2",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        f"📧 Send All Re-Eng Emails ({len(re_email_pending)})",
                        id="fb-re-bulk-email",
                        color="success",
                        size="sm",
                        disabled=len(re_email_pending) == 0,
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Button(
                        f"📱 Send All Re-Eng SMS ({len(re_sms_pending)})",
                        id="fb-re-bulk-sms",
                        color="success",
                        size="sm",
                        disabled=len(re_sms_pending) == 0,
                    ),
                    md=3,
                ),
            ],
            className="mb-3",
        ),
    ]

    # Re-engagement lead table
    if re_leads:
        re_table_data = []
        for l in re_leads:
            es = _smart_fb_already_sent(l["email"], "fb_reengagement", "email")
            ss = (
                _smart_fb_already_sent(
                    l["email"], "fb_reengagement", "sms", l.get("phone")
                )
                if l.get("phone")
                else None
            )
            re_table_data.append(
                {
                    "Name": f"{l.get('first_name', '')} {l.get('last_name', '')}",
                    "Email": l.get("email", ""),
                    "Phone": l.get("phone") or "—",
                    "Email Status": "✅ Sent" if es else "⏳ Pending",
                    "SMS Status": (
                        ("✅ Sent" if ss else "⏳ Pending")
                        if l.get("phone")
                        else "No phone"
                    ),
                }
            )
        sections.append(
            dash_table.DataTable(
                data=re_table_data,
                columns=[{"name": c, "id": c} for c in re_table_data[0].keys()],
                style_table={"overflowX": "auto"},
                style_cell={
                    "fontSize": "12px",
                    "padding": "6px",
                    "fontFamily": "Sora",
                    "textAlign": "left",
                },
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
                style_data_conditional=[
                    {
                        "if": {
                            "filter_query": '{Email Status} = "✅ Sent"',
                            "column_id": "Email Status",
                        },
                        "color": "#155724",
                        "fontWeight": "600",
                    },
                    {
                        "if": {
                            "filter_query": '{SMS Status} = "✅ Sent"',
                            "column_id": "SMS Status",
                        },
                        "color": "#155724",
                        "fontWeight": "600",
                    },
                ],
                sort_action="native",
                page_size=20,
            )
        )
    else:
        sections.append(
            dbc.Alert(
                "No re-engagement leads imported yet. Use the CSV importer above.",
                color="info",
            )
        )

    sections.append(html.Hr())

    # ── New Leads ──
    sections.extend(
        [
            html.H5(
                "🆕 New Leads Campaign", style={"marginTop": "16px", "color": DARK}
            ),
            html.P(
                "Fresh FB leads → Partner Program shortlist email + SMS. Rule: Send 12 hours after lead comes in.",
                style={"color": NEUTRAL, "fontSize": "12px"},
            ),
            dbc.Row(
                [
                    dbc.Col(metric_card("Total Leads", f"{len(new_leads):,}"), md=2),
                    dbc.Col(
                        metric_card("Waiting (<12h)", f"{len(nl_waiting):,}"), md=2
                    ),
                    dbc.Col(
                        metric_card("Email Pending", f"{len(nl_email_pending):,}"), md=2
                    ),
                    dbc.Col(
                        metric_card("SMS Pending", f"{len(nl_sms_pending):,}"), md=2
                    ),
                ],
                className="mb-2",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Button(
                            f"📧 Send All New Lead Emails ({len(nl_email_pending)})",
                            id="fb-nl-bulk-email",
                            color="success",
                            size="sm",
                            disabled=len(nl_email_pending) == 0,
                        ),
                        md=3,
                    ),
                    dbc.Col(
                        dbc.Button(
                            f"📱 Send All New Lead SMS ({len(nl_sms_pending)})",
                            id="fb-nl-bulk-sms",
                            color="success",
                            size="sm",
                            disabled=len(nl_sms_pending) == 0,
                        ),
                        md=3,
                    ),
                ],
                className="mb-3",
            ),
        ]
    )

    if nl_eligible:
        nl_table_data = []
        for l in nl_eligible:
            es = _smart_fb_already_sent(l["email"], "fb_new_lead", "email")
            ss = (
                _smart_fb_already_sent(l["email"], "fb_new_lead", "sms", l.get("phone"))
                if l.get("phone")
                else None
            )
            ld = l.get("lead_date", "")
            try:
                ld = pd.to_datetime(ld).strftime("%d %b %Y %H:%M")
            except Exception:
                pass
            # Compute auto-send time (lead_date + 12h)
            sends_at2 = "—"
            raw_ld2 = l.get("lead_date", "")
            if raw_ld2 and raw_ld2 not in ("None", ""):
                try:
                    sa_dt = pd.to_datetime(raw_ld2, utc=True) + pd.Timedelta(hours=12)
                    if sa_dt <= now:
                        sends_at2 = "Ready now"
                    else:
                        sends_at2 = sa_dt.strftime("%d %b %H:%M UTC")
                except Exception:
                    pass
            all_done = es and (ss if l.get("phone") else True)
            nl_table_data.append(
                {
                    "Name": f"{l.get('first_name', '')} {l.get('last_name', '')}",
                    "Email": l.get("email", ""),
                    "Phone": l.get("phone") or "—",
                    "Lead Date": ld,
                    "Sends At": "✅ Done" if all_done else sends_at2,
                    "Email Status": "✅ Sent" if es else "⏳ Pending",
                    "SMS Status": (
                        ("✅ Sent" if ss else "⏳ Pending")
                        if l.get("phone")
                        else "No phone"
                    ),
                }
            )
        sections.append(
            dash_table.DataTable(
                data=nl_table_data,
                columns=[{"name": c, "id": c} for c in nl_table_data[0].keys()],
                style_table={"overflowX": "auto"},
                style_cell={
                    "fontSize": "12px",
                    "padding": "6px",
                    "fontFamily": "Sora",
                    "textAlign": "left",
                },
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
                style_data_conditional=[
                    {
                        "if": {
                            "filter_query": '{Email Status} = "✅ Sent"',
                            "column_id": "Email Status",
                        },
                        "color": "#155724",
                        "fontWeight": "600",
                    },
                    {
                        "if": {
                            "filter_query": '{SMS Status} = "✅ Sent"',
                            "column_id": "SMS Status",
                        },
                        "color": "#155724",
                        "fontWeight": "600",
                    },
                ],
                sort_action="native",
                page_size=20,
            )
        )
    else:
        sections.append(
            dbc.Alert(
                "No eligible leads (all within 12h waiting period or none imported).",
                color="info",
            )
        )

    if nl_waiting:
        wait_rows = []
        for l in nl_waiting:
            ld = l.get("lead_date", "")
            try:
                dt = pd.to_datetime(ld, utc=True)
                mins_left = int(
                    (dt + pd.Timedelta(hours=12) - now).total_seconds() / 60
                )
                time_str = f"{mins_left // 60}h {mins_left % 60}m"
            except Exception:
                time_str = "unknown"
            wait_rows.append(
                {
                    "Name": f"{l.get('first_name', '')} {l.get('last_name', '')}",
                    "Email": l.get("email", ""),
                    "Time Remaining": time_str,
                }
            )
        sections.extend(
            [
                html.H6(
                    "⏳ Waiting Leads (< 12 hours)",
                    style={"marginTop": "12px", "color": NEUTRAL},
                ),
                dash_table.DataTable(
                    data=wait_rows,
                    columns=[{"name": c, "id": c} for c in wait_rows[0].keys()],
                    style_cell={
                        "fontSize": "12px",
                        "padding": "5px",
                        "fontFamily": "Sora",
                        "textAlign": "left",
                    },
                    style_header={"fontWeight": "600", "backgroundColor": "#FFF3CD"},
                    page_size=10,
                ),
            ]
        )

    return html.Div(sections)


# ═══════════════════════════════════════════════════════════════
# 📧  EMAIL DRAFT QUEUE
# ═══════════════════════════════════════════════════════════════
def _render_email_queue(prospects):
    if not prospects:
        return dbc.Alert("No prospects yet. Sync from BigQuery first.", color="info")

    total = len(prospects)
    with_email = sum(1 for p in prospects if p.get("email"))
    all_sent_history = get_sent_history()
    total_sent_count = len(all_sent_history)

    pending = []
    for p in prospects:
        if not p.get("email"):
            continue
        tpl = _pick_email_template(p)
        if tpl is None:
            continue
        enriched = _enrich_prospect(p)
        progress = get_task_progress(enriched)
        pending.append((p, tpl, enriched, progress))

    sections = [
        section_header(f"📧 Email Draft Queue"),
        html.P(
            "Review each email draft, then click Send to deliver via Brevo.",
            style={"color": NEUTRAL, "fontSize": "13px"},
        ),
        dbc.Row(
            [
                dbc.Col(metric_card("Total Prospects", f"{total:,}"), md=2),
                dbc.Col(metric_card("With Email", f"{with_email:,}"), md=2),
                dbc.Col(metric_card("Drafts Pending", f"{len(pending):,}"), md=2),
                dbc.Col(metric_card("Emails Sent", f"{total_sent_count:,}"), md=2),
            ],
            className="mb-3",
        ),
    ]

    if not pending:
        sections.append(
            html.P(
                "🎉 All emails sent!",
                style={"color": GREEN, "fontWeight": "600", "fontSize": "14px"},
            )
        )
        return html.Div(sections)

    for idx, (p, tpl_key, enriched, progress) in enumerate(pending):
        app_id = p["application_id"]
        name = p.get("name", "Unknown")
        email = p.get("email", "—")
        niche = p.get("coach_type") or "Unknown"

        # Compute auto-send time (signup + 36h for email)
        email_sends_at = "—"
        raw_sd = p.get("signup_date", "")
        if raw_sd and raw_sd not in ("None", ""):
            try:
                sa_dt = pd.to_datetime(raw_sd, utc=True) + pd.Timedelta(hours=36)
                now_utc = datetime.now(timezone.utc)
                if sa_dt <= now_utc:
                    email_sends_at = "Ready now"
                else:
                    email_sends_at = sa_dt.strftime("%d %b %H:%M UTC")
            except Exception:
                pass

        # Action chips
        action_chips = []
        for step_label in progress.get("completed", []):
            action_chips.append(
                html.Span(
                    step_label,
                    style={
                        "display": "inline-block",
                        "background": "#DEF8FE",
                        "border": f"1px solid {DARK}",
                        "borderRadius": "14px",
                        "padding": "1px 10px",
                        "fontSize": "0.78em",
                        "color": DARK,
                        "margin": "2px 3px 2px 0",
                    },
                )
            )
        for step_label in progress.get("remaining", []):
            action_chips.append(
                html.Span(
                    step_label,
                    style={
                        "display": "inline-block",
                        "background": "#F9DAD1",
                        "border": f"1px solid {DARK}",
                        "borderRadius": "14px",
                        "padding": "1px 10px",
                        "fontSize": "0.78em",
                        "color": DARK,
                        "margin": "2px 3px 2px 0",
                    },
                )
            )

        # Email preview
        try:
            subject, html_body = render_email(tpl_key, enriched)
        except Exception as e:
            subject = f"Template error: {e}"
            html_body = ""

        tpl_label = tpl_key.replace("_", " ").title()
        attach_pdf = tpl_key == "cheat_sheet"

        card = dbc.Card(
            [
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H5(
                                            name,
                                            style={
                                                "marginBottom": "4px",
                                                "color": DARK,
                                            },
                                        ),
                                        html.Span(niche, style=_BADGE_STYLE),
                                        html.Span(
                                            email,
                                            style={
                                                "color": NEUTRAL,
                                                "fontSize": "0.85em",
                                                "marginLeft": "8px",
                                            },
                                        ),
                                        html.Span(
                                            f"⏰ Sends At: {email_sends_at}",
                                            style={
                                                "display": "inline-block",
                                                "background": (
                                                    "#FFF3CD"
                                                    if email_sends_at != "Ready now"
                                                    else "#D4EDDA"
                                                ),
                                                "border": (
                                                    "1px solid #856404"
                                                    if email_sends_at != "Ready now"
                                                    else "1px solid #155724"
                                                ),
                                                "borderRadius": "14px",
                                                "padding": "1px 10px",
                                                "fontSize": "0.78em",
                                                "color": (
                                                    "#856404"
                                                    if email_sends_at != "Ready now"
                                                    else "#155724"
                                                ),
                                                "marginLeft": "8px",
                                                "fontWeight": "600",
                                            },
                                        ),
                                        html.Div(
                                            action_chips, style={"marginTop": "8px"}
                                        ),
                                        html.P(
                                            f"{progress.get('done_count', 0)}/{progress.get('total', 0)} steps done — "
                                            f"{progress.get('progress_text', '')}",
                                            style={
                                                "marginTop": "6px",
                                                "fontSize": "0.85em",
                                                "color": DARK,
                                            },
                                        ),
                                    ],
                                    md=6,
                                ),
                                dbc.Col(
                                    [
                                        html.P(
                                            [
                                                html.Span(
                                                    "Template: ",
                                                    style={
                                                        "color": NEUTRAL,
                                                        "fontSize": "0.8em",
                                                    },
                                                ),
                                                html.Strong(
                                                    tpl_label,
                                                    style={"fontSize": "0.85em"},
                                                ),
                                            ],
                                            style={"marginBottom": "4px"},
                                        ),
                                        html.P(
                                            [
                                                html.Strong(
                                                    "Subject: ",
                                                    style={"fontSize": "0.85em"},
                                                ),
                                                html.Span(
                                                    subject,
                                                    style={"fontSize": "0.85em"},
                                                ),
                                            ]
                                        ),
                                        (
                                            html.P(
                                                "📎 Will attach cheat sheet PDF",
                                                style={
                                                    "color": TANGERINE,
                                                    "fontSize": "0.8em",
                                                    "fontWeight": "600",
                                                },
                                            )
                                            if attach_pdf
                                            else html.Div()
                                        ),
                                        dbc.Button(
                                            f"🚀 Send Email",
                                            id={
                                                "type": "send-email-btn",
                                                "index": str(app_id) + "_" + tpl_key,
                                            },
                                            color="success",
                                            size="sm",
                                            className="mt-2",
                                        ),
                                        html.Div(
                                            id={
                                                "type": "send-email-status",
                                                "index": str(app_id) + "_" + tpl_key,
                                            },
                                            style={"marginTop": "6px"},
                                        ),
                                    ],
                                    md=6,
                                ),
                            ]
                        ),
                    ]
                )
            ],
            style={
                "marginBottom": "12px",
                "border": f"2px solid {DARK}",
                "borderRadius": "10px",
                "boxShadow": f"3px 3px 0 {DARK}",
                "background": IVORY,
            },
        )

        sections.append(card)

    return html.Div(sections)


# ═══════════════════════════════════════════════════════════════
# 📱  SMS QUEUE
# ═══════════════════════════════════════════════════════════════
def _render_sms_queue():
    try:
        bq_phones = fetch_all_phones()
    except Exception:
        bq_phones = []

    now = datetime.now(timezone.utc)
    cutoff_168h = now - pd.Timedelta(hours=168)  # 7 days max
    cutoff_12h = now - pd.Timedelta(hours=12)  # 12h min delay

    def _sms_eligible(p):
        sd = p.get("created_at")
        if not sd or sd in ("None", ""):
            return False
        try:
            dt = pd.to_datetime(sd, utc=True)
            return cutoff_168h <= dt <= cutoff_12h
        except Exception:
            return False

    time_eligible = [p for p in bq_phones if _sms_eligible(p)]

    # Check return activity
    with_phone = []
    for p in time_eligible:
        try:
            if not has_returned_after_signup(p["application_id"]):
                p["phone"] = p.get("phone_number", "")
                p["name"] = p.get("application_name", "Coach")
                p["signup_date"] = str(p.get("created_at", ""))
                with_phone.append(p)
        except Exception:
            pass

    total_sms_sent = len([h for h in get_sent_history() if h.get("channel") == "sms"])
    sms_tpl_keys = list(SMS_TEMPLATES.keys()) if SMS_TEMPLATES else ["welcome"]

    sections = [
        section_header("📱 SMS Queue"),
        html.P(
            "Send SMS via KLIQ Alpha Sender ID. Rules: signed up 12h–168h ago (7 days max), not logged back in.",
            style={"color": NEUTRAL, "fontSize": "13px"},
        ),
        dbc.Row(
            [
                dbc.Col(
                    metric_card("Total w/ Phone (BQ)", f"{len(bq_phones):,}"), md=2
                ),
                dbc.Col(
                    metric_card("Eligible (12h–168h)", f"{len(time_eligible):,}"), md=2
                ),
                dbc.Col(metric_card("SMS Ready", f"{len(with_phone):,}"), md=2),
                dbc.Col(metric_card("SMS Sent", f"{total_sms_sent:,}"), md=2),
            ],
            className="mb-3",
        ),
    ]

    if not with_phone:
        sections.append(
            dbc.Alert(
                f"No eligible prospects right now. {len(bq_phones)} have phone numbers, "
                f"{len(time_eligible)} signed up 24h-14d ago, but none passed the return check.",
                color="info",
            )
        )
        return html.Div(sections)

    # Template selector + bulk send
    sections.extend(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label(
                                "SMS Template",
                                style={"fontSize": "12px", "fontWeight": "600"},
                            ),
                            dcc.Dropdown(
                                id="sms-template-select",
                                options=[
                                    {"label": k.replace("_", " ").title(), "value": k}
                                    for k in sms_tpl_keys
                                ],
                                value=sms_tpl_keys[0],
                                clearable=False,
                                style={"fontSize": "13px"},
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.Div(style={"height": "22px"}),
                            dbc.Button(
                                f"⚡ Bulk Send All SMS ({len(with_phone)})",
                                id="sms-bulk-send-btn",
                                color="danger",
                                size="sm",
                                className="w-100",
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.Div(id="sms-bulk-status"),
                        ],
                        md=4,
                    ),
                ],
                className="mb-3",
            ),
        ]
    )

    # Individual SMS cards
    sms_rows = []
    for p in with_phone[:50]:  # Limit to 50
        app_id = p.get("application_id", "")
        name = p.get("name", "Unknown")
        phone = p.get("phone", "—")
        email = p.get("email", "—")
        niche = p.get("coach_type") or "Unknown"
        signup = p.get("signup_date") or p.get("created_at") or "—"
        if signup and signup not in ("—", "None"):
            try:
                signup = pd.to_datetime(signup).strftime("%d %b %Y")
            except Exception:
                pass

        # Compute auto-send time (signup + 12h)
        sms_sends_at = "—"
        raw_created = p.get("created_at") or p.get("signup_date") or ""
        if raw_created and raw_created not in ("None", ""):
            try:
                sa_dt = pd.to_datetime(raw_created, utc=True) + pd.Timedelta(hours=12)
                if sa_dt <= now:
                    sms_sends_at = "Ready now"
                else:
                    sms_sends_at = sa_dt.strftime("%d %b %H:%M UTC")
            except Exception:
                pass

        sms_rows.append(
            {
                "App ID": app_id,
                "Name": name,
                "Phone": phone,
                "Email": email,
                "Coach Type": niche,
                "Signup": signup,
                "SMS Sends At": sms_sends_at,
            }
        )

    if sms_rows:
        sections.append(
            dash_table.DataTable(
                data=sms_rows,
                columns=[{"name": c, "id": c} for c in sms_rows[0].keys()],
                style_table={"overflowX": "auto"},
                style_cell={
                    "fontSize": "12px",
                    "padding": "6px",
                    "fontFamily": "Sora",
                    "textAlign": "left",
                },
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
                sort_action="native",
                filter_action="native",
                page_size=25,
            )
        )

    return html.Div(sections)


# ═══════════════════════════════════════════════════════════════
# 👥  PROSPECTS
# ═══════════════════════════════════════════════════════════════
_DEAL_STATUSES = ["New", "Interested", "Lost", "Won"]
_STATUS_COLORS = {
    "New": "#6B7280",
    "Interested": "#2563EB",
    "Lost": "#DC2626",
    "Won": "#15803D",
}


def _render_prospects(prospects):
    if not prospects:
        return dbc.Alert(
            "No prospects yet. Use the Sync tab to pull sign-ups from BigQuery.",
            color="info",
        )

    # Compute pipeline KPIs
    status_counts = {"New": 0, "Interested": 0, "Lost": 0, "Won": 0}
    total_won_amount = 0
    for p in prospects:
        st = p.get("deal_status") or "New"
        status_counts[st] = status_counts.get(st, 0) + 1
        if st == "Won":
            total_won_amount += float(p.get("deal_amount") or 0)

    sections = [
        section_header(f"👥 Prospect Pipeline ({len(prospects)})"),
        html.P(
            "Set each prospect's deal status and enter the amount when Won. "
            "Changes save automatically.",
            style={"color": NEUTRAL, "fontSize": "12px", "marginBottom": "8px"},
        ),
        # Pipeline KPIs
        dbc.Row(
            [
                dbc.Col(
                    metric_card("New", f"{status_counts['New']:,}"),
                    md=2,
                ),
                dbc.Col(
                    metric_card("Interested", f"{status_counts['Interested']:,}"),
                    md=2,
                ),
                dbc.Col(
                    metric_card("Won", f"{status_counts['Won']:,}"),
                    md=2,
                ),
                dbc.Col(
                    metric_card("Lost", f"{status_counts['Lost']:,}"),
                    md=2,
                ),
                dbc.Col(
                    metric_card(
                        "Total Won Revenue",
                        f"£{total_won_amount:,.0f}",
                        f"{status_counts['Won']} deals",
                    ),
                    md=4,
                ),
            ],
            className="mb-3",
        ),
        html.Div(id="prospect-deal-status"),
    ]

    # Build interactive table rows
    table_rows = []
    for p in prospects:
        app_id = p.get("application_id", 0)
        history = get_sent_history(app_id)
        msgs_sent = len(history) if history else 0
        current_status = p.get("deal_status") or "New"
        current_amount = float(p.get("deal_amount") or 0)
        status_color = _STATUS_COLORS.get(current_status, NEUTRAL)

        table_rows.append(
            html.Tr(
                [
                    html.Td(
                        str(app_id),
                        style={"fontSize": "11px", "color": NEUTRAL},
                    ),
                    html.Td(
                        p.get("name", "Unknown"),
                        style={"fontWeight": "600", "fontSize": "12px"},
                    ),
                    html.Td(
                        p.get("email", "—"),
                        style={"fontSize": "11px"},
                    ),
                    html.Td(
                        p.get("phone", "—"),
                        style={"fontSize": "11px"},
                    ),
                    html.Td(
                        p.get("coach_type", "—"),
                        style={"fontSize": "11px"},
                    ),
                    html.Td(
                        (p.get("signup_date") or "—")[:10],
                        style={"fontSize": "11px"},
                    ),
                    html.Td(
                        str(msgs_sent),
                        style={
                            "fontSize": "11px",
                            "fontWeight": "600" if msgs_sent > 0 else "normal",
                            "color": GREEN if msgs_sent > 0 else NEUTRAL,
                        },
                    ),
                    html.Td(
                        dcc.Dropdown(
                            id={"type": "deal-status-dd", "index": app_id},
                            options=[{"label": s, "value": s} for s in _DEAL_STATUSES],
                            value=current_status,
                            clearable=False,
                            style={"fontSize": "11px", "minWidth": "110px"},
                        ),
                        style={"minWidth": "120px"},
                    ),
                    html.Td(
                        dbc.Input(
                            id={"type": "deal-amount-input", "index": app_id},
                            type="number",
                            value=current_amount if current_amount > 0 else None,
                            placeholder="£0",
                            size="sm",
                            style={
                                "fontSize": "11px",
                                "width": "90px",
                                "display": (
                                    "block" if current_status == "Won" else "none"
                                ),
                            },
                            debounce=True,
                        ),
                        style={"minWidth": "100px"},
                    ),
                ],
                style={
                    "backgroundColor": (
                        "#F0FFF4"
                        if current_status == "Won"
                        else (
                            "#FEF2F2"
                            if current_status == "Lost"
                            else (
                                "#EFF6FF"
                                if current_status == "Interested"
                                else "transparent"
                            )
                        )
                    ),
                },
            )
        )

    sections.append(
        html.Div(
            dbc.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th("ID"),
                                html.Th("Name"),
                                html.Th("Email"),
                                html.Th("Phone"),
                                html.Th("Coach Type"),
                                html.Th("Signup"),
                                html.Th("Msgs"),
                                html.Th("Status"),
                                html.Th("Amount (£)"),
                            ],
                            style={"backgroundColor": "#F2F3EE"},
                        )
                    ),
                    html.Tbody(table_rows),
                ],
                bordered=True,
                hover=True,
                size="sm",
                responsive=True,
                style={"fontSize": "12px"},
            ),
            style={"maxHeight": "600px", "overflowY": "auto"},
        )
    )

    # Phone update section
    sections.extend(
        [
            html.Hr(),
            html.H6("Update Phone Number", style={"color": DARK, "fontWeight": "600"}),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("App ID", style={"fontSize": "12px"}),
                            dbc.Input(
                                id="prospect-phone-appid",
                                type="number",
                                placeholder="Application ID",
                                size="sm",
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Phone", style={"fontSize": "12px"}),
                            dbc.Input(
                                id="prospect-phone-input",
                                type="text",
                                placeholder="+44...",
                                size="sm",
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.Div(style={"height": "22px"}),
                            dbc.Button(
                                "Save Phone",
                                id="prospect-save-phone-btn",
                                color="dark",
                                size="sm",
                            ),
                        ],
                        md=2,
                    ),
                    dbc.Col(
                        [
                            html.Div(id="prospect-phone-status"),
                        ],
                        md=4,
                    ),
                ]
            ),
        ]
    )

    return html.Div(sections)


# ═══════════════════════════════════════════════════════════════
# 📨  SENT MESSAGES
# ═══════════════════════════════════════════════════════════════
def _render_sent_history(all_sent):
    if not all_sent:
        return dbc.Alert("No messages sent yet.", color="info")

    df = pd.DataFrame(all_sent)
    display_cols = ["channel", "recipient", "sequence_step", "sent_at", "message_id"]
    display_cols = [c for c in display_cols if c in df.columns]
    display_df = df[display_cols].copy()
    display_df.columns = [c.replace("_", " ").title() for c in display_cols]

    # Truncate message IDs
    if "Message Id" in display_df.columns:
        display_df["Message Id"] = display_df["Message Id"].apply(
            lambda x: (str(x)[:20] + "...") if x and len(str(x)) > 20 else x
        )

    # Check email opens via Brevo API (only for email channel)
    opened_status = []
    email_count = 0
    open_count = 0
    for row in all_sent:
        ch = row.get("channel", "")
        recip = row.get("recipient", "")
        if ch == "email" and recip:
            email_count += 1
            try:
                if _email_was_opened(recip):
                    opened_status.append("✅ Opened")
                    open_count += 1
                else:
                    opened_status.append("—")
            except Exception:
                opened_status.append("?")
        else:
            opened_status.append("n/a")

    display_df["Opened"] = opened_status
    display_df = display_df.iloc[::-1]  # Most recent first

    open_rate = f"{open_count / email_count * 100:.0f}%" if email_count > 0 else "—"

    sections = [
        section_header(f"📨 Sent Message History ({len(display_df)})"),
        dbc.Row(
            [
                dbc.Col(metric_card("Emails Sent", f"{email_count}"), md=2),
                dbc.Col(metric_card("Emails Opened", f"{open_count}"), md=2),
                dbc.Col(metric_card("Open Rate", open_rate), md=2),
                dbc.Col(
                    metric_card("SMS Sent", f"{len(all_sent) - email_count}"), md=2
                ),
            ],
            className="mb-3",
        ),
        html.P(
            "Open tracking via Brevo pixel. Some email clients block tracking pixels, so actual opens may be higher.",
            style={"color": NEUTRAL, "fontSize": "12px", "marginBottom": "12px"},
        ),
        dash_table.DataTable(
            data=display_df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in display_df.columns],
            style_table={"overflowX": "auto"},
            style_cell={
                "fontSize": "12px",
                "padding": "6px",
                "fontFamily": "Sora",
                "textAlign": "left",
            },
            style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            style_data_conditional=[
                {
                    "if": {
                        "filter_query": '{Channel} = "email"',
                        "column_id": "Channel",
                    },
                    "color": "#2E86C1",
                },
                {
                    "if": {"filter_query": '{Channel} = "sms"', "column_id": "Channel"},
                    "color": "#27AE60",
                },
                {
                    "if": {
                        "filter_query": '{Opened} contains "Opened"',
                        "column_id": "Opened",
                    },
                    "color": "#27AE60",
                    "fontWeight": "600",
                },
                {
                    "if": {
                        "filter_query": '{Opened} = "—"',
                        "column_id": "Opened",
                    },
                    "color": "#999",
                },
            ],
            sort_action="native",
            filter_action="native",
            page_size=25,
        ),
    ]

    return html.Div(sections)


# ═══════════════════════════════════════════════════════════════
# 📥  IMPORT PHONES
# ═══════════════════════════════════════════════════════════════
def _render_import_phones():
    return html.Div(
        [
            section_header("📥 Import Phone Numbers"),
            html.P(
                "Upload a CSV with columns: application_id, phone (or email, phone to match by email).",
                style={"color": NEUTRAL, "fontSize": "13px", "marginBottom": "12px"},
            ),
            card_wrapper(
                [
                    html.P(
                        "CSV Upload",
                        style={
                            "fontWeight": "700",
                            "color": DARK,
                            "marginBottom": "8px",
                        },
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dcc.Upload(
                                        id="phone-csv-upload",
                                        children=dbc.Button(
                                            "📁 Choose CSV File",
                                            color="secondary",
                                            size="sm",
                                            className="w-100",
                                        ),
                                        accept=".csv",
                                    ),
                                ],
                                md=3,
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        "Import",
                                        id="phone-import-btn",
                                        color="dark",
                                        size="sm",
                                    ),
                                ],
                                md=2,
                            ),
                            dbc.Col(
                                [
                                    html.Div(id="phone-import-status"),
                                ],
                                md=5,
                            ),
                        ]
                    ),
                ]
            ),
            html.Hr(),
            html.H6("Manual Entry", style={"color": DARK, "fontWeight": "600"}),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Application ID", style={"fontSize": "12px"}),
                            dbc.Input(
                                id="manual-phone-appid",
                                type="number",
                                placeholder="App ID",
                                size="sm",
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Phone Number", style={"fontSize": "12px"}),
                            dbc.Input(
                                id="manual-phone-input",
                                type="text",
                                placeholder="+44...",
                                size="sm",
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.Div(style={"height": "22px"}),
                            dbc.Button(
                                "Save",
                                id="manual-phone-save-btn",
                                color="dark",
                                size="sm",
                            ),
                        ],
                        md=2,
                    ),
                    dbc.Col(
                        [
                            html.Div(id="manual-phone-status"),
                        ],
                        md=4,
                    ),
                ]
            ),
        ]
    )


# ═══════════════════════════════════════════════════════════════
# 📄  CHEAT SHEETS
# ═══════════════════════════════════════════════════════════════
def _render_cheat_sheets(prospects):
    if not prospects:
        return dbc.Alert("No prospects yet. Sync from BigQuery first.", color="info")

    options = [
        {
            "label": f"{p.get('name', 'Unknown')} (ID: {p['application_id']})",
            "value": str(p["application_id"]),
        }
        for p in prospects
    ]

    # List existing PDFs
    pdf_list = []
    if CHEAT_SHEET_OUTPUT_DIR and os.path.exists(CHEAT_SHEET_OUTPUT_DIR):
        pdfs = [f for f in os.listdir(CHEAT_SHEET_OUTPUT_DIR) if f.endswith(".pdf")]
        for pdf in sorted(pdfs, reverse=True):
            path = os.path.join(CHEAT_SHEET_OUTPUT_DIR, pdf)
            size_kb = os.path.getsize(path) / 1024
            pdf_list.append(
                html.P(
                    f"📄 {pdf} ({size_kb:.1f} KB)",
                    style={"fontSize": "12px", "margin": "2px 0"},
                )
            )

    return html.Div(
        [
            section_header("📄 Cheat Sheet Generator"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label(
                                "Select Prospect",
                                style={"fontSize": "12px", "fontWeight": "600"},
                            ),
                            dcc.Dropdown(
                                id="cheatsheet-prospect-select",
                                options=options,
                                placeholder="Choose a prospect…",
                                style={"fontSize": "13px"},
                            ),
                        ],
                        md=5,
                    ),
                    dbc.Col(
                        [
                            html.Div(style={"height": "22px"}),
                            dbc.Button(
                                "Generate Cheat Sheet PDF",
                                id="cheatsheet-gen-btn",
                                color="dark",
                                size="sm",
                                className="w-100",
                            ),
                        ],
                        md=3,
                    ),
                    dbc.Col(
                        [
                            html.Div(id="cheatsheet-status"),
                        ],
                        md=4,
                    ),
                ]
            ),
            html.Hr(),
            html.H6("Generated PDFs", style={"fontWeight": "600", "color": DARK}),
            (
                html.Div(pdf_list)
                if pdf_list
                else html.P(
                    "No PDFs generated yet.",
                    style={"color": NEUTRAL, "fontSize": "12px"},
                )
            ),
        ]
    )


# ═══════════════════════════════════════════════════════════════
# 🔄  SYNC FROM BIGQUERY
# ═══════════════════════════════════════════════════════════════
def _render_sync():
    sections = [
        section_header("🔄 Sync from BigQuery"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        card_wrapper(
                            [
                                html.H6(
                                    "📥 Sync New Sign-ups",
                                    style={"fontWeight": "700", "color": DARK},
                                ),
                                html.P(
                                    "Pull recent sign-ups from BigQuery and upsert into prospect database.",
                                    style={"fontSize": "12px", "color": NEUTRAL},
                                ),
                                dbc.Label(
                                    "Look back (hours)", style={"fontSize": "12px"}
                                ),
                                dbc.Input(
                                    id="sync-hours-input",
                                    type="number",
                                    value=168,
                                    min=1,
                                    max=720,
                                    step=24,
                                    size="sm",
                                ),
                                dbc.Button(
                                    "🔄 Sync Sign-ups",
                                    id="sync-signups-btn",
                                    color="success",
                                    size="sm",
                                    className="mt-2 w-100",
                                ),
                                html.Div(
                                    id="sync-signups-status", style={"marginTop": "8px"}
                                ),
                            ]
                        ),
                    ],
                    md=6,
                ),
                dbc.Col(
                    [
                        card_wrapper(
                            [
                                html.H6(
                                    "📱 Sync Phone Numbers",
                                    style={"fontWeight": "700", "color": DARK},
                                ),
                                html.P(
                                    "Pull phone numbers from BigQuery and attach to existing prospects.",
                                    style={"fontSize": "12px", "color": NEUTRAL},
                                ),
                                dbc.Button(
                                    "📱 Sync Phones from BigQuery",
                                    id="sync-phones-btn",
                                    color="success",
                                    size="sm",
                                    className="mt-2 w-100",
                                ),
                                html.Div(
                                    id="sync-phones-status", style={"marginTop": "8px"}
                                ),
                            ]
                        ),
                    ],
                    md=6,
                ),
            ]
        ),
    ]

    # Current prospects summary
    try:
        prospects = get_all_prospects()
        if prospects:
            df = pd.DataFrame(prospects)
            display_cols = [
                c
                for c in [
                    "application_id",
                    "name",
                    "email",
                    "phone",
                    "coach_type",
                    "country",
                    "signup_date",
                ]
                if c in df.columns
            ]
            with_phone = sum(1 for p in prospects if p.get("phone"))
            sections.extend(
                [
                    html.Hr(),
                    html.P(
                        f"{len(prospects)} total prospects, {with_phone} with phone numbers",
                        style={"fontWeight": "600", "fontSize": "13px", "color": DARK},
                    ),
                    dash_table.DataTable(
                        data=df[display_cols].to_dict("records"),
                        columns=[
                            {"name": c.replace("_", " ").title(), "id": c}
                            for c in display_cols
                        ],
                        style_table={"overflowX": "auto"},
                        style_cell={
                            "fontSize": "12px",
                            "padding": "5px",
                            "fontFamily": "Sora",
                            "textAlign": "left",
                        },
                        style_header={
                            "fontWeight": "600",
                            "backgroundColor": "#F2F3EE",
                        },
                        sort_action="native",
                        filter_action="native",
                        page_size=25,
                    ),
                ]
            )
    except Exception:
        pass

    return html.Div(sections)


# ═══════════════════════════════════════════════════════════════
# 🤖  AUTOPILOT
# ═══════════════════════════════════════════════════════════════
def _render_autopilot():
    if not _OUTREACH_AVAILABLE:
        return _not_available()

    try:
        running = _autopilot.is_running()
        run_log = _autopilot.get_run_log()
    except Exception:
        running = False
        run_log = []

    status_color = GREEN if running else "#DC2626"
    status_text = "🟢 RUNNING" if running else "🔴 STOPPED"

    rules = [
        {
            "Rule": "SMS → New Sign-ups",
            "Delay": "12 hours after signup",
            "Template": "welcome",
            "Channel": "SMS",
        },
        {
            "Rule": "Email → New Sign-ups",
            "Delay": "36 hours after signup",
            "Template": "welcome",
            "Channel": "Email",
        },
        {
            "Rule": "SMS → FB Re-Engagement",
            "Delay": "12 hours after lead date",
            "Template": "fb_reengagement",
            "Channel": "SMS",
        },
        {
            "Rule": "SMS → FB New Leads",
            "Delay": "12 hours after lead date",
            "Template": "fb_new_lead",
            "Channel": "SMS",
        },
        {
            "Rule": "Email → FB Re-Engagement",
            "Delay": "12 hours after lead date",
            "Template": "fb_reengagement",
            "Channel": "Email",
        },
        {
            "Rule": "Email → FB New Leads",
            "Delay": "12 hours after lead date",
            "Template": "fb_new_lead",
            "Channel": "Email",
        },
    ]

    log_rows = []
    for entry in run_log[:50]:
        log_rows.append(
            {
                "Time": entry.get("ts", ""),
                "Action": entry.get("action", ""),
                "Detail": entry.get("detail", ""),
                "Status": "✅" if entry.get("ok", True) else "❌",
            }
        )

    poll_min = _autopilot.POLL_MINUTES if hasattr(_autopilot, "POLL_MINUTES") else 15
    dry_run = _autopilot.DRY_RUN if hasattr(_autopilot, "DRY_RUN") else DRY_RUN

    sections = [
        section_header("🤖 Autopilot Scheduler"),
        html.P(
            "Automated outreach runs in the background. Messages are sent once per prospect "
            "and tracked in the database to prevent duplicates.",
            style={"color": NEUTRAL, "fontSize": "13px"},
        ),
        # Status + controls
        dbc.Row(
            [
                dbc.Col(metric_card("Status", status_text), md=2),
                dbc.Col(metric_card("Poll Interval", f"{poll_min}m"), md=2),
                dbc.Col(metric_card("Mode", "DRY RUN" if dry_run else "LIVE"), md=2),
                dbc.Col(metric_card("Log Entries", f"{len(run_log):,}"), md=2),
            ],
            className="mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button(
                            "▶ Start Autopilot" if not running else "⏸ Stop Autopilot",
                            id="autopilot-toggle-btn",
                            color="success" if not running else "danger",
                            size="sm",
                        ),
                    ],
                    md=3,
                ),
                dbc.Col(
                    [
                        html.Div(id="autopilot-toggle-status"),
                    ],
                    md=6,
                ),
            ],
            className="mb-3",
        ),
        html.Hr(),
        # Rules table
        html.H6("📋 Automation Rules", style={"fontWeight": "600", "color": DARK}),
        dash_table.DataTable(
            data=rules,
            columns=[{"name": c, "id": c} for c in rules[0].keys()],
            style_table={"overflowX": "auto"},
            style_cell={
                "fontSize": "12px",
                "padding": "8px",
                "fontFamily": "Sora",
                "textAlign": "left",
            },
            style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            style_data_conditional=[
                {
                    "if": {"column_id": "Channel", "filter_query": '{Channel} = "SMS"'},
                    "color": "#27AE60",
                    "fontWeight": "600",
                },
                {
                    "if": {
                        "column_id": "Channel",
                        "filter_query": '{Channel} = "Email"',
                    },
                    "color": "#2E86C1",
                    "fontWeight": "600",
                },
            ],
        ),
        html.Hr(),
        # Run log
        html.H6(
            "📜 Recent Activity Log",
            style={"fontWeight": "600", "color": DARK, "marginTop": "12px"},
        ),
    ]

    if log_rows:
        sections.append(
            dash_table.DataTable(
                data=log_rows,
                columns=[{"name": c, "id": c} for c in log_rows[0].keys()],
                style_table={
                    "overflowX": "auto",
                    "maxHeight": "400px",
                    "overflowY": "auto",
                },
                style_cell={
                    "fontSize": "11px",
                    "padding": "5px",
                    "fontFamily": "Sora",
                    "textAlign": "left",
                },
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
                style_data_conditional=[
                    {
                        "if": {
                            "column_id": "Status",
                            "filter_query": '{Status} = "❌"',
                        },
                        "color": "#DC2626",
                        "fontWeight": "600",
                    },
                    {
                        "if": {
                            "column_id": "Status",
                            "filter_query": '{Status} = "✅"',
                        },
                        "color": "#155724",
                        "fontWeight": "600",
                    },
                ],
                page_size=20,
            )
        )
    else:
        sections.append(
            html.P(
                "No log entries yet. The autopilot logs each cycle and action.",
                style={"color": NEUTRAL, "fontSize": "12px"},
            )
        )

    return html.Div(sections)


# ═══════════════════════════════════════════════════════════════
# 📊  CONVERSIONS (Calendly Booking Tracking)
# ═══════════════════════════════════════════════════════════════
def _render_conversions():
    if not _OUTREACH_AVAILABLE:
        return _not_available()

    configured = False
    try:
        configured = _calendly_configured()
    except Exception:
        pass

    if not configured:
        return html.Div(
            [
                section_header("📊 Conversion Tracking — Calendly Bookings"),
                dbc.Alert(
                    [
                        html.Strong("Calendly API not configured. "),
                        html.Span(
                            "Add your Calendly Personal Access Token to env.sh as "
                            "CALENDLY_API_TOKEN to enable conversion tracking. "
                            "Generate one at: "
                        ),
                        html.A(
                            "calendly.com/integrations/api_webhooks",
                            href="https://calendly.com/integrations/api_webhooks",
                            target="_blank",
                        ),
                    ],
                    color="warning",
                ),
            ]
        )

    # Get stats
    try:
        stats = _get_booking_stats()
        bookings = _get_all_bookings()
    except Exception as e:
        return html.Div(
            [
                section_header("📊 Conversion Tracking — Calendly Bookings"),
                dbc.Alert(f"Error loading booking data: {e}", color="danger"),
            ]
        )

    total_bookings = stats.get("total_bookings", 0)
    matched_total = stats.get("matched_total", 0)
    unmatched_total = stats.get("unmatched_total", 0)
    total_unique_outreach = stats.get("total_unique_outreach", 0)
    outreach_conversion_rate = stats.get("outreach_conversion_rate", 0)
    conversions = stats.get("conversions", [])
    by_type = stats.get("by_event_type", [])
    total_sales = stats.get("total_sales", 0)
    booking_to_sale_rate = stats.get("booking_to_sale_rate", 0)
    outreach_to_sale_rate = stats.get("outreach_to_sale_rate", 0)

    sections = [
        section_header("📊 Conversion Tracking — Calendly Bookings"),
        html.P(
            "Track how many outreach recipients book a Calendly call. "
            "Invitee emails are matched against sent messages to compute conversion rates.",
            style={"color": NEUTRAL, "fontSize": "13px"},
        ),
        # KPI cards — row 1: totals
        dbc.Row(
            [
                dbc.Col(metric_card("Total Bookings", f"{total_bookings:,}"), md=2),
                dbc.Col(
                    metric_card("From Outreach", f"{matched_total:,}"),
                    md=2,
                ),
                dbc.Col(
                    metric_card("Organic / Other", f"{unmatched_total:,}"),
                    md=2,
                ),
                dbc.Col(
                    metric_card(
                        "Outreach Conversion",
                        f"{outreach_conversion_rate:.1f}%",
                        f"{matched_total} bookings / {total_unique_outreach} recipients",
                    ),
                    md=3,
                ),
                dbc.Col(
                    metric_card("Unique Recipients", f"{total_unique_outreach:,}"),
                    md=3,
                ),
            ],
            className="mb-3",
        ),
        # KPI cards — row 2: per event type breakdown
        dbc.Row(
            (
                [
                    dbc.Col(
                        metric_card(
                            t.get("event_type_slug", "unknown"),
                            f"{t.get('cnt', 0):,}",
                            f"{t.get('matched', 0)} outreach · {t.get('unmatched', 0)} organic",
                        ),
                        md=3,
                    )
                    for t in by_type
                ]
                if by_type
                else []
            ),
            className="mb-3",
        ),
        # KPI cards — row 3: sale conversion funnel
        dbc.Row(
            [
                dbc.Col(
                    kpi_card(
                        "Converted to Sale",
                        f"{total_sales:,}",
                        f"of {total_bookings:,} bookings",
                        GREEN if total_sales > 0 else None,
                    ),
                    md=3,
                ),
                dbc.Col(
                    metric_card(
                        "Booking → Sale",
                        f"{booking_to_sale_rate:.1f}%",
                        f"{total_sales} sales / {total_bookings} bookings",
                    ),
                    md=3,
                ),
                dbc.Col(
                    metric_card(
                        "Outreach → Sale",
                        f"{outreach_to_sale_rate:.1f}%",
                        f"{total_sales} sales / {total_unique_outreach} recipients",
                    ),
                    md=3,
                ),
            ],
            className="mb-3",
        ),
        # Sync button
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Button(
                            "🔄 Sync Calendly Now",
                            id="calendly-sync-btn",
                            color="success",
                            size="sm",
                        ),
                    ],
                    md=3,
                ),
                dbc.Col(
                    [
                        html.Div(id="calendly-sync-status"),
                    ],
                    md=6,
                ),
            ],
            className="mb-3",
        ),
        html.Hr(),
    ]

    # Conversion rates by campaign
    if conversions:
        sections.append(
            html.H6(
                "📈 Conversion Rates by Campaign",
                style={"fontWeight": "600", "color": DARK},
            )
        )
        conv_rows = []
        for c in sorted(conversions, key=lambda x: x["conversion_rate"], reverse=True):
            conv_rows.append(
                {
                    "Campaign": c["campaign"] or "Unknown",
                    "Unique Recipients": f"{c['unique_sent']:,}",
                    "Total Msgs Sent": f"{c['total_sent']:,}",
                    "Bookings": f"{c['booked']:,}",
                    "Conversion Rate": f"{c['conversion_rate']}%",
                }
            )
        sections.append(
            dash_table.DataTable(
                data=conv_rows,
                columns=[{"name": col, "id": col} for col in conv_rows[0].keys()],
                style_table={"overflowX": "auto"},
                style_cell={
                    "fontSize": "12px",
                    "padding": "8px",
                    "fontFamily": "Sora",
                    "textAlign": "left",
                },
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
                style_data_conditional=[
                    {
                        "if": {"column_id": "Conversion Rate"},
                        "fontWeight": "700",
                        "color": GREEN,
                    },
                    {
                        "if": {"column_id": "Bookings"},
                        "fontWeight": "600",
                        "color": "#2E86C1",
                    },
                ],
            )
        )
        sections.append(html.Hr())

    # Bookings by event type
    if by_type:
        sections.append(
            html.H6(
                "📅 Bookings by Event Type",
                style={"fontWeight": "600", "color": DARK, "marginTop": "12px"},
            )
        )
        type_rows = [
            {"Event Type": t["event_type_slug"], "Bookings": f"{t['cnt']:,}"}
            for t in by_type
        ]
        sections.append(
            dash_table.DataTable(
                data=type_rows,
                columns=[{"name": col, "id": col} for col in type_rows[0].keys()],
                style_table={"overflowX": "auto"},
                style_cell={
                    "fontSize": "12px",
                    "padding": "8px",
                    "fontFamily": "Sora",
                    "textAlign": "left",
                },
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
            )
        )
        sections.append(html.Hr())

    # Recent bookings table with conversion checkboxes
    sections.append(
        html.H6(
            "📋 Prospect → Booking → Sale Pipeline",
            style={"fontWeight": "600", "color": DARK, "marginTop": "12px"},
        )
    )
    sections.append(
        html.P(
            "Check the 'Converted' box when a booking results in a sale. "
            "This tracks the full outreach → booking → sale funnel.",
            style={"color": NEUTRAL, "fontSize": "12px", "marginBottom": "8px"},
        )
    )
    _CALL_STATUS_OPTIONS = [
        {"label": "Booked", "value": "Booked"},
        {"label": "Completed", "value": "Completed"},
        {"label": "No Show", "value": "No Show"},
        {"label": "Cancelled", "value": "Cancelled"},
        {"label": "Rescheduled", "value": "Rescheduled"},
        {"label": "Interested", "value": "Interested"},
        {"label": "Not Interested", "value": "Not Interested"},
        {"label": "Closed Won", "value": "Closed Won"},
        {"label": "Closed Lost", "value": "Closed Lost"},
    ]
    _STATUS_COLORS = {
        "Booked": "#2E86C1",
        "Completed": GREEN,
        "No Show": "#DC2626",
        "Cancelled": NEUTRAL,
        "Rescheduled": TANGERINE,
        "Interested": "#2E86C1",
        "Not Interested": NEUTRAL,
        "Closed Won": GREEN,
        "Closed Lost": "#DC2626",
    }
    sections.append(html.Div(id="conversion-update-status"))
    sections.append(html.Div(id="call-status-update-status"))
    if bookings:
        booking_table_rows = []
        for b in bookings[:100]:
            bid = b.get("id", 0)
            converted = b.get("converted_to_sale", 0)
            converted_at = b.get("converted_at") or ""
            current_status = b.get("call_status") or "Booked"
            status_color = _STATUS_COLORS.get(current_status, NEUTRAL)
            booking_table_rows.append(
                html.Tr(
                    [
                        html.Td(
                            dbc.Checkbox(
                                id={"type": "sale-checkbox", "index": bid},
                                value=bool(converted),
                            ),
                            style={"width": "40px", "textAlign": "center"},
                        ),
                        html.Td(
                            (b.get("event_start") or "")[:16].replace("T", " "),
                            style={"fontSize": "11px"},
                        ),
                        html.Td(
                            b.get("invitee_name", ""),
                            style={"fontWeight": "600", "fontSize": "12px"},
                        ),
                        html.Td(
                            b.get("invitee_email", ""),
                            style={"fontSize": "11px"},
                        ),
                        html.Td(
                            b.get("event_type_slug", ""),
                            style={"fontSize": "11px"},
                        ),
                        html.Td(
                            b.get("matched_campaign") or "—",
                            style={
                                "fontSize": "11px",
                                "color": (
                                    "#2E86C1" if b.get("matched_campaign") else NEUTRAL
                                ),
                                "fontWeight": (
                                    "600" if b.get("matched_campaign") else "normal"
                                ),
                            },
                        ),
                        html.Td(
                            b.get("matched_channel") or "—",
                            style={"fontSize": "11px"},
                        ),
                        html.Td(
                            dcc.Dropdown(
                                id={"type": "call-status-dropdown", "index": bid},
                                options=_CALL_STATUS_OPTIONS,
                                value=current_status,
                                clearable=False,
                                style={
                                    "fontSize": "11px",
                                    "minWidth": "130px",
                                    "color": status_color,
                                },
                            ),
                            style={"minWidth": "140px", "padding": "2px 4px"},
                        ),
                        html.Td(
                            html.Span(
                                "✅ Sale" if converted else "—",
                                style={
                                    "color": GREEN if converted else NEUTRAL,
                                    "fontWeight": "700" if converted else "normal",
                                    "fontSize": "11px",
                                },
                            )
                        ),
                        html.Td(
                            converted_at[:10] if converted_at else "",
                            style={"fontSize": "10px", "color": NEUTRAL},
                        ),
                    ],
                    style={
                        "backgroundColor": (
                            "#F0FFF4"
                            if current_status == "Closed Won"
                            else (
                                "#FFF5F5"
                                if current_status in ("No Show", "Closed Lost")
                                else (
                                    "#FFFFF0"
                                    if current_status == "Interested"
                                    else "transparent"
                                )
                            )
                        ),
                    },
                )
            )
        sections.append(
            html.Div(
                dbc.Table(
                    [
                        html.Thead(
                            html.Tr(
                                [
                                    html.Th("Sale", style={"width": "40px"}),
                                    html.Th("Date"),
                                    html.Th("Invitee"),
                                    html.Th("Email"),
                                    html.Th("Event Type"),
                                    html.Th("Campaign"),
                                    html.Th("Channel"),
                                    html.Th("Call Status", style={"minWidth": "140px"}),
                                    html.Th("Result"),
                                    html.Th("Converted"),
                                ],
                                style={"backgroundColor": "#F2F3EE"},
                            )
                        ),
                        html.Tbody(booking_table_rows),
                    ],
                    bordered=True,
                    hover=True,
                    size="sm",
                    responsive=True,
                    style={"fontSize": "12px"},
                ),
                style={"maxHeight": "500px", "overflowY": "auto"},
            )
        )
    else:
        sections.append(
            html.P(
                "No bookings synced yet. Click 'Sync Calendly Now' or wait for the next autopilot cycle.",
                style={"color": NEUTRAL, "fontSize": "12px"},
            )
        )

    return html.Div(sections)


# ═══════════════════════════════════════════════════════════════
# ACTION CALLBACKS
# ═══════════════════════════════════════════════════════════════


# ── Calendly Sync ──
@callback(
    Output("calendly-sync-status", "children"),
    Input("calendly-sync-btn", "n_clicks"),
    prevent_initial_call=True,
)
def sync_calendly(n_clicks):
    if not n_clicks or not _OUTREACH_AVAILABLE:
        return no_update
    try:
        if not _calendly_configured():
            return html.Span(
                "⚠️ CALENDLY_API_TOKEN not set.",
                style={"color": "#DC2626", "fontSize": "12px"},
            )
        new_count = _sync_calendly(lookback_days=30)
        return html.Span(
            f"✅ Synced — {new_count} new bookings found!",
            style={"color": GREEN, "fontSize": "12px", "fontWeight": "600"},
        )
    except Exception as e:
        return html.Span(
            f"❌ {str(e)[:80]}", style={"color": "#DC2626", "fontSize": "12px"}
        )


# ── Prospect Deal Status ──
@callback(
    Output("prospect-deal-status", "children"),
    Input({"type": "deal-status-dd", "index": ALL}, "value"),
    Input({"type": "deal-amount-input", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def update_deal_status(statuses, amounts):
    """Save deal status/amount when dropdown or amount input changes."""
    if not _OUTREACH_AVAILABLE:
        return no_update
    triggered = ctx.triggered_id
    if not triggered or not isinstance(triggered, dict):
        return no_update
    app_id = triggered.get("index")
    trigger_type = triggered.get("type")
    if not app_id:
        return no_update

    try:
        if trigger_type == "deal-status-dd":
            # Find the new status value
            new_status = None
            for t in ctx.triggered:
                if t.get("value") is not None:
                    new_status = t["value"]
                    break
            if not new_status:
                return no_update
            # Get current amount (keep it if status changed)
            p = get_prospect(app_id)
            current_amount = float(p.get("deal_amount") or 0) if p else 0
            # Reset amount if not Won
            if new_status != "Won":
                current_amount = 0
            update_prospect_deal(app_id, new_status, current_amount)
            color = _STATUS_COLORS.get(new_status, NEUTRAL)
            return html.Span(
                f"✅ Prospect {app_id} → {new_status}",
                style={"color": color, "fontSize": "12px", "fontWeight": "600"},
            )
        elif trigger_type == "deal-amount-input":
            new_amount = None
            for t in ctx.triggered:
                if t.get("value") is not None:
                    new_amount = t["value"]
                    break
            p = get_prospect(app_id)
            current_status = p.get("deal_status", "New") if p else "New"
            update_prospect_deal(app_id, current_status, float(new_amount or 0))
            return html.Span(
                f"✅ Prospect {app_id} amount → £{float(new_amount or 0):,.0f}",
                style={"color": GREEN, "fontSize": "12px", "fontWeight": "600"},
            )
    except Exception as e:
        return html.Span(
            f"❌ Error: {str(e)[:80]}",
            style={"color": "#DC2626", "fontSize": "12px"},
        )
    return no_update


# ── Sale Conversion Checkbox ──
@callback(
    Output("conversion-update-status", "children"),
    Input({"type": "sale-checkbox", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def toggle_sale_conversion(values):
    """Mark/unmark a booking as converted to sale when checkbox is toggled."""
    if not _OUTREACH_AVAILABLE:
        return no_update
    triggered = ctx.triggered_id
    if not triggered or not isinstance(triggered, dict):
        return no_update
    booking_id = triggered.get("index")
    if not booking_id:
        return no_update
    # Find the value for the triggered checkbox
    # ctx.triggered gives us which input changed
    new_value = None
    for t in ctx.triggered:
        if t.get("value") is not None:
            new_value = t["value"]
            break
    if new_value is None:
        return no_update
    try:
        _mark_converted(booking_id, converted=bool(new_value))
        if new_value:
            return html.Span(
                f"✅ Booking #{booking_id} marked as converted to sale!",
                style={"color": GREEN, "fontSize": "12px", "fontWeight": "600"},
            )
        else:
            return html.Span(
                f"↩️ Booking #{booking_id} unmarked — not a sale.",
                style={"color": NEUTRAL, "fontSize": "12px"},
            )
    except Exception as e:
        return html.Span(
            f"❌ Error: {str(e)[:80]}",
            style={"color": "#DC2626", "fontSize": "12px"},
        )


# ── Call Status Dropdown ──
@callback(
    Output("call-status-update-status", "children"),
    Input({"type": "call-status-dropdown", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def update_call_status_cb(values):
    """Update call status when dropdown is changed."""
    if not _OUTREACH_AVAILABLE:
        return no_update
    triggered = ctx.triggered_id
    if not triggered or not isinstance(triggered, dict):
        return no_update
    booking_id = triggered.get("index")
    if not booking_id:
        return no_update
    new_status = None
    for t in ctx.triggered:
        if t.get("value") is not None:
            new_status = t["value"]
            break
    if not new_status:
        return no_update
    try:
        _update_call_status(booking_id, new_status)
        _DISPLAY_COLORS = {
            "Booked": "#2E86C1",
            "Completed": GREEN,
            "No Show": "#DC2626",
            "Cancelled": NEUTRAL,
            "Rescheduled": TANGERINE,
            "Interested": "#2E86C1",
            "Not Interested": NEUTRAL,
            "Closed Won": GREEN,
            "Closed Lost": "#DC2626",
        }
        color = _DISPLAY_COLORS.get(new_status, NEUTRAL)
        return html.Span(
            f"✅ Booking #{booking_id} → {new_status}",
            style={"color": color, "fontSize": "12px", "fontWeight": "600"},
        )
    except Exception as e:
        return html.Span(
            f"❌ Error: {str(e)[:80]}",
            style={"color": "#DC2626", "fontSize": "12px"},
        )


# ── Autopilot Toggle ──
@callback(
    Output("autopilot-toggle-status", "children"),
    Input("autopilot-toggle-btn", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_autopilot(n_clicks):
    if not n_clicks or not _OUTREACH_AVAILABLE:
        return no_update
    try:
        if _autopilot.is_running():
            _autopilot.stop()
            return html.Span(
                "⏸ Autopilot stopped.",
                style={"color": "#DC2626", "fontSize": "12px", "fontWeight": "600"},
            )
        else:
            _autopilot.start()
            return html.Span(
                "▶ Autopilot started!",
                style={"color": GREEN, "fontSize": "12px", "fontWeight": "600"},
            )
    except Exception as e:
        return html.Span(
            f"❌ {str(e)[:80]}", style={"color": "#DC2626", "fontSize": "12px"}
        )


# ── Google Sheet Sync ──
@callback(
    Output("fb-gsheet-sync-status", "children"),
    Input("fb-gsheet-sync-btn", "n_clicks"),
    prevent_initial_call=True,
)
def sync_gsheet(n_clicks):
    if not n_clicks or not _OUTREACH_AVAILABLE:
        return no_update
    try:
        new_count = _sync_gsheet()
        return html.Span(
            f"✅ Synced from Google Sheet — {new_count} new leads imported!",
            style={"color": GREEN, "fontSize": "12px", "fontWeight": "600"},
        )
    except Exception as e:
        return html.Span(
            f"❌ {str(e)[:80]}", style={"color": "#DC2626", "fontSize": "12px"}
        )


# ── FB CSV Import ──
@callback(
    Output("fb-import-status", "children"),
    Input("fb-import-btn", "n_clicks"),
    State("fb-csv-upload", "contents"),
    State("fb-csv-upload", "filename"),
    State("fb-import-campaign", "value"),
    prevent_initial_call=True,
)
def fb_import_csv(n_clicks, contents, filename, campaign):
    if not n_clicks or not contents:
        return html.Span(
            "⚠ Upload a CSV first.", style={"color": NEUTRAL, "fontSize": "12px"}
        )

    try:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string).decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))
        imported = 0
        for row in reader:
            email = (row.get("email") or row.get("Email") or "").strip()
            if not email:
                continue
            fn = (
                row.get("first_name")
                or row.get("First Name")
                or row.get("first name")
                or ""
            ).strip()
            ln = (
                row.get("last_name")
                or row.get("Last Name")
                or row.get("last name")
                or ""
            ).strip()
            phone = (
                row.get("phone") or row.get("Phone") or row.get("phone_number") or ""
            ).strip()
            lead_date = (
                row.get("lead_date") or row.get("created_time") or row.get("date") or ""
            ).strip()
            if not lead_date:
                lead_date = datetime.now(timezone.utc).isoformat()
            upsert_fb_lead(fn, ln, email, phone, campaign, lead_date)
            imported += 1
        return html.Span(
            f"✅ Imported {imported} leads into {campaign}!",
            style={"color": GREEN, "fontSize": "12px", "fontWeight": "600"},
        )
    except Exception as e:
        return html.Span(
            f"❌ Error: {str(e)[:80]}", style={"color": "#DC2626", "fontSize": "12px"}
        )


# ── FB Bulk Email (Re-Engagement) ──
@callback(
    Output("outreach-refresh", "data", allow_duplicate=True),
    Input("fb-re-bulk-email", "n_clicks"),
    prevent_initial_call=True,
)
def fb_re_bulk_email(n_clicks):
    if not n_clicks or not _OUTREACH_AVAILABLE:
        return no_update
    try:
        re_leads = get_fb_leads(campaign="fb_reengagement")
        pending = [
            l
            for l in re_leads
            if not _smart_fb_already_sent(l["email"], "fb_reengagement", "email")
        ]
        for lead in pending:
            ctx_data = {
                "first_name": lead["first_name"] or "Coach",
                "name": lead["first_name"] or "Coach",
            }
            subject, body = render_email("fb_reengagement", ctx_data)
            msg_id = send_email(lead["email"], subject, body)
            if msg_id:
                record_fb_sent(
                    lead["email"], "fb_reengagement", "email", lead["email"], msg_id
                )
    except Exception:
        pass
    return (n_clicks or 0) + 1


# ── FB Bulk SMS (Re-Engagement) ──
@callback(
    Output("outreach-refresh", "data", allow_duplicate=True),
    Input("fb-re-bulk-sms", "n_clicks"),
    prevent_initial_call=True,
)
def fb_re_bulk_sms(n_clicks):
    if not n_clicks or not _OUTREACH_AVAILABLE:
        return no_update
    try:
        re_leads = get_fb_leads(campaign="fb_reengagement")
        pending = [
            l
            for l in re_leads
            if l.get("phone")
            and not _smart_fb_already_sent(
                l["email"], "fb_reengagement", "sms", l.get("phone")
            )
        ]
        for lead in pending:
            ctx_data = {
                "first_name": lead["first_name"] or "Coach",
                "name": lead["first_name"] or "Coach",
            }
            body = render_sms("fb_reengagement", ctx_data)
            msg_id = send_sms(lead["phone"], body)
            if msg_id:
                record_fb_sent(
                    lead["email"], "fb_reengagement", "sms", lead["phone"], msg_id
                )
    except Exception:
        pass
    return (n_clicks or 0) + 1


# ── FB Bulk Email (New Leads) ──
@callback(
    Output("outreach-refresh", "data", allow_duplicate=True),
    Input("fb-nl-bulk-email", "n_clicks"),
    prevent_initial_call=True,
)
def fb_nl_bulk_email(n_clicks):
    if not n_clicks or not _OUTREACH_AVAILABLE:
        return no_update
    try:
        new_leads = get_fb_leads(campaign="fb_new_lead")
        now = datetime.now(timezone.utc)
        cutoff_12h = now - pd.Timedelta(hours=12)
        for lead in new_leads:
            ld = lead.get("lead_date")
            try:
                if ld and pd.to_datetime(ld, utc=True) > cutoff_12h:
                    continue
            except Exception:
                pass
            if _smart_fb_already_sent(lead["email"], "fb_new_lead", "email"):
                continue
            ctx_data = {
                "first_name": lead["first_name"] or "Coach",
                "name": lead["first_name"] or "Coach",
            }
            subject, body = render_email("fb_new_lead", ctx_data)
            msg_id = send_email(lead["email"], subject, body)
            if msg_id:
                record_fb_sent(
                    lead["email"], "fb_new_lead", "email", lead["email"], msg_id
                )
    except Exception:
        pass
    return (n_clicks or 0) + 1


# ── FB Bulk SMS (New Leads) ──
@callback(
    Output("outreach-refresh", "data", allow_duplicate=True),
    Input("fb-nl-bulk-sms", "n_clicks"),
    prevent_initial_call=True,
)
def fb_nl_bulk_sms(n_clicks):
    if not n_clicks or not _OUTREACH_AVAILABLE:
        return no_update
    try:
        new_leads = get_fb_leads(campaign="fb_new_lead")
        now = datetime.now(timezone.utc)
        cutoff_12h = now - pd.Timedelta(hours=12)
        for lead in new_leads:
            ld = lead.get("lead_date")
            try:
                if ld and pd.to_datetime(ld, utc=True) > cutoff_12h:
                    continue
            except Exception:
                pass
            if not lead.get("phone") or _smart_fb_already_sent(
                lead["email"], "fb_new_lead", "sms", lead.get("phone")
            ):
                continue
            ctx_data = {
                "first_name": lead["first_name"] or "Coach",
                "name": lead["first_name"] or "Coach",
            }
            body = render_sms("fb_new_lead", ctx_data)
            msg_id = send_sms(lead["phone"], body)
            if msg_id:
                record_fb_sent(
                    lead["email"], "fb_new_lead", "sms", lead["phone"], msg_id
                )
    except Exception:
        pass
    return (n_clicks or 0) + 1


# ── Individual Email Send (pattern-matching callback) ──
@callback(
    Output({"type": "send-email-status", "index": dash.MATCH}, "children"),
    Input({"type": "send-email-btn", "index": dash.MATCH}, "n_clicks"),
    State({"type": "send-email-btn", "index": dash.MATCH}, "id"),
    prevent_initial_call=True,
)
def send_individual_email(n_clicks, btn_id):
    if not n_clicks or not _OUTREACH_AVAILABLE:
        return no_update
    try:
        index_str = btn_id["index"]
        parts = index_str.rsplit("_", 1)
        if len(parts) == 2:
            app_id_str, tpl_key = parts
        else:
            # Handle template keys with underscores (e.g., "no_activity_7d")
            # The index is "appid_templatekey" where appid is numeric
            for i in range(len(index_str)):
                if index_str[i] == "_":
                    try:
                        int(index_str[:i])
                        app_id_str = index_str[:i]
                        tpl_key = index_str[i + 1 :]
                        break
                    except ValueError:
                        continue
            else:
                return html.Span(
                    "❌ Parse error", style={"color": "#DC2626", "fontSize": "12px"}
                )

        app_id = int(app_id_str)
        prospect = get_prospect(app_id)
        if not prospect:
            return html.Span(
                "❌ Prospect not found", style={"color": "#DC2626", "fontSize": "12px"}
            )

        enriched = _enrich_prospect(prospect)
        email = prospect.get("email", "")
        subject, html_body = render_email(tpl_key, enriched)

        attachment_path = None
        if tpl_key == "cheat_sheet":
            attachment_path = generate_cheat_sheet(enriched)

        msg_id = send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            attachment_path=attachment_path,
        )
        record_sent(app_id, tpl_key, "email", email, msg_id)

        if msg_id:
            return html.Span(
                f"✅ Sent to {email}!",
                style={"color": GREEN, "fontSize": "12px", "fontWeight": "600"},
            )
        else:
            return html.Span(
                "❌ Failed — check Brevo API key",
                style={"color": "#DC2626", "fontSize": "12px"},
            )
    except Exception as e:
        return html.Span(
            f"❌ {str(e)[:80]}", style={"color": "#DC2626", "fontSize": "12px"}
        )


# ── SMS Bulk Send ──
@callback(
    Output("sms-bulk-status", "children"),
    Input("sms-bulk-send-btn", "n_clicks"),
    State("sms-template-select", "value"),
    prevent_initial_call=True,
)
def sms_bulk_send(n_clicks, sms_tpl):
    if not n_clicks or not _OUTREACH_AVAILABLE:
        return no_update
    try:
        bq_phones = fetch_all_phones()
        now = datetime.now(timezone.utc)
        cutoff_14d = now - pd.Timedelta(days=14)
        cutoff_24h = now - pd.Timedelta(hours=24)

        sent_count = 0
        for p in bq_phones:
            sd = p.get("created_at")
            if not sd or sd in ("None", ""):
                continue
            try:
                dt = pd.to_datetime(sd, utc=True)
                if not (cutoff_14d <= dt <= cutoff_24h):
                    continue
            except Exception:
                continue
            if has_returned_after_signup(p["application_id"]):
                continue
            p["phone"] = p.get("phone_number", "")
            p["name"] = p.get("application_name", "Coach")
            if not p["phone"]:
                continue
            if _smart_already_sent(p["application_id"], sms_tpl, "sms", p.get("phone")):
                continue

            enriched = _enrich_prospect(p)
            body = render_sms(sms_tpl, enriched)
            msg_id = send_sms(p["phone"], body)
            if msg_id:
                record_sent(p["application_id"], sms_tpl, "sms", p["phone"], msg_id)
                sent_count += 1

        return html.Span(
            f"✅ Sent {sent_count} SMS messages!",
            style={"color": GREEN, "fontSize": "12px", "fontWeight": "600"},
        )
    except Exception as e:
        return html.Span(
            f"❌ {str(e)[:80]}", style={"color": "#DC2626", "fontSize": "12px"}
        )


# ── Save Phone (Prospects tab) ──
@callback(
    Output("prospect-phone-status", "children"),
    Input("prospect-save-phone-btn", "n_clicks"),
    State("prospect-phone-appid", "value"),
    State("prospect-phone-input", "value"),
    prevent_initial_call=True,
)
def save_prospect_phone(n_clicks, app_id, phone):
    if not n_clicks or not app_id or not phone:
        return html.Span(
            "⚠ Enter App ID and phone.", style={"color": NEUTRAL, "fontSize": "12px"}
        )
    try:
        upsert_prospect(int(app_id), phone=phone)
        return html.Span(
            f"✅ Phone {phone} saved for app {app_id}",
            style={"color": GREEN, "fontSize": "12px", "fontWeight": "600"},
        )
    except Exception as e:
        return html.Span(
            f"❌ {str(e)[:80]}", style={"color": "#DC2626", "fontSize": "12px"}
        )


# ── Phone CSV Import ──
@callback(
    Output("phone-import-status", "children"),
    Input("phone-import-btn", "n_clicks"),
    State("phone-csv-upload", "contents"),
    prevent_initial_call=True,
)
def phone_import_csv(n_clicks, contents):
    if not n_clicks or not contents:
        return html.Span(
            "⚠ Upload a CSV first.", style={"color": NEUTRAL, "fontSize": "12px"}
        )
    try:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string).decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))
        updated = 0
        for row in reader:
            phone = (row.get("phone") or "").strip()
            if not phone:
                continue
            app_id = (row.get("application_id") or "").strip()
            email_val = (row.get("email") or "").strip()
            if app_id:
                upsert_prospect(int(app_id), phone=phone)
                updated += 1
            elif email_val:
                all_p = get_all_prospects()
                for ap in all_p:
                    if (ap.get("email") or "").lower() == email_val.lower():
                        upsert_prospect(ap["application_id"], phone=phone)
                        updated += 1
                        break
        return html.Span(
            f"✅ Updated {updated} phone numbers!",
            style={"color": GREEN, "fontSize": "12px", "fontWeight": "600"},
        )
    except Exception as e:
        return html.Span(
            f"❌ {str(e)[:80]}", style={"color": "#DC2626", "fontSize": "12px"}
        )


# ── Manual Phone Save ──
@callback(
    Output("manual-phone-status", "children"),
    Input("manual-phone-save-btn", "n_clicks"),
    State("manual-phone-appid", "value"),
    State("manual-phone-input", "value"),
    prevent_initial_call=True,
)
def manual_phone_save(n_clicks, app_id, phone):
    if not n_clicks or not app_id or not phone:
        return html.Span(
            "⚠ Enter both fields.", style={"color": NEUTRAL, "fontSize": "12px"}
        )
    try:
        upsert_prospect(int(app_id), phone=phone)
        return html.Span(
            f"✅ Phone {phone} saved for app {app_id}",
            style={"color": GREEN, "fontSize": "12px", "fontWeight": "600"},
        )
    except Exception as e:
        return html.Span(
            f"❌ {str(e)[:80]}", style={"color": "#DC2626", "fontSize": "12px"}
        )


# ── Generate Cheat Sheet ──
@callback(
    Output("cheatsheet-status", "children"),
    Output("outreach-download", "data"),
    Input("cheatsheet-gen-btn", "n_clicks"),
    State("cheatsheet-prospect-select", "value"),
    prevent_initial_call=True,
)
def generate_cheatsheet(n_clicks, app_id_str):
    if not n_clicks or not app_id_str:
        return (
            html.Span(
                "⚠ Select a prospect.", style={"color": NEUTRAL, "fontSize": "12px"}
            ),
            no_update,
        )
    try:
        prospect = get_prospect(int(app_id_str))
        if not prospect:
            return (
                html.Span(
                    "❌ Prospect not found.",
                    style={"color": "#DC2626", "fontSize": "12px"},
                ),
                no_update,
            )

        enriched = _enrich_prospect(prospect)
        pdf_path = generate_cheat_sheet(enriched)

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        name = prospect.get("name", "coach").replace(" ", "_")
        filename = f"cheatsheet_{name}.pdf"
        status = html.Span(
            f"✅ PDF generated!",
            style={"color": GREEN, "fontSize": "12px", "fontWeight": "600"},
        )
        return status, dcc.send_bytes(pdf_bytes, filename)
    except Exception as e:
        return (
            html.Span(
                f"❌ {str(e)[:80]}", style={"color": "#DC2626", "fontSize": "12px"}
            ),
            no_update,
        )


# ── Sync Sign-ups ──
@callback(
    Output("sync-signups-status", "children"),
    Input("sync-signups-btn", "n_clicks"),
    State("sync-hours-input", "value"),
    prevent_initial_call=True,
)
def sync_signups(n_clicks, hours):
    if not n_clicks or not _OUTREACH_AVAILABLE:
        return no_update
    try:
        hours = int(hours or 168)
        signups = fetch_new_signups(since_hours=hours)
        synced = 0
        for s in signups:
            app_id = s["application_id"]
            profile = fetch_prospect_profile(app_id)
            profile["name"] = s.get("name") or profile.get("app_name", "Coach")
            profile["email"] = s.get("email") or profile.get("email", "")
            upsert_prospect(
                application_id=app_id,
                name=profile.get("name"),
                email=profile.get("email"),
                phone=profile.get("phone"),
                coach_type=profile.get("coach_type"),
                country=profile.get("country"),
                signup_date=str(s.get("signup_date", "")),
                profile_json=json.dumps(profile, default=str),
            )
            synced += 1
        return html.Span(
            f"✅ Synced {synced} prospects from last {hours}h!",
            style={"color": GREEN, "fontSize": "12px", "fontWeight": "600"},
        )
    except Exception as e:
        return html.Span(
            f"❌ {str(e)[:80]}", style={"color": "#DC2626", "fontSize": "12px"}
        )


# ── Sync Phones ──
@callback(
    Output("sync-phones-status", "children"),
    Input("sync-phones-btn", "n_clicks"),
    prevent_initial_call=True,
)
def sync_phones(n_clicks):
    if not n_clicks or not _OUTREACH_AVAILABLE:
        return no_update
    try:
        phone_records = fetch_all_phones()
        updated = 0
        for rec in phone_records:
            app_id = rec.get("application_id")
            phone = rec.get("phone_number")
            if not phone:
                continue
            if app_id:
                upsert_prospect(int(app_id), phone=phone)
                updated += 1
            else:
                email_val = rec.get("email", "")
                if email_val:
                    all_p = get_all_prospects()
                    for ap in all_p:
                        if (ap.get("email") or "").lower() == email_val.lower():
                            upsert_prospect(ap["application_id"], phone=phone)
                            updated += 1
                            break
        return html.Span(
            f"✅ Updated {updated} phone numbers!",
            style={"color": GREEN, "fontSize": "12px", "fontWeight": "600"},
        )
    except Exception as e:
        return html.Span(
            f"❌ {str(e)[:80]}", style={"color": "#DC2626", "fontSize": "12px"}
        )


# ═══════════════════════════════════════════════════════════════
# 📈  AD PERFORMANCE (Meta Marketing API)
# ═══════════════════════════════════════════════════════════════
def _render_ad_performance():
    if not _OUTREACH_AVAILABLE:
        return _not_available()

    import plotly.express as px
    import plotly.graph_objects as go

    children = [section_header("📈 Meta Ad Performance")]

    import os

    has_token = bool(os.getenv("META_ACCESS_TOKEN", ""))
    has_account = bool(os.getenv("META_AD_ACCOUNT_ID", ""))

    if not has_token or not has_account:
        children.append(
            dbc.Alert(
                [
                    html.H5("Meta API Not Configured"),
                    html.P(
                        "Set META_ACCESS_TOKEN and META_AD_ACCOUNT_ID environment variables to "
                        "view ad performance data."
                    ),
                ],
                color="info",
            )
        )
        return html.Div(children)

    try:
        summary = _fb_account_summary(days_back=90)
    except Exception as exc:
        print(f"[outreach] _fb_account_summary error: {exc}")
        summary = {}

    if not summary:
        children.append(
            dbc.Alert(
                [
                    html.H5("Meta API — No Data Returned"),
                    html.P(
                        "Credentials are set but the API returned no data. "
                        "This may mean: (1) the access token has expired, "
                        "(2) no ads ran in the last 90 days, or "
                        "(3) the ad account ID is incorrect. Check Cloud Run logs for details."
                    ),
                ],
                color="warning",
            )
        )
        return html.Div(children)

    spend = float(summary.get("spend", 0))
    impressions = int(summary.get("impressions", 0))
    reach = int(summary.get("reach", 0))
    clicks = int(summary.get("clicks", 0))
    ctr = float(summary.get("ctr", 0))
    cpc = float(summary.get("cpc", 0))
    cpm = float(summary.get("cpm", 0))
    frequency = float(summary.get("frequency", 0))
    actions = summary.get("actions", [])
    leads = _fb_action_val(actions, "leadgen.other")
    if not leads:
        leads = _fb_action_val(actions, "lead")
    cpl = spend / leads if leads > 0 else 0

    children.append(
        dbc.Row(
            [
                dbc.Col(metric_card("Total Spend", f"£{spend:,.2f}"), md=2),
                dbc.Col(metric_card("Impressions", f"{impressions:,}"), md=2),
                dbc.Col(metric_card("Reach", f"{reach:,}"), md=2),
                dbc.Col(metric_card("Clicks", f"{clicks:,}"), md=2),
                dbc.Col(metric_card("Leads", f"{leads:,}"), md=2),
                dbc.Col(metric_card("Cost/Lead", f"£{cpl:,.2f}"), md=2),
            ],
            className="mb-3",
        )
    )
    children.append(
        dbc.Row(
            [
                dbc.Col(metric_card("CTR", f"{ctr:.2f}%"), md=3),
                dbc.Col(metric_card("CPC", f"£{cpc:,.2f}"), md=3),
                dbc.Col(metric_card("CPM", f"£{cpm:,.2f}"), md=3),
                dbc.Col(metric_card("Frequency", f"{frequency:.1f}"), md=3),
            ],
            className="mb-3",
        )
    )
    children.append(html.Hr())

    # Campaign breakdown
    try:
        campaigns = _fb_campaign_insights(days_back=90)
    except Exception:
        campaigns = []

    if campaigns:
        children.append(section_header("Campaign Breakdown"))
        rows = []
        for c in campaigns:
            c_actions = c.get("actions", [])
            c_leads = _fb_action_val(c_actions, "leadgen.other") or _fb_action_val(
                c_actions, "lead"
            )
            c_spend = float(c.get("spend", 0))
            rows.append(
                {
                    "Campaign": c.get("campaign_name", ""),
                    "Spend": f"£{c_spend:,.2f}",
                    "Impressions": int(c.get("impressions", 0)),
                    "Clicks": int(c.get("clicks", 0)),
                    "Leads": c_leads,
                    "CPL": f"£{c_spend / c_leads:,.2f}" if c_leads > 0 else "N/A",
                    "CTR": f"{float(c.get('ctr', 0)):.2f}%",
                }
            )
        df_camp = pd.DataFrame(rows)
        children.append(
            card_wrapper(
                dash_table.DataTable(
                    data=df_camp.to_dict("records"),
                    columns=[{"name": col, "id": col} for col in df_camp.columns],
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "fontSize": "12px",
                        "padding": "6px",
                        "fontFamily": "Sora",
                        "textAlign": "left",
                    },
                    style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
                    sort_action="native",
                )
            )
        )
        children.append(html.Hr())

    # Age + Gender breakdown
    try:
        demo_data = _fb_demo_insights(days_back=90, breakdown="age,gender")
    except Exception:
        demo_data = []

    if demo_data:
        children.append(section_header("Audience Demographics"))
        demo_rows = []
        for d in demo_data:
            d_actions = d.get("actions", [])
            d_leads = _fb_action_val(d_actions, "leadgen.other") or _fb_action_val(
                d_actions, "lead"
            )
            demo_rows.append(
                {
                    "Age": d.get("age", ""),
                    "Gender": d.get("gender", ""),
                    "Impressions": int(d.get("impressions", 0)),
                    "Clicks": int(d.get("clicks", 0)),
                    "Spend": float(d.get("spend", 0)),
                    "Leads": d_leads,
                }
            )
        df_demo = pd.DataFrame(demo_rows)

        if not df_demo.empty:
            age_agg = (
                df_demo.groupby("Age")[["Impressions", "Clicks", "Leads"]]
                .sum()
                .reset_index()
            )
            fig_age = px.bar(
                age_agg,
                x="Age",
                y=["Impressions", "Clicks", "Leads"],
                title="Performance by Age Group",
                barmode="group",
            )
            fig_age.update_layout(height=350)

            gender_agg = (
                df_demo.groupby("Gender")[["Impressions", "Clicks", "Leads"]]
                .sum()
                .reset_index()
            )
            fig_gender = px.pie(
                gender_agg,
                names="Gender",
                values="Impressions",
                title="Impressions by Gender",
            )
            fig_gender.update_layout(height=300)

            children.append(
                dbc.Row(
                    [
                        dbc.Col(dcc.Graph(figure=fig_age), md=7),
                        dbc.Col(dcc.Graph(figure=fig_gender), md=5),
                    ]
                )
            )
        children.append(html.Hr())

    # Placement breakdown
    try:
        place_data = _fb_placement_insights(days_back=90)
    except Exception:
        place_data = []

    if place_data:
        children.append(section_header("Placement Breakdown"))
        place_rows = []
        for p in place_data:
            place_rows.append(
                {
                    "Platform": p.get("publisher_platform", ""),
                    "Position": p.get("platform_position", ""),
                    "Impressions": int(p.get("impressions", 0)),
                    "Clicks": int(p.get("clicks", 0)),
                    "Spend": f"£{float(p.get('spend', 0)):,.2f}",
                }
            )
        df_place = pd.DataFrame(place_rows)
        if not df_place.empty:
            fig_place = px.bar(
                df_place,
                x="Position",
                y="Impressions",
                color="Platform",
                title="Impressions by Placement",
                barmode="stack",
            )
            fig_place.update_layout(height=350)
            children.append(dcc.Graph(figure=fig_place))
        children.append(html.Hr())

    # Country breakdown
    try:
        country_data = _fb_country_insights(days_back=90)
    except Exception:
        country_data = []

    if country_data:
        children.append(section_header("Geographic Breakdown"))
        country_rows = []
        for cr in country_data:
            cr_actions = cr.get("actions", [])
            cr_leads = _fb_action_val(cr_actions, "leadgen.other") or _fb_action_val(
                cr_actions, "lead"
            )
            country_rows.append(
                {
                    "Country": cr.get("country", ""),
                    "Impressions": int(cr.get("impressions", 0)),
                    "Clicks": int(cr.get("clicks", 0)),
                    "Spend": float(cr.get("spend", 0)),
                    "Leads": cr_leads,
                }
            )
        df_country = pd.DataFrame(country_rows)
        if not df_country.empty:
            fig_map = px.choropleth(
                df_country,
                locations="Country",
                locationmode="ISO-3",
                color="Impressions",
                title="Ad Reach by Country",
                color_continuous_scale="Greens",
            )
            fig_map.update_layout(height=400)
            children.append(dcc.Graph(figure=fig_map))

    return html.Div(children)


# ═══════════════════════════════════════════════════════════════
# 🧑  LEAD INSIGHTS (Meta Lead Forms)
# ═══════════════════════════════════════════════════════════════
def _render_lead_insights():
    if not _OUTREACH_AVAILABLE:
        return _not_available()

    import plotly.express as px

    children = [section_header("🧑 Lead Insights")]

    import os

    has_token = bool(os.getenv("META_ACCESS_TOKEN", ""))
    has_account = bool(os.getenv("META_AD_ACCOUNT_ID", ""))
    has_page = bool(os.getenv("META_PAGE_ID", ""))

    if not has_token or not has_account or not has_page:
        children.append(
            dbc.Alert(
                [
                    html.H5("Meta API Not Configured"),
                    html.P(
                        "Set META_ACCESS_TOKEN, META_AD_ACCOUNT_ID, and META_PAGE_ID "
                        "environment variables to view lead data."
                    ),
                ],
                color="info",
            )
        )
        return html.Div(children)

    try:
        raw_leads = _fb_all_leads(limit=500)
    except Exception as exc:
        print(f"[outreach] _fb_all_leads error: {exc}")
        raw_leads = []

    if not raw_leads:
        children.append(
            dbc.Alert(
                [
                    html.H5("No Lead Data Available"),
                    html.P(
                        "Credentials are set but no leads were returned. "
                        "This may mean: (1) no lead ad forms exist on this page, "
                        "(2) the access token has expired, or "
                        "(3) the Page ID is incorrect. Check Cloud Run logs for details."
                    ),
                ],
                color="warning",
            )
        )
        return html.Div(children)

    leads = [_fb_parse_lead(l) for l in raw_leads]
    df = pd.DataFrame(leads)

    total_leads = len(df)
    organic = len(df[df["is_organic"] == True]) if "is_organic" in df.columns else 0
    paid = total_leads - organic
    campaigns = df["campaign_name"].nunique() if "campaign_name" in df.columns else 0
    forms = df["form_name"].nunique() if "form_name" in df.columns else 0

    children.append(
        dbc.Row(
            [
                dbc.Col(metric_card("Total Leads", f"{total_leads:,}"), md=2),
                dbc.Col(metric_card("Paid Leads", f"{paid:,}"), md=2),
                dbc.Col(metric_card("Organic Leads", f"{organic:,}"), md=2),
                dbc.Col(metric_card("Campaigns", f"{campaigns:,}"), md=2),
                dbc.Col(metric_card("Lead Forms", f"{forms:,}"), md=2),
            ],
            className="mb-3",
        )
    )
    children.append(html.Hr())

    # Lead timeline
    if "created_time" in df.columns:
        df["date"] = pd.to_datetime(df["created_time"], errors="coerce").dt.date
        daily = df.groupby("date").size().reset_index(name="Leads")
        if not daily.empty:
            children.append(section_header("Lead Volume Over Time"))
            fig_timeline = px.bar(daily, x="date", y="Leads", title="Daily Leads")
            fig_timeline.update_layout(height=300)
            children.append(dcc.Graph(figure=fig_timeline))
            children.append(html.Hr())

    # By Campaign
    if "campaign_name" in df.columns:
        camp_counts = df["campaign_name"].value_counts().reset_index()
        camp_counts.columns = ["Campaign", "Leads"]
        if not camp_counts.empty:
            children.append(section_header("Leads by Campaign"))
            fig_camp = px.bar(
                camp_counts, x="Campaign", y="Leads", title="Leads by Campaign"
            )
            fig_camp.update_layout(height=300)
            children.append(dcc.Graph(figure=fig_camp))
            children.append(html.Hr())

    # By Platform
    if "platform" in df.columns:
        plat_counts = df["platform"].value_counts().reset_index()
        plat_counts.columns = ["Platform", "Leads"]
        if not plat_counts.empty and len(plat_counts) > 1:
            children.append(section_header("Leads by Platform"))
            fig_plat = px.pie(
                plat_counts,
                names="Platform",
                values="Leads",
                title="Facebook vs Instagram",
            )
            fig_plat.update_layout(height=300)
            children.append(dcc.Graph(figure=fig_plat))
            children.append(html.Hr())

    # By Form
    if "form_name" in df.columns:
        form_counts = df["form_name"].value_counts().reset_index()
        form_counts.columns = ["Form", "Leads"]
        if not form_counts.empty:
            children.append(section_header("Leads by Form"))
            fig_form = px.bar(
                form_counts,
                x="Form",
                y="Leads",
                title="Which forms generate the most leads",
            )
            fig_form.update_layout(height=300)
            children.append(dcc.Graph(figure=fig_form))
            children.append(html.Hr())

    # Lead detail table
    children.append(section_header("All Leads"))
    display_cols = [c for c in df.columns if c not in ("is_organic", "date")]
    children.append(
        card_wrapper(
            dash_table.DataTable(
                data=(
                    df[display_cols].to_dict("records")
                    if display_cols
                    else df.to_dict("records")
                ),
                columns=[{"name": c, "id": c} for c in (display_cols or df.columns)],
                style_table={"overflowX": "auto"},
                style_cell={
                    "fontSize": "12px",
                    "padding": "6px",
                    "fontFamily": "Sora",
                    "textAlign": "left",
                },
                style_header={"fontWeight": "600", "backgroundColor": "#F2F3EE"},
                page_size=25,
                sort_action="native",
                filter_action="native",
            )
        )
    )

    return html.Div(children)

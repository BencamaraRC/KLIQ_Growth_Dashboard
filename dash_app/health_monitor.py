"""
KLIQ Dashboard — Hourly Health Monitor
Checks all BQ tables + external APIs every hour.
Sends a Brevo email summary when any check fails.
"""

import os
import sys
import threading
import time
import logging
import requests
from datetime import datetime, timezone

log = logging.getLogger("health_monitor")
log.setLevel(logging.INFO)
if not log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(
        logging.Formatter("[%(asctime)s] HEALTH %(levelname)s  %(message)s", "%H:%M:%S")
    )
    log.addHandler(_h)

# ── Config ──
ALERT_EMAIL = os.environ.get("HEALTH_ALERT_EMAIL", "ben@joinkliq.io")
CHECK_INTERVAL_H = int(os.environ.get("HEALTH_CHECK_HOURS", "1"))
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_FROM_EMAIL = os.environ.get("BREVO_FROM_EMAIL", "ben@joinkliq.io")
BREVO_FROM_NAME = os.environ.get("BREVO_FROM_NAME", "KLIQ Health Monitor")

# ── BQ tables to monitor ──
# (table_name, expected_min_rows, description)
BQ_TABLES = [
    # Core growth
    ("d1_growth_metrics", 50, "Sign-ups, upgrades, subscriptions"),
    ("d1_onboarding_funnel", 10, "Onboarding funnel steps"),
    ("d1_engagement_funnel", 10, "Coach engagement funnel"),
    ("d1_activation_score", 100, "Activation scores per app"),
    ("d1_leads_sales", 5, "Weekly leads & sales"),
    ("d1_device_type", 5, "Sign-ups by device"),
    ("d1_invoice_revenue", 10, "Invoice revenue"),
    ("d1_appfee_revenue", 5, "KLIQ app fees"),
    ("d1_revenue_summary", 10, "Revenue summary"),
    ("d1_coach_summary", 10, "Coach summary"),
    ("d1_coach_engagement", 10, "Coach community engagement"),
    ("d1_churn_analysis", 5, "Churn analysis"),
    ("d1_retention_analysis", 5, "Retention analysis"),
    ("d1_coach_gmv_timeline", 5, "Coach GMV timeline"),
    ("d1_app_status", 5, "App status"),
    # Leads & external
    ("d1_demo_calls", 1, "Google Calendar demo calls"),
    ("d1_meta_ads", 1, "Meta/Facebook ads"),
    ("d1_tiktok_ads", 0, "TikTok ads (may be empty)"),
    # GA4
    ("d1_ga4_acquisition", 10, "GA4 acquisition"),
    ("d1_ga4_traffic", 10, "GA4 traffic"),
    ("d1_ga4_funnel", 5, "GA4 website funnel"),
    # App Store & Play Store
    ("d1_appstore_sales", 1000, "Apple App Store sales"),
    ("d1_unified_revenue", 10, "Unified revenue (Stripe+iOS+Google)"),
    ("d1_ios_downloads", 5, "iOS downloads"),
    ("d1_apple_analytics", 10, "Apple analytics"),
    ("d1_play_store_performance", 1, "Google Play performance"),
    ("d1_google_earnings", 100, "Google Play earnings"),
    # App performance
    ("d1_app_engagement", 10, "App engagement metrics"),
    ("d1_app_device_breakdown", 5, "App device breakdown"),
    ("d1_app_downloads", 5, "App downloads"),
    ("d1_app_top_users", 5, "Top users per app"),
    # Dashboard 2
    ("d2_app_lookup", 10, "App lookup"),
    ("d2_engagement", 10, "D2 engagement"),
    ("d2_subscriptions_revenue", 5, "D2 subscriptions"),
    ("d2_user_overview", 5, "D2 user overview"),
    ("d2_dau", 10, "Daily active users"),
    ("d2_mau", 5, "Monthly active users"),
]


def _send_alert_email(subject, html_body):
    """Send alert email via Brevo."""
    if not BREVO_API_KEY:
        log.warning("BREVO_API_KEY not set — cannot send health alert email")
        return False

    payload = {
        "sender": {"email": BREVO_FROM_EMAIL, "name": BREVO_FROM_NAME},
        "to": [{"email": ALERT_EMAIL}],
        "subject": subject,
        "htmlContent": html_body,
        "tags": ["kliq-health-monitor"],
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY,
    }
    try:
        resp = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        log.info(f"Alert email sent to {ALERT_EMAIL}")
        return True
    except Exception as e:
        log.error(f"Failed to send alert email: {e}")
        return False


def check_bq_tables():
    """Check all BQ tables for existence and minimum row count."""
    results = []
    try:
        from data import query, T
    except ImportError:
        _dash_dir = os.path.dirname(os.path.abspath(__file__))
        if _dash_dir not in sys.path:
            sys.path.insert(0, _dash_dir)
        from data import query, T

    for table_name, min_rows, description in BQ_TABLES:
        try:
            df = query(f"SELECT COUNT(*) AS cnt FROM {T(table_name)}")
            if df.empty:
                results.append(
                    {
                        "name": table_name,
                        "description": description,
                        "status": "FAIL",
                        "detail": "Query returned empty",
                        "rows": 0,
                    }
                )
            else:
                cnt = int(df.iloc[0]["cnt"])
                ok = cnt >= min_rows
                results.append(
                    {
                        "name": table_name,
                        "description": description,
                        "status": "OK" if ok else "WARN",
                        "detail": f"{cnt:,} rows"
                        + ("" if ok else f" (expected ≥{min_rows})"),
                        "rows": cnt,
                    }
                )
        except Exception as e:
            results.append(
                {
                    "name": table_name,
                    "description": description,
                    "status": "FAIL",
                    "detail": str(e)[:200],
                    "rows": 0,
                }
            )
    return results


def check_external_apis():
    """Check connectivity to external APIs."""
    results = []

    # 1. Brevo
    brevo_key = os.environ.get("BREVO_API_KEY", "")
    if brevo_key:
        try:
            resp = requests.get(
                "https://api.brevo.com/v3/account",
                headers={"api-key": brevo_key, "accept": "application/json"},
                timeout=15,
            )
            ok = resp.status_code == 200
            results.append(
                {
                    "name": "Brevo (Email)",
                    "status": "OK" if ok else "FAIL",
                    "detail": f"HTTP {resp.status_code}"
                    + (f" — {resp.json().get('email', '')}" if ok else ""),
                }
            )
        except Exception as e:
            results.append(
                {"name": "Brevo (Email)", "status": "FAIL", "detail": str(e)[:200]}
            )
    else:
        results.append(
            {"name": "Brevo (Email)", "status": "SKIP", "detail": "API key not set"}
        )

    # 2. Twilio
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    if twilio_sid and twilio_token:
        try:
            resp = requests.get(
                f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}.json",
                auth=(twilio_sid, twilio_token),
                timeout=15,
            )
            ok = resp.status_code == 200
            detail = f"HTTP {resp.status_code}"
            if ok:
                detail += f" — {resp.json().get('friendly_name', '')}"
            else:
                detail += f" — {resp.json().get('message', 'Auth failed')}"
            results.append(
                {
                    "name": "Twilio (SMS)",
                    "status": "OK" if ok else "FAIL",
                    "detail": detail,
                }
            )
        except Exception as e:
            results.append(
                {"name": "Twilio (SMS)", "status": "FAIL", "detail": str(e)[:200]}
            )
    else:
        results.append(
            {"name": "Twilio (SMS)", "status": "SKIP", "detail": "Credentials not set"}
        )

    # 3. Meta / Facebook Ads
    meta_token = os.environ.get("META_ACCESS_TOKEN", "")
    meta_account = os.environ.get("META_AD_ACCOUNT_ID", "")
    if meta_token and meta_account:
        try:
            resp = requests.get(
                f"https://graph.facebook.com/v21.0/{meta_account}",
                params={"access_token": meta_token, "fields": "name,account_status"},
                timeout=15,
            )
            ok = resp.status_code == 200
            detail = f"HTTP {resp.status_code}"
            if ok:
                detail += f" — {resp.json().get('name', '')}"
            else:
                err = resp.json().get("error", {})
                detail += f" — {err.get('message', 'Unknown error')[:100]}"
            results.append(
                {
                    "name": "Meta Ads API",
                    "status": "OK" if ok else "FAIL",
                    "detail": detail,
                }
            )
        except Exception as e:
            results.append(
                {"name": "Meta Ads API", "status": "FAIL", "detail": str(e)[:200]}
            )
    else:
        results.append(
            {"name": "Meta Ads API", "status": "SKIP", "detail": "Token not set"}
        )

    # 4. Calendly
    calendly_token = os.environ.get("CALENDLY_API_TOKEN", "")
    if calendly_token:
        try:
            resp = requests.get(
                "https://api.calendly.com/users/me",
                headers={"Authorization": f"Bearer {calendly_token}"},
                timeout=15,
            )
            ok = resp.status_code == 200
            detail = f"HTTP {resp.status_code}"
            if ok:
                detail += f" — {resp.json().get('resource', {}).get('name', '')}"
            results.append(
                {"name": "Calendly", "status": "OK" if ok else "FAIL", "detail": detail}
            )
        except Exception as e:
            results.append(
                {"name": "Calendly", "status": "FAIL", "detail": str(e)[:200]}
            )
    else:
        results.append(
            {"name": "Calendly", "status": "SKIP", "detail": "Token not set"}
        )

    # 5. TikTok Ads
    tiktok_token = os.environ.get("TIKTOK_ACCESS_TOKEN", "")
    tiktok_adv = os.environ.get("TIKTOK_ADVERTISER_ID", "")
    if tiktok_token and tiktok_adv:
        try:
            resp = requests.get(
                "https://business-api.tiktok.com/open_api/v1.3/advertiser/info/",
                headers={"Access-Token": tiktok_token},
                params={"advertiser_ids": f'["{tiktok_adv}"]'},
                timeout=15,
            )
            ok = resp.status_code == 200 and resp.json().get("code") == 0
            detail = f"HTTP {resp.status_code}"
            if ok:
                data = resp.json().get("data", {}).get("list", [{}])
                detail += f" — {data[0].get('name', '')}" if data else ""
            else:
                detail += f" — {resp.json().get('message', '')[:100]}"
            results.append(
                {
                    "name": "TikTok Ads",
                    "status": "OK" if ok else "FAIL",
                    "detail": detail,
                }
            )
        except Exception as e:
            results.append(
                {"name": "TikTok Ads", "status": "FAIL", "detail": str(e)[:200]}
            )
    else:
        results.append(
            {"name": "TikTok Ads", "status": "SKIP", "detail": "Token not set"}
        )

    # 6. Google BigQuery (basic connectivity)
    try:
        from data import query

        df = query("SELECT 1 AS ok")
        ok = not df.empty
        results.append(
            {
                "name": "BigQuery",
                "status": "OK" if ok else "FAIL",
                "detail": "Connected" if ok else "Query returned empty",
            }
        )
    except Exception as e:
        results.append({"name": "BigQuery", "status": "FAIL", "detail": str(e)[:200]})

    return results


def check_credits():
    """Check Brevo sending credits and Twilio account balance."""
    results = []

    # Brevo credits
    brevo_key = os.environ.get("BREVO_API_KEY", "")
    if brevo_key:
        try:
            resp = requests.get(
                "https://api.brevo.com/v3/account",
                headers={"api-key": brevo_key, "accept": "application/json"},
                timeout=15,
            )
            if resp.status_code == 200:
                acct = resp.json()
                plans = acct.get("plan", [])
                email_plan = next(
                    (p for p in plans if p.get("type") == "subscription"), {}
                )
                credits = email_plan.get("credits", 0)
                period_end = email_plan.get("endDate", "unknown")
                ok = credits > 0
                results.append(
                    {
                        "name": "Brevo Email Credits",
                        "status": "OK" if ok else "FAIL",
                        "detail": f"{credits:,} remaining (resets {period_end})",
                        "credits": credits,
                    }
                )
            else:
                results.append(
                    {
                        "name": "Brevo Email Credits",
                        "status": "FAIL",
                        "detail": f"HTTP {resp.status_code}",
                        "credits": 0,
                    }
                )
        except Exception as e:
            results.append(
                {
                    "name": "Brevo Email Credits",
                    "status": "FAIL",
                    "detail": str(e)[:150],
                    "credits": 0,
                }
            )
    else:
        results.append(
            {
                "name": "Brevo Email Credits",
                "status": "SKIP",
                "detail": "API key not set",
                "credits": 0,
            }
        )

    # AWS SES sending quota
    aws_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
    aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    aws_region = os.environ.get("AWS_SES_REGION", "eu-west-2")
    email_provider = os.environ.get("EMAIL_PROVIDER", "ses+brevo")
    if aws_key and aws_secret:
        try:
            import boto3

            ses = boto3.client(
                "ses",
                region_name=aws_region,
                aws_access_key_id=aws_key,
                aws_secret_access_key=aws_secret,
            )
            quota = ses.get_send_quota()
            max_24h = int(quota.get("Max24HourSend", 0))
            sent_24h = int(quota.get("SentLast24Hours", 0))
            remaining = max_24h - sent_24h
            max_per_sec = quota.get("MaxSendRate", 0)
            ok = remaining > 0
            results.append(
                {
                    "name": "AWS SES Quota",
                    "status": "OK" if ok else "FAIL",
                    "detail": f"{remaining:,} remaining of {max_24h:,}/day ({sent_24h:,} sent) · {max_per_sec}/sec",
                    "credits": remaining,
                }
            )
        except Exception as e:
            results.append(
                {
                    "name": "AWS SES Quota",
                    "status": "FAIL",
                    "detail": str(e)[:150],
                    "credits": 0,
                }
            )
    else:
        results.append(
            {
                "name": "AWS SES Quota",
                "status": "SKIP",
                "detail": "AWS credentials not set",
                "credits": 0,
            }
        )

    # Active email provider
    results.append(
        {
            "name": "Email Provider",
            "status": "OK",
            "detail": f"Mode: {email_provider}",
            "credits": -1,
        }
    )

    # Twilio balance
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    if twilio_sid and twilio_token:
        try:
            resp = requests.get(
                f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Balance.json",
                auth=(twilio_sid, twilio_token),
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                balance = float(data.get("balance", 0))
                currency = data.get("currency", "USD")
                ok = balance > 1.0
                status = "OK" if ok else ("WARN" if balance > 0 else "FAIL")
                results.append(
                    {
                        "name": "Twilio SMS Balance",
                        "status": status,
                        "detail": f"{currency} {balance:.2f}",
                        "balance": balance,
                        "currency": currency,
                    }
                )
            else:
                results.append(
                    {
                        "name": "Twilio SMS Balance",
                        "status": "FAIL",
                        "detail": f"HTTP {resp.status_code}",
                        "balance": 0,
                    }
                )
        except Exception as e:
            results.append(
                {
                    "name": "Twilio SMS Balance",
                    "status": "FAIL",
                    "detail": str(e)[:150],
                    "balance": 0,
                }
            )
    else:
        results.append(
            {
                "name": "Twilio SMS Balance",
                "status": "SKIP",
                "detail": "Credentials not set",
                "balance": 0,
            }
        )

    return results


def run_health_check():
    """Run full health check and return structured results."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    log.info(f"Running health check at {now}")

    bq_results = check_bq_tables()
    api_results = check_external_apis()
    credit_results = check_credits()

    bq_failures = [r for r in bq_results if r["status"] == "FAIL"]
    bq_warnings = [r for r in bq_results if r["status"] == "WARN"]
    api_failures = [r for r in api_results if r["status"] == "FAIL"]
    credit_failures = [r for r in credit_results if r["status"] == "FAIL"]

    total_issues = len(bq_failures) + len(api_failures) + len(credit_failures)

    log.info(
        f"Health check complete: {len(bq_failures)} BQ failures, "
        f"{len(bq_warnings)} BQ warnings, {len(api_failures)} API failures, "
        f"{len(credit_failures)} credit failures"
    )

    return {
        "timestamp": now,
        "bq_results": bq_results,
        "api_results": api_results,
        "credit_results": credit_results,
        "bq_failures": bq_failures,
        "bq_warnings": bq_warnings,
        "api_failures": api_failures,
        "credit_failures": credit_failures,
        "total_issues": total_issues,
    }


def _build_alert_html(results):
    """Build HTML email body from health check results."""
    now = results["timestamp"]
    bq = results["bq_results"]
    apis = results["api_results"]
    bq_fail = results["bq_failures"]
    api_fail = results["api_failures"]

    credit_results = results.get("credit_results", [])
    credit_fail = results.get("credit_failures", [])

    # Styles
    style_ok = "color:#15803D;font-weight:600;"
    style_fail = "color:#DC2626;font-weight:600;"
    style_warn = "color:#D97706;font-weight:600;"
    style_skip = "color:#6B7280;"

    def status_badge(s):
        if s == "OK":
            return f'<span style="{style_ok}">✅ OK</span>'
        elif s == "FAIL":
            return f'<span style="{style_fail}">❌ FAIL</span>'
        elif s == "WARN":
            return f'<span style="{style_warn}">⚠️ WARN</span>'
        return f'<span style="{style_skip}">⏭ SKIP</span>'

    html = f"""
    <div style="font-family:Sora,Arial,sans-serif;max-width:700px;margin:0 auto;">
        <h2 style="color:#1a1a1a;">🏥 KLIQ Dashboard Health Report</h2>
        <p style="color:#666;font-size:13px;">{now}</p>
        <p style="font-size:14px;">
            <strong>{len(bq_fail)} BQ table failures</strong> · 
            <strong>{len(api_fail)} API failures</strong> · 
            <strong>{len(credit_fail)} credit/balance issues</strong> · 
            {len(bq)} tables checked · {len(apis)} APIs checked
        </p>
    """

    # Credits / Balance section
    if credit_results:
        html += '<h3 style="margin-top:24px;">💳 Credits & Balance</h3>'
        html += '<table style="width:100%;border-collapse:collapse;font-size:13px;">'
        html += '<tr style="background:#f2f3ee;"><th style="text-align:left;padding:6px;">Service</th><th style="padding:6px;">Status</th><th style="text-align:left;padding:6px;">Detail</th></tr>'
        for r in credit_results:
            html += f'<tr style="border-bottom:1px solid #eee;"><td style="padding:6px;">{r["name"]}</td><td style="padding:6px;text-align:center;">{status_badge(r["status"])}</td><td style="padding:6px;color:#666;">{r["detail"]}</td></tr>'
        html += "</table>"

    # API section
    html += '<h3 style="margin-top:24px;">🔌 External APIs</h3>'
    html += '<table style="width:100%;border-collapse:collapse;font-size:13px;">'
    html += '<tr style="background:#f2f3ee;"><th style="text-align:left;padding:6px;">Service</th><th style="padding:6px;">Status</th><th style="text-align:left;padding:6px;">Detail</th></tr>'
    for r in apis:
        html += f'<tr style="border-bottom:1px solid #eee;"><td style="padding:6px;">{r["name"]}</td><td style="padding:6px;text-align:center;">{status_badge(r["status"])}</td><td style="padding:6px;color:#666;">{r["detail"]}</td></tr>'
    html += "</table>"

    # BQ failures first
    if bq_fail:
        html += '<h3 style="margin-top:24px;color:#DC2626;">❌ Failed BQ Tables</h3>'
        html += '<table style="width:100%;border-collapse:collapse;font-size:13px;">'
        html += '<tr style="background:#FEE2E2;"><th style="text-align:left;padding:6px;">Table</th><th style="text-align:left;padding:6px;">Description</th><th style="text-align:left;padding:6px;">Error</th></tr>'
        for r in bq_fail:
            html += f'<tr style="border-bottom:1px solid #eee;"><td style="padding:6px;font-weight:600;">{r["name"]}</td><td style="padding:6px;color:#666;">{r["description"]}</td><td style="padding:6px;color:#DC2626;">{r["detail"][:150]}</td></tr>'
        html += "</table>"

    # Full BQ table list
    html += '<h3 style="margin-top:24px;">📊 All BQ Tables</h3>'
    html += '<table style="width:100%;border-collapse:collapse;font-size:12px;">'
    html += '<tr style="background:#f2f3ee;"><th style="text-align:left;padding:4px;">Table</th><th style="padding:4px;">Status</th><th style="text-align:right;padding:4px;">Rows</th><th style="text-align:left;padding:4px;">Description</th></tr>'
    for r in bq:
        html += f'<tr style="border-bottom:1px solid #eee;"><td style="padding:4px;">{r["name"]}</td><td style="padding:4px;text-align:center;">{status_badge(r["status"])}</td><td style="padding:4px;text-align:right;">{r.get("rows", 0):,}</td><td style="padding:4px;color:#888;">{r["description"]}</td></tr>'
    html += "</table>"

    html += '<p style="color:#999;font-size:11px;margin-top:24px;">Sent by KLIQ Health Monitor</p></div>'
    return html


def _monitor_loop():
    """Background loop: check every HEALTH_CHECK_HOURS hours."""
    # Wait 2 min after boot for app to stabilize
    time.sleep(120)
    log.info(f"Health monitor active — checking every {CHECK_INTERVAL_H}h")

    while True:
        try:
            results = run_health_check()

            if results["total_issues"] > 0:
                subject = (
                    f"⚠️ KLIQ Dashboard: {results['total_issues']} issue(s) detected"
                )
                html = _build_alert_html(results)
                _send_alert_email(subject, html)
            else:
                log.info("All checks passed — no alert email needed")

        except Exception as e:
            log.error(f"Health monitor error: {e}")
            # Try to send error notification
            try:
                _send_alert_email(
                    "🚨 KLIQ Health Monitor crashed",
                    f"<p>The health monitor itself encountered an error:</p><pre>{e}</pre>",
                )
            except Exception:
                pass

        time.sleep(CHECK_INTERVAL_H * 3600)


_thread = None


def start():
    """Start the health monitor background thread."""
    global _thread
    if _thread is not None and _thread.is_alive():
        log.info("Health monitor already running")
        return
    _thread = threading.Thread(target=_monitor_loop, daemon=True)
    _thread.start()
    log.info(
        f"Health monitor started (interval={CHECK_INTERVAL_H}h, alert={ALERT_EMAIL})"
    )


def run_once():
    """Run a single health check and send email if issues found. For manual testing."""
    results = run_health_check()
    subject = (
        f"⚠️ KLIQ Dashboard: {results['total_issues']} issue(s) detected"
        if results["total_issues"] > 0
        else "✅ KLIQ Dashboard: All checks passed"
    )
    html = _build_alert_html(results)
    _send_alert_email(subject, html)
    return results

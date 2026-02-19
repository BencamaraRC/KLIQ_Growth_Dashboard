"""
KLIQ Prospect Outreach — integrated into the Growth Dashboard.
Wraps the prospect-outreach admin_app functionality as a Streamlit page.
"""

import os
import sys
import json
import csv
import io
import streamlit as st
import pandas as pd
from datetime import datetime, timezone

# Add prospect-outreach to path so we can import its modules
_OUTREACH_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "prospect-outreach",
)
if _OUTREACH_DIR not in sys.path:
    sys.path.insert(0, _OUTREACH_DIR)

from config import DRY_RUN, CHEAT_SHEET_OUTPUT_DIR
from tracker import (
    get_all_prospects,
    get_prospect,
    upsert_prospect,
    get_sent_history,
    already_sent,
    record_sent,
    _get_db,
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

# ── Auth gate (reuse growth dashboard auth) ──
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth

require_auth()

# ── Page config ──
st.title("📧 Prospect Outreach")
mode_label = "🟢 LIVE" if not DRY_RUN else "🟡 DRY RUN"
st.caption(f"Mode: {mode_label}")

# ── Brand CSS ──
st.markdown(
    """
<style>
    .draft-card {
        background: #FFFAF1; border: 2px solid #1C3838; border-radius: 10px;
        padding: 18px 22px; margin-bottom: 14px; box-shadow: 3px 3px 0 #1C3838;
    }
    .draft-card h4 {margin: 0 0 4px 0; color: #1C3838;}
    .niche-badge {
        display: inline-block; background: #F9FFED; border: 1.5px solid #1C3838;
        border-radius: 20px; padding: 2px 12px; font-size: 0.82em; font-weight: 600;
        color: #1C3838; margin-right: 6px;
    }
    .action-chip {
        display: inline-block; background: #DEF8FE; border: 1px solid #1C3838;
        border-radius: 14px; padding: 1px 10px; font-size: 0.78em; color: #1C3838;
        margin: 2px 3px 2px 0;
    }
    .action-chip.pending {background: #F9DAD1;}
    .sent-badge {
        display: inline-block; background: #d4edda; border: 1px solid #155724;
        border-radius: 14px; padding: 2px 12px; font-size: 0.8em; color: #155724;
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)


def _enrich_prospect(p):
    """Merge profile_json into the prospect dict for rendering."""
    enriched = dict(p)
    if enriched.get("profile_json"):
        try:
            full = json.loads(enriched["profile_json"])
            enriched.update(full)
        except (json.JSONDecodeError, TypeError):
            pass
    return enriched


def _pick_email_template(prospect):
    """Decide which email template to use based on what's already been sent."""
    app_id = prospect["application_id"]
    for key in ["welcome", "cheat_sheet", "no_activity_7d"]:
        if not already_sent(app_id, key, "email"):
            return key
    return None


# ── Sub-page navigation ──
tab = st.radio(
    "Section",
    [
        "📧 Email Draft Queue",
        "📱 SMS Queue",
        "👥 Prospects",
        "📨 Sent Messages",
        "📥 Import Phones",
        "📄 Cheat Sheets",
        "🔄 Sync from BigQuery",
    ],
    horizontal=True,
)


# ═══════════════════════════════════════════════════════════════════
# 📧  EMAIL DRAFT QUEUE
# ═══════════════════════════════════════════════════════════════════
if tab == "📧 Email Draft Queue":
    hcol1, hcol2 = st.columns([6, 1])
    with hcol1:
        st.subheader("📧 Email Draft Queue")
        st.caption(
            "Review each email draft, then click **Send** to deliver it via Brevo."
        )
    with hcol2:
        if st.button("🔄 Refresh", key="refresh_email", use_container_width=True):
            st.rerun()

    prospects = get_all_prospects()
    sent = get_sent_history()

    total = len(prospects)
    with_email = sum(1 for p in prospects if p.get("email"))
    total_sent = len(sent)
    pending_count = 0
    for p in prospects:
        if p.get("email") and _pick_email_template(p) is not None:
            pending_count += 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Prospects", total)
    c2.metric("With Email", with_email)
    c3.metric("Drafts Pending", pending_count)
    c4.metric("Emails Sent", total_sent)

    st.divider()

    if not prospects:
        st.info("No prospects yet. Go to **Sync from BigQuery** to pull in sign-ups.")
        st.stop()

    fcol1, fcol2, fcol3 = st.columns([2, 2, 1])
    with fcol1:
        search = st.text_input("🔍 Search name or email", key="dq_search")
    with fcol2:
        all_niches = sorted(set(p.get("coach_type") or "Unknown" for p in prospects))
        niche_filter = st.multiselect(
            "Filter by niche", all_niches, default=all_niches, key="dq_niche"
        )
    with fcol3:
        show_sent = st.checkbox("Show already sent", value=False, key="dq_show_sent")

    filtered = []
    for p in prospects:
        if not p.get("email"):
            continue
        niche = p.get("coach_type") or "Unknown"
        if niche not in niche_filter:
            continue
        if search:
            q = search.lower()
            if (
                q not in (p.get("name") or "").lower()
                and q not in (p.get("email") or "").lower()
            ):
                continue
        tpl_key = _pick_email_template(p)
        if tpl_key is None and not show_sent:
            continue
        filtered.append((p, tpl_key))

    st.caption(f"Showing **{len(filtered)}** prospects")

    for idx, (p, tpl_key) in enumerate(filtered):
        enriched = _enrich_prospect(p)
        progress = get_task_progress(enriched)
        app_id = p["application_id"]
        name = p.get("name", "Unknown")
        email = p.get("email", "—")
        niche = p.get("coach_type") or "Unknown"

        actions_html = ""
        for step_label in progress["completed"]:
            actions_html += f'<span class="action-chip">{step_label}</span>'
        for step_label in progress["remaining"]:
            actions_html += f'<span class="action-chip pending">{step_label}</span>'

        all_sent = tpl_key is None

        with st.container():
            h1, h2 = st.columns([3, 2])
            with h1:
                st.markdown(
                    f'<div class="draft-card">'
                    f"<h4>{name}</h4>"
                    f'<span class="niche-badge">{niche}</span>'
                    f'<span style="color:#666; font-size:0.85em;">{email}</span>'
                    f'<div style="margin-top:8px;">{actions_html}</div>'
                    f'<div style="margin-top:6px; font-size:0.85em; color:#1C3838;">'
                    f'<b>{progress["done_count"]}/{progress["total"]}</b> steps done — '
                    f'{progress["progress_text"]}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with h2:
                if all_sent:
                    st.markdown(
                        '<div class="draft-card" style="text-align:center; padding-top:30px;">'
                        '<span class="sent-badge">All emails sent</span></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    try:
                        subject, html_body = render_email(tpl_key, enriched)
                    except Exception as e:
                        st.error(f"Template error: {e}")
                        continue

                    tpl_label = tpl_key.replace("_", " ").title()
                    st.markdown(
                        f'<div class="draft-card">'
                        f'<div style="font-size:0.8em; color:#888; margin-bottom:4px;">Template: <b>{tpl_label}</b></div>'
                        f'<div style="font-size:0.9em; color:#1C3838; margin-bottom:6px;"><b>Subject:</b> {subject}</div>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                    with st.expander("Preview email body", expanded=False):
                        st.components.v1.html(html_body, height=400, scrolling=True)

                    bcol1, bcol2 = st.columns([1, 1])
                    with bcol1:
                        attach_pdf = tpl_key == "cheat_sheet"
                        if attach_pdf:
                            st.caption("📎 Will attach cheat sheet PDF")

                    with bcol2:
                        if st.button(
                            f"🚀 Send",
                            key=f"send_{app_id}_{tpl_key}",
                            type="primary",
                            use_container_width=True,
                        ):
                            with st.spinner("Sending..."):
                                attachment_path = None
                                if attach_pdf:
                                    attachment_path = generate_cheat_sheet(enriched)

                                msg_id = send_email(
                                    to_email=email,
                                    subject=subject,
                                    html_body=html_body,
                                    attachment_path=attachment_path,
                                )
                                record_sent(app_id, tpl_key, "email", email, msg_id)

                            if msg_id:
                                st.success(f"Sent to {email}!")
                                st.rerun()
                            else:
                                st.error("Failed to send — check Brevo API key.")

            st.markdown("---")


# ═══════════════════════════════════════════════════════════════════
# �  SMS QUEUE
# ═══════════════════════════════════════════════════════════════════
elif tab == "📱 SMS Queue":
    hcol1, hcol2 = st.columns([6, 1])
    with hcol1:
        st.subheader("📱 SMS Queue")
        st.caption(
            "Send SMS via **KLIQ** Alpha Sender ID. Rules: signed up **24h+ ago** (max 14 days), **not logged back in**. "
            "Phone numbers pulled live from BigQuery `prod_dataset.applications`."
        )
    with hcol2:
        if st.button("🔄 Refresh", key="refresh_sms", use_container_width=True):
            st.rerun()

    # Pull phone numbers directly from BigQuery (prod_dataset.applications)
    with st.spinner("Loading phone numbers from BigQuery..."):
        bq_phones = fetch_all_phones()

    # Filter to those signed up 24h+ ago but within 14 days
    now = datetime.now(timezone.utc)
    cutoff_14d = now - pd.Timedelta(days=14)
    cutoff_24h = now - pd.Timedelta(hours=24)

    def _sms_eligible(p):
        """Eligible if signed up 24h-14d ago."""
        sd = p.get("created_at")
        if not sd or sd in ("None", ""):
            return False
        try:
            dt = pd.to_datetime(sd, utc=True)
            return cutoff_14d <= dt <= cutoff_24h
        except Exception:
            return False

    time_eligible = [p for p in bq_phones if _sms_eligible(p)]

    # Check BigQuery: only include prospects who have NOT logged back in
    with_phone = []
    if time_eligible:
        with st.spinner(
            f"Checking {len(time_eligible)} prospects for return activity..."
        ):
            for p in time_eligible:
                if not has_returned_after_signup(p["application_id"]):
                    # Normalise field names for downstream compatibility
                    p["phone"] = p.get("phone_number", "")
                    p["name"] = p.get("application_name", "Coach")
                    p["signup_date"] = str(p.get("created_at", ""))
                    with_phone.append(p)

    total_sms_sent = len([h for h in get_sent_history() if h.get("channel") == "sms"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total w/ Phone (BQ)", len(bq_phones))
    c2.metric("Eligible (24h-14d)", len(time_eligible))
    c3.metric("SMS Ready", len(with_phone))
    c4.metric("SMS Sent", total_sms_sent)

    st.divider()

    if not with_phone:
        st.info(
            f"No eligible prospects right now. **{len(bq_phones)}** have phone numbers in BigQuery, "
            f"**{len(time_eligible)}** signed up 24h-14d ago, but none passed the 'not logged back in' check "
            "(or the time window is empty)."
        )
        st.stop()

    # Filters
    fcol1, fcol2, fcol3 = st.columns([2, 2, 1])
    with fcol1:
        sms_search = st.text_input("🔍 Search name or phone", key="sms_search")
    with fcol2:
        sms_tpl = st.selectbox(
            "SMS Template", list(SMS_TEMPLATES.keys()), key="sms_tpl"
        )
    with fcol3:
        sms_show_sent = st.checkbox(
            "Show already sent", value=False, key="sms_show_sent"
        )

    # Filter
    sms_filtered = []
    for p in with_phone:
        if sms_search:
            q = sms_search.lower()
            if q not in (p.get("name") or "").lower() and q not in (
                p.get("phone") or ""
            ):
                continue
        if not sms_show_sent and already_sent(p["application_id"], sms_tpl, "sms"):
            continue
        sms_filtered.append(p)

    st.caption(f"Showing **{len(sms_filtered)}** prospects")

    # Bulk send option
    if sms_filtered:
        with st.expander("⚡ Bulk Send SMS", expanded=False):
            st.warning(
                f"This will send **{len(sms_filtered)}** SMS messages using the **{sms_tpl}** template."
            )
            if st.button("🚀 Send All SMS", key="bulk_sms", type="primary"):
                progress_bar = st.progress(0)
                sent_count = 0
                for i, p in enumerate(sms_filtered):
                    enriched = _enrich_prospect(p)
                    body = render_sms(sms_tpl, enriched)
                    msg_id = send_sms(p["phone"], body)
                    if msg_id:
                        record_sent(
                            p["application_id"], sms_tpl, "sms", p["phone"], msg_id
                        )
                        sent_count += 1
                    progress_bar.progress((i + 1) / len(sms_filtered))
                st.success(f"Sent {sent_count} SMS messages!")
                st.rerun()

    # Individual cards
    for p in sms_filtered:
        enriched = _enrich_prospect(p)
        app_id = p["application_id"]
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
        was_sent = already_sent(app_id, sms_tpl, "sms")

        # Preview the SMS
        try:
            sms_body = render_sms(sms_tpl, enriched)
        except Exception as e:
            sms_body = f"[Template error: {e}]"

        with st.container():
            h1, h2 = st.columns([3, 2])
            with h1:
                sent_html = '<span class="sent-badge">Sent</span>' if was_sent else ""
                st.markdown(
                    f'<div class="draft-card">'
                    f"<h4>{name} {sent_html}</h4>"
                    f'<span class="niche-badge">{niche}</span>'
                    f'<span style="color:#666; font-size:0.85em;">📱 {phone}</span><br>'
                    f'<span style="color:#666; font-size:0.8em;">📧 {email}</span><br>'
                    f'<span style="color:#999; font-size:0.75em;">Signed up: {signup} · App ID: {app_id}</span>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with h2:
                st.markdown(
                    f'<div class="draft-card">'
                    f'<div style="font-size:0.8em; color:#888; margin-bottom:4px;">Template: <b>{sms_tpl}</b></div>'
                    f'<div style="font-size:0.9em; color:#1C3838;">{sms_body}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if not was_sent:
                    if st.button(
                        f"📱 Send SMS",
                        key=f"sms_{app_id}_{sms_tpl}",
                        type="primary",
                        use_container_width=True,
                    ):
                        msg_id = send_sms(phone, sms_body)
                        if msg_id:
                            record_sent(app_id, sms_tpl, "sms", phone, msg_id)
                            st.success(f"SMS sent to {phone}!")
                            st.rerun()
                        else:
                            st.error("Failed to send SMS.")
            st.markdown("---")


# ═══════════════════════════════════════════════════════════════════
# �👥  PROSPECTS
# ═══════════════════════════════════════════════════════════════════
elif tab == "👥 Prospects":
    hcol1, hcol2 = st.columns([6, 1])
    with hcol1:
        st.subheader("👥 Prospect Management")
    with hcol2:
        if st.button("🔄 Refresh", key="refresh_prospects", use_container_width=True):
            st.rerun()

    prospects = get_all_prospects()
    if not prospects:
        st.info("No prospects yet. Sync from BigQuery first.")
    else:
        search = st.text_input("🔍 Search by name or email")
        if search:
            prospects = [
                p
                for p in prospects
                if search.lower() in (p.get("name") or "").lower()
                or search.lower() in (p.get("email") or "").lower()
            ]

        for p in prospects:
            with st.expander(
                f"**{p.get('name', 'Unknown')}** — {p.get('email', 'No email')} | {p.get('coach_type', '?')} | App ID: {p['application_id']}"
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Email:** {p.get('email', '—')}")
                    st.write(f"**Phone:** {p.get('phone', '—')}")
                    st.write(f"**Coach Type:** {p.get('coach_type', '—')}")
                with col2:
                    st.write(f"**Country:** {p.get('country', '—')}")
                    st.write(f"**Signed Up:** {p.get('signup_date', '—')}")

                new_phone = st.text_input(
                    "Update phone number",
                    value=p.get("phone") or "",
                    key=f"phone_{p['application_id']}",
                )
                if st.button("Save Phone", key=f"save_{p['application_id']}"):
                    upsert_prospect(p["application_id"], phone=new_phone)
                    st.success(f"Phone updated to {new_phone}")
                    st.rerun()

                history = get_sent_history(p["application_id"])
                if history:
                    st.write("**Message History:**")
                    for h in history:
                        st.write(
                            f"  - {h['sent_at']} — {h['channel'].upper()} — {h['sequence_step']} → {h['recipient']}"
                        )


# ═══════════════════════════════════════════════════════════════════
# 📨  SENT MESSAGES
# ═══════════════════════════════════════════════════════════════════
elif tab == "📨 Sent Messages":
    hcol1, hcol2 = st.columns([6, 1])
    with hcol1:
        st.subheader("📨 Sent Message History")
    with hcol2:
        if st.button("🔄 Refresh", key="refresh_sent", use_container_width=True):
            st.rerun()

    sent = get_sent_history()
    if not sent:
        st.info("No messages sent yet.")
    else:
        df = pd.DataFrame(sent)

        col1, col2 = st.columns(2)
        with col1:
            channel_filter = st.multiselect(
                "Channel",
                df["channel"].unique().tolist(),
                default=df["channel"].unique().tolist(),
            )
        with col2:
            step_filter = st.multiselect(
                "Sequence Step",
                df["sequence_step"].unique().tolist(),
                default=df["sequence_step"].unique().tolist(),
            )

        filtered = df[
            df["channel"].isin(channel_filter) & df["sequence_step"].isin(step_filter)
        ]
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(filtered)} of {len(df)} messages")


# ═══════════════════════════════════════════════════════════════════
# 📥  IMPORT PHONES
# ═══════════════════════════════════════════════════════════════════
elif tab == "📥 Import Phones":
    hcol1, hcol2 = st.columns([6, 1])
    with hcol1:
        st.subheader("📥 Import Phone Numbers")
    with hcol2:
        if st.button("🔄 Refresh", key="refresh_import", use_container_width=True):
            st.rerun()
    st.write(
        "Upload a CSV with columns: `application_id`, `phone` (or `email`, `phone` to match by email)"
    )

    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded:
        content = uploaded.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        st.write(f"Found **{len(rows)}** rows")
        st.dataframe(pd.DataFrame(rows).head(10))

        if st.button("Import Phone Numbers"):
            updated = 0
            for row in rows:
                phone = row.get("phone", "").strip()
                if not phone:
                    continue
                app_id = row.get("application_id", "").strip()
                email_val = row.get("email", "").strip()
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
            st.success(f"Updated {updated} phone numbers")
            st.rerun()

    st.divider()
    st.subheader("Manual Entry")
    with st.form("manual_phone"):
        app_id_input = st.number_input("Application ID", min_value=1, step=1)
        phone_input = st.text_input("Phone Number (with country code, e.g. +44...)")
        if st.form_submit_button("Save"):
            if phone_input:
                upsert_prospect(int(app_id_input), phone=phone_input)
                st.success(f"Phone {phone_input} saved for app_id={app_id_input}")


# ═══════════════════════════════════════════════════════════════════
# 📄  CHEAT SHEETS
# ═══════════════════════════════════════════════════════════════════
elif tab == "📄 Cheat Sheets":
    hcol1, hcol2 = st.columns([6, 1])
    with hcol1:
        st.subheader("📄 Cheat Sheet Generator")
    with hcol2:
        if st.button("🔄 Refresh", key="refresh_cheat", use_container_width=True):
            st.rerun()

    prospects = get_all_prospects()
    if not prospects:
        st.info("No prospects yet. Sync from BigQuery first.")
    else:
        names = {
            f"{p.get('name', 'Unknown')} (ID: {p['application_id']})": p
            for p in prospects
        }
        selected = st.selectbox("Select Prospect", list(names.keys()))
        prospect = names[selected]

        st.write(
            f"**Name:** {prospect.get('name')}  |  **Niche:** {prospect.get('coach_type', 'Fitness')}  |  **Email:** {prospect.get('email')}"
        )

        if st.button("Generate Cheat Sheet PDF", type="primary"):
            enriched = _enrich_prospect(prospect)
            pdf_path = generate_cheat_sheet(enriched)
            st.success("PDF generated!")

            with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇️ Download PDF",
                    data=f.read(),
                    file_name=f"cheatsheet_{prospect.get('name', 'coach').replace(' ', '_')}.pdf",
                    mime="application/pdf",
                )

    st.divider()
    st.subheader("Generated PDFs")
    if os.path.exists(CHEAT_SHEET_OUTPUT_DIR):
        pdfs = [f for f in os.listdir(CHEAT_SHEET_OUTPUT_DIR) if f.endswith(".pdf")]
        if pdfs:
            for pdf in sorted(pdfs, reverse=True):
                path = os.path.join(CHEAT_SHEET_OUTPUT_DIR, pdf)
                size_kb = os.path.getsize(path) / 1024
                st.write(f"📄 **{pdf}** ({size_kb:.1f} KB)")
        else:
            st.info("No PDFs generated yet.")


# ═══════════════════════════════════════════════════════════════════
# 🔄  SYNC FROM BIGQUERY
# ═══════════════════════════════════════════════════════════════════
elif tab == "🔄 Sync from BigQuery":
    hcol1, hcol2 = st.columns([6, 1])
    with hcol1:
        st.subheader("🔄 Sync Prospects from BigQuery")
    with hcol2:
        if st.button("🔄 Refresh", key="refresh_sync", use_container_width=True):
            st.rerun()

    sync_col1, sync_col2 = st.columns(2)

    with sync_col1:
        st.markdown("### 📥 Sync New Sign-ups")
        hours = st.slider(
            "Look back (hours)",
            1,
            720,
            168,
            step=24,
            help="How far back to look for new sign-ups",
        )

        if st.button("🔄 Sync Sign-ups", type="primary"):
            with st.spinner("Fetching from BigQuery..."):
                signups = fetch_new_signups(since_hours=hours)

            st.write(f"Found **{len(signups)}** sign-ups in the last {hours} hours")

            synced = 0
            progress_bar = st.progress(0)
            for i, s in enumerate(signups):
                app_id = s["application_id"]
                with st.spinner(f"Building profile for {s.get('name', 'Unknown')}..."):
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
                progress_bar.progress((i + 1) / len(signups))

            st.success(f"Synced {synced} prospects!")

    with sync_col2:
        st.markdown("### 📱 Sync Phone Numbers")
        st.caption(
            "Pull phone numbers from BigQuery `prod_dataset.applications` and attach to existing prospects."
        )

        if st.button("📱 Sync Phones from BigQuery", type="primary"):
            with st.spinner("Fetching phone numbers from BigQuery..."):
                phone_records = fetch_all_phones()

            st.write(f"Found **{len(phone_records)}** prospects with phone numbers")

            updated = 0
            for rec in phone_records:
                app_id = rec.get("application_id")
                phone = rec.get("phone_number")
                if not phone:
                    continue

                if app_id:
                    # Direct match by application_id
                    upsert_prospect(int(app_id), phone=phone)
                    updated += 1
                else:
                    # Try matching by email
                    email_val = rec.get("email", "")
                    if email_val:
                        all_p = get_all_prospects()
                        for ap in all_p:
                            if (ap.get("email") or "").lower() == email_val.lower():
                                upsert_prospect(ap["application_id"], phone=phone)
                                updated += 1
                                break

            st.success(f"Updated {updated} phone numbers!")
            st.rerun()

    st.divider()

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
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        with_phone = sum(1 for p in prospects if p.get("phone"))
        st.caption(
            f"**{len(prospects)}** total prospects, **{with_phone}** with phone numbers"
        )

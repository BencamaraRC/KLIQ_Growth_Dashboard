# KLIQ Product Roadmap 2026
## The Complete Platform Evolution: From Coach Tool to Creator Business Engine

---

# EXECUTIVE SUMMARY

KLIQ is an all-in-one platform for coaches and creators to build, manage, and grow their business. The platform currently offers: web storefront, branded mobile apps, live streaming, e-courses, subscriptions, 1:1 coaching, community feed, digital downloads, and premium content.

**The problem:** Despite strong product-market fit with top coaches, the platform suffers from:
- **91.2% coach churn** at 90 days (only 182 of 2,064 retained)
- **98.5% of coach apps** have zero revenue (1,346 of 1,367)
- **73.3% of coaches** never take a single meaningful action after signup
- **74.5% drop-off** between completing onboarding and creating first content

**The opportunity:** Coaches who DO activate are incredibly successful:
- Top 12 coaches generate **$615K+ GMV** with **$7,340 monthly recurring revenue**
- Blog engagement in Week 1 = **50.8% retention** (vs 7.5% without)
- Coaches active 3+ days in Week 1 = **50.9% retention** (vs 7.7%)
- Fitness is the **#1 earning category** in the creator economy (avg $11,939/month)

**This roadmap transforms KLIQ from a "tool coaches sign up for" into a "business engine coaches can't leave."**

---

# THE ROADMAP AT A GLANCE

```
Q1 2026 (NOW)          Q2 2026               Q3 2026               Q4 2026
─────────────          ───────               ───────               ───────
ACTIVATE               ENGAGE                MONETISE              SCALE
─────────────          ───────               ───────               ───────
AI Blog Writer         Notification Engine   Affiliate Marketplace Creator Fund
5-Min Storefront       User Onboarding       Brand Deal Portal     Content Marketplace
Mobile→Desktop         Live Session Boost    Content Licensing     Cross-Promotion
Activation Scorecard   Referral System       Managed PPC Service   Predictive AI
Anti-Bot + Verify      Coach Analytics       250 Club              White-Label
```

---

# PHASE 1: ACTIVATE (Q1 2026) — Fix the First Hour

**Goal:** Increase coach 90-day retention from 8.8% to 20%

**Data driving this phase:**
- 73.3% never take action → Need guided first experience
- 74.5% cliff after onboarding → Need to eliminate blank dashboard
- Blog engagement = +43pp retention → Need AI to create blogs automatically
- Mobile retention is 3.3x worse than desktop → Need device bridge
- Significant bot signups → Need verification

## 1.1 — "Store in 5 Minutes" Web Storefront Fast Track

**Priority: CRITICAL | Effort: Medium | Impact: Very High**

| Step | Time | What Happens |
|------|------|-------------|
| 1 | 30 sec | Sign up (name, email, password) + email verification |
| 2 | 30 sec | Choose template (Fitness / Wellness / Business / Creator) |
| 3 | 30 sec | Upload photo or pull from connected social account |
| 4 | 60 sec | AI generates store name, bio, and 3 blog posts from social content |
| 5 | 30 sec | Set subscription price (with benchmark: "Coaches in your niche charge £X-Y") |
| 6 | 30 sec | Store is LIVE — show URL + preview |
| 7 | 60 sec | Share on social media (pre-written post + QR code) |

**Technical requirements:**
- Template engine with 4 pre-designed themes
- Social OAuth (Instagram, TikTok, YouTube) for content import
- OpenAI/Claude API integration for bio + blog generation
- Instant subdomain provisioning (coachname.joinkliq.io)
- Social share deep links (Instagram Stories, WhatsApp, Twitter)

**Success metric:** 50% of new coaches have a live store within 10 minutes of signup (currently ~1%)

## 1.2 — AI Blog Writer from Social Content

**Priority: CRITICAL | Effort: Medium | Impact: Very High**

Blog engagement is the #1 retention driver for both coaches (+43pp) and users (+23pp). Most coaches never write a blog. They already have content on social media.

**The flow:**
```
Coach connects Instagram/TikTok/YouTube (OAuth)
    ↓
System pulls top 5 performing posts (by engagement)
    ↓
AI generates 3 blog drafts (300-500 words each)
    ↓
Coach reviews → edits or approves in 1 tap
    ↓
Blog published to store → Users get notified
    ↓
Ongoing: New social post detected → AI draft ready (weekly)
```

**Technical requirements:**
- Social media API integrations (Instagram Graph API, TikTok API, YouTube Data API)
- LLM pipeline for content transformation (tone matching, structure, CTA insertion)
- Content queue with approval workflow
- Auto-tagging by category
- Recurring cron job for new social post detection

**Success metric:** 50% of coaches have 3+ published blogs in Week 1 (currently <5%)

## 1.3 — Mobile → Desktop Bridge

**Priority: HIGH | Effort: Low | Impact: High**

47.4% sign up on mobile but mobile 90-day retention is 2.1% vs 7.0% desktop.

**Implementation:**
- Detect device on signup
- If mobile: show "Email me a link to continue on desktop" button
- Generate magic link (JWT token, no re-login required)
- Email: "Continue building your store on your laptop → [Magic Link]"
- Desktop landing: picks up exactly where mobile left off
- Nudge sequence: +4h SMS/Push, +24h Email if no desktop open

**Mobile quick wins (for those who stay):**
- Upload profile photo (camera prompt)
- Record 30-sec voice intro for community
- Connect social accounts (feeds AI blog)

**Technical requirements:**
- Magic link generation + JWT session transfer
- Device detection middleware
- Cross-device session state persistence
- SMS integration (Twilio)

**Success metric:** 40% of mobile signups open on desktop within 24 hours

## 1.4 — Coach Activation Scorecard

**Priority: HIGH | Effort: Low | Impact: High**

Industry data: gamified checklists increase activation by 40%.

```
┌─────────────────────────────────────────────────┐
│  🚀 YOUR LAUNCH SCORECARD — Day [X] of 7       │
│                                                  │
│  ✅ Profile photo uploaded              [Done]   │
│  ✅ Socials connected                   [Done]   │
│  ✅ 3 blogs published (AI-generated)    [3/3]   │
│  ⬜ Store link shared on social          [0/1]   │
│  ⬜ First live session scheduled         [0/1]   │
│                                                  │
│  Progress: ████████░░ 60%                        │
│                                                  │
│  🏆 You're ahead of 72% of new coaches!         │
└─────────────────────────────────────────────────┘
```

**Nudge sequence for incomplete items:**

| Trigger | Timing | Channel | Message |
|---------|--------|---------|---------|
| Scorecard < 50% | Day 2 AM | Email | "You're 40% through! Complete 1 more item today →" |
| No blog published | Day 2 | Push | "Your AI blogs are ready! Publish in 1 tap →" |
| Store not shared | Day 3 | Push | "Your store is live but nobody knows! Share →" |
| No live session | Day 4 | Push | "Successful coaches go live in week 1 →" |
| 100% complete | On completion | Push + Email | "🎉 LAUNCH CHAMPION! You're in the top 8.8%!" |

**Technical requirements:**
- Scorecard component (web + mobile)
- Event tracking for each checklist item
- Automated nudge engine (Firebase + SendGrid)
- Progress persistence in user profile

## 1.5 — Anti-Bot & Email Verification

**Priority: HIGH | Effort: Low | Impact: Medium**

Significant bot activity detected: scrambled Gmail addresses from tablet devices.

**Implementation:**
- reCAPTCHA v3 on signup (invisible, no friction)
- Email verification before onboarding starts
- Rate limit: max 3 signups per IP per hour
- Flag pattern: tablet + manual + dots-in-random-words@gmail.com
- Admin dashboard for flagged signups

**Success metric:** Reduce fake signups by 80%+

## 1.6 — Eliminate the Blank Dashboard

**Priority: HIGH | Effort: Low | Impact: High**

After onboarding, coaches face a blank dashboard with zeros everywhere.

**Solution:**
- Pre-populate with AI-generated content (from social import)
- Show "what success looks like" preview (top coach dashboard example)
- Replace zeros with progress bars ("0/3 blogs published → Get started")
- "Next step" always visible — never leave coach wondering what to do
- Sample community post from KLIQ team welcoming the coach

---

# PHASE 2: ENGAGE (Q2 2026) — Keep Them Coming Back

**Goal:** Increase user 30-day retention from ~47% to 60%, coach weekly active rate to 50%

## 2.1 — Notification Engine (Push + Email + In-App)

**Priority: CRITICAL | Effort: High | Impact: Very High**

### User Lifecycle Notifications

| Trigger | Timing | Channel | Message |
|---------|--------|---------|---------|
| User signs up | Immediately | Push + Email | "Welcome! [Coach] wrote a guide to get you started → [Blog]" |
| User signs up | +2 hours | Push | "Check out [Coach]'s most popular post →" |
| User hasn't returned | Day 2 | Push + Email | "[Coach] posted something new — don't miss it →" |
| User hasn't watched video | Day 2 | Push | "[Coach] has a new video for you →" |
| User opened but didn't engage | Day 3 | Push | "LIVE tomorrow! [Coach] is going live at [Time] →" |
| User opened <3 days | Day 5 | Push + Email | "You're almost there! Open today →" |
| User opened 3+ days | Day 7 | Push | "Great first week! Here's what's coming next →" |

### Coach Lifecycle Notifications

| Trigger | Timing | Channel | Message |
|---------|--------|---------|---------|
| New subscriber | Immediately | Push + Email | "🎉 You got a new subscriber! [Name] just joined" |
| First revenue | Immediately | Push + Email + In-App | "💰 Your first sale! [Amount] from [Name]" |
| Content milestone | On event | Push | "📊 Your blog '[Title]' has been read 50 times!" |
| Inactivity 3 days | Day 3 | Email | "Your subscribers are waiting! Post something today →" |
| Weekly scorecard | Monday AM | Email | "Last week: [X] new subs, [Y] views, £[Z] revenue" |

**Technical requirements:**
- Firebase Cloud Messaging (FCM) for push
- SendGrid or Customer.io for email
- In-app message framework
- Event-driven trigger system
- Frequency capping: max 2 push/day, 3 email/week
- A/B testing framework for copy + timing

## 2.2 — Live Session Enhancement

**Priority: HIGH | Effort: Medium | Impact: High**

Live session creation = +28pp retention lift. Currently only 8.5% of coaches create one.

**New features:**
- **One-tap scheduling** — "Go live in 5 minutes" button on dashboard
- **RSVP system** — Users tap to RSVP, get reminders at -24h, -1h, -5min
- **Replay auto-publish** — Live sessions automatically become on-demand content
- **Live session templates** — "Q&A", "Workout", "Masterclass" pre-configured formats
- **Audience size indicator** — Show coach how many RSVPs before going live
- **Co-host feature** — Invite another KLIQ coach for joint sessions

## 2.3 — Referral System

**Priority: HIGH | Effort: Medium | Impact: High**

**Coach referral:** "Invite a coach, both get 1 month free hosting"
**User referral:** "Invite a friend, both get 1 month free subscription"

**Implementation:**
- Unique referral codes per coach and per user
- Shareable referral links with tracking
- Referral dashboard showing invites sent, accepted, converted
- Automated reward fulfilment (credit to account)
- Leaderboard: "Top referrers this month"

## 2.4 — Coach Analytics Dashboard

**Priority: HIGH | Effort: Medium | Impact: High**

Coaches currently have limited visibility into their business performance.

**Dashboard includes:**
- **Revenue:** MRR, total GMV, revenue trend (chart), avg subscription price
- **Subscribers:** Total, new this month, churn rate, growth trend
- **Content:** Blog views, video watches, live session attendance
- **Engagement:** DAU, WAU, MAU, avg session duration
- **Funnel:** Store visitors → signups → paid subscribers (conversion rates)
- **Benchmarks:** "You're in the top X% of KLIQ coaches for [metric]"

## 2.5 — User Onboarding Form + Personalisation

**Priority: MEDIUM | Effort: Medium | Impact: Medium**

30-second form after user signup:
1. "What's your main goal?" (Lose weight / Build muscle / Improve flexibility / General wellness)
2. "How often do you work out?" (Never / 1-2x/week / 3-4x/week / 5+/week)
3. "What content do you prefer?" (Videos / Written guides / Live sessions / Community)

**Result:** Personalised home screen showing content matching their preferences. Users who get personalised content retain 15-20% better (industry benchmark).

---

# PHASE 3: MONETISE (Q3 2026) — Diversify Coach Revenue

**Goal:** Get 50 coaches to 250+ subscribers, launch 3 new revenue streams

## 3.1 — KLIQ Ads Manager (Managed PPC)

**Priority: HIGH | Effort: High | Impact: Very High**

KLIQ runs Meta/TikTok ads on behalf of coaches to grow their subscriber base.

**Pricing:** £49/month base + £5 per new subscriber acquired

**Features:**
- Ad creative builder using coach's existing content
- Audience targeting (fitness/wellness, lookalikes, geo)
- Landing page = coach's KLIQ web storefront
- Monthly performance dashboard
- Budget controls (coach sets monthly max)
- A/B testing of ad creative and audiences

**Technical requirements:**
- Meta Marketing API integration
- TikTok Ads API integration
- Ad creative template engine
- Conversion tracking pixel on KLIQ storefronts
- Billing system for PPC fees
- Reporting dashboard

## 3.2 — Affiliate Marketplace

**Priority: HIGH | Effort: High | Impact: High**

Curated marketplace of affiliate products for fitness/wellness coaches.

**How it works:**
- KLIQ partners with brands (MyProtein, Gymshark, Huel, etc.)
- Coaches browse marketplace and select products relevant to their audience
- KLIQ auto-inserts contextual affiliate links into blogs, modules, community posts
- Users click → buy → Coach earns commission
- KLIQ takes 10-20% platform fee on commissions

**Features:**
- Brand catalogue with commission rates
- One-click product selection for coaches
- Auto-insertion engine for contextual placement
- Earnings dashboard for coaches
- Brand analytics dashboard (impressions, clicks, conversions)

**Target categories:** Supplements, equipment, apparel, wearables, nutrition, wellness apps

## 3.3 — Brand Deal Portal

**Priority: MEDIUM | Effort: Medium | Impact: High**

KLIQ acts as talent agency connecting coaches (250+ subscribers) with brands.

**Deal types:**
- Sponsored blog posts (£200-500)
- Product integrations in modules/live sessions (£300-1,000)
- Ambassador deals (£500-2,000/month)
- Co-branded products (5-15% royalty)

**Features:**
- Brand brief submission portal
- Coach profile cards (audience size, niche, engagement rate)
- Deal negotiation workflow
- Content approval system
- Payment processing (KLIQ takes 15% agency fee)
- Campaign performance tracking

## 3.4 — Content Licensing Infrastructure

**Priority: MEDIUM | Effort: High | Impact: Medium**

Three licensing models:

**A) Coach-to-Coach:** Top coaches license programs to newer coaches (£50-200/month)
**B) Corporate Wellness:** Companies license content for employee programs (£500-5,000/month)
**C) Gym & Studio:** Gyms license on-demand content for members (£200-1,000/month)

**Features:**
- Content packaging tool (bundle modules into licensable programs)
- Licensing agreement templates
- DRM / access control for licensed content
- Revenue sharing automation
- B2B sales portal for corporate/gym clients

## 3.5 — The "250 Club"

**Priority: LOW | Effort: Low | Impact: Medium**

Milestone unlock at 250 subscribers:
- Premium coach badge on storefront
- Access to Affiliate Marketplace
- Access to Brand Deal Portal
- Priority support
- Featured in KLIQ's marketing

---

# PHASE 4: SCALE (Q4 2026) — Platform Flywheel

**Goal:** 100+ coaches using growth services, £300K+ new revenue for KLIQ

## 4.1 — KLIQ Creator Fund

Invest £1,000-5,000 in PPC for high-potential coaches in exchange for higher revenue share (25% of GMV for 12 months).

**Selection criteria:**
- Coach has 50+ subscribers (proven product-market fit)
- Growing month-over-month
- Active content creator (3+ posts/week)
- Niche with strong PPC economics

## 4.2 — Content Marketplace

Top coaches sell programs as white-label content:
- Other fitness businesses buy and rebrand
- Coach earns royalties (5-15% of sales)
- KLIQ handles distribution, payments, DRM

## 4.3 — Cross-Promotion Network

KLIQ coaches promote each other:
- "If you like CHAMPIONFIT, try REBARRE STRONG"
- Curated recommendations based on user preferences
- Referral fees for cross-promoted signups
- Joint live sessions between coaches

## 4.4 — Predictive AI

Use all our data to predict and prevent churn:
- **Coach churn prediction:** First-week behaviour → 90-day survival probability
- **User churn prediction:** Engagement patterns → 30-day retention probability
- **Smart notifications:** AI optimises send time, channel, and content per user
- **Revenue forecasting:** Predict coach GMV trajectory, identify at-risk revenue

## 4.5 — KLIQ Pro (Premium Tier)

New premium tier for coaches earning £1K+/month MRR:
- Custom domain (mycoachname.com)
- Advanced analytics + benchmarking
- Priority app store review
- Dedicated account manager
- White-glove PPC management
- Premium brand deal access

---

# TECHNICAL ARCHITECTURE REQUIREMENTS

## New Infrastructure Needed

| Component | Technology | Purpose | Phase |
|-----------|-----------|---------|-------|
| **AI Pipeline** | OpenAI/Claude API | Blog generation, bio writing, content suggestions | Q1 |
| **Social APIs** | Instagram Graph, TikTok, YouTube | Content import for AI blog writer | Q1 |
| **Push Notifications** | Firebase Cloud Messaging | User + coach lifecycle notifications | Q1 |
| **Email Engine** | Customer.io or SendGrid | Automated sequences, scorecards, win-back | Q1 |
| **Magic Links** | JWT + custom auth | Cross-device session transfer | Q1 |
| **reCAPTCHA** | Google reCAPTCHA v3 | Anti-bot protection | Q1 |
| **Analytics Dashboard** | React + BigQuery | Coach-facing business analytics | Q2 |
| **Referral System** | Custom + Stripe | Referral tracking + reward fulfilment | Q2 |
| **Ad Platform APIs** | Meta Marketing API, TikTok Ads | Managed PPC service | Q3 |
| **Affiliate Tracking** | Custom + partner APIs | Commission tracking + auto-insertion | Q3 |
| **Brand Portal** | Custom CMS | Deal management + content approval | Q3 |
| **Licensing DRM** | Custom | Content access control for licensed programs | Q3 |
| **ML Pipeline** | BigQuery ML / Python | Churn prediction, smart notifications | Q4 |

## Data Infrastructure

All analytics already flow through BigQuery (`rcwl-data.prod_dataset.events`). New tables needed:

| Table | Purpose | Phase |
|-------|---------|-------|
| `coach_scorecard_state` | Track activation checklist progress | Q1 |
| `ai_blog_queue` | AI-generated blog drafts awaiting approval | Q1 |
| `notification_log` | All notifications sent, delivered, opened, acted on | Q1 |
| `referral_tracking` | Referral codes, invites, conversions | Q2 |
| `affiliate_clicks` | Affiliate link impressions, clicks, conversions | Q3 |
| `brand_deals` | Deal pipeline, status, payments | Q3 |
| `content_licenses` | Licensed content, access rights, revenue | Q3 |
| `churn_predictions` | ML model outputs for coach + user churn risk | Q4 |

---

# ENGINEERING TEAM REQUIREMENTS

## Recommended Team Structure

| Role | Count | Focus | Phase |
|------|-------|-------|-------|
| **Full-Stack Engineer** | 2 | Storefront fast track, scorecard, dashboard | Q1-Q2 |
| **Backend Engineer** | 1 | Notification engine, referral system, APIs | Q1-Q2 |
| **AI/ML Engineer** | 1 | Blog writer, content pipeline, churn prediction | Q1-Q4 |
| **Mobile Engineer** | 1 | Push notifications, scorecard, magic links | Q1-Q2 |
| **Growth/PPC Specialist** | 1 | Managed PPC service, ad creative | Q3 |
| **Partnerships Manager** | 1 | Affiliate brands, brand deals, licensing | Q3-Q4 |
| **Product Designer** | 1 | UX for all new features | Q1-Q4 |

**Minimum viable team:** 3 engineers + 1 designer for Q1-Q2, expanding to 5+ for Q3-Q4.

---

# REVENUE IMPACT PROJECTION

## New Revenue Streams

| Stream | Q1 | Q2 | Q3 | Q4 | Year Total |
|--------|-----|-----|-----|-----|-----------|
| **Increased hosting** (more active coaches) | £5K | £10K | £15K | £20K | £50K |
| **Increased app fees** (more GMV) | £5K | £10K | £15K | £20K | £50K |
| **Managed PPC fees** | — | — | £8K | £22K | £30K |
| **Affiliate commissions** | — | — | £2K | £4K | £6K |
| **Brand deal agency fees** | — | — | £4K | £11K | £15K |
| **Content licensing** | — | — | — | £10K | £10K |
| **Creator Fund returns** | — | — | — | £5K | £5K |
| **TOTAL NEW REVENUE** | **£10K** | **£20K** | **£44K** | **£92K** | **£166K** |

## Key Assumptions
- Coach 90-day retention improves from 8.8% to 20% by Q2
- 50 coaches using PPC by Q4
- 25 affiliate brands onboarded by Q3
- 10 brand deals closed by Q4
- Average coach MRR grows from £432 to £800

---

# SUCCESS METRICS DASHBOARD

## Coach Metrics

| Metric | Current | Q1 Target | Q2 Target | Q3 Target | Q4 Target |
|--------|---------|-----------|-----------|-----------|-----------|
| 90-day retention | 8.8% | 15% | 20% | 22% | 25% |
| Complete activation (5 steps) | ~1% | 30% | 45% | 50% | 55% |
| Create content in Week 1 | <5% | 40% | 55% | 60% | 65% |
| Share store URL in Day 1 | 0.3% | 15% | 25% | 30% | 35% |
| Coaches with revenue | 21 | 35 | 50 | 75 | 100 |
| Coaches at 250+ subs | 21 | 25 | 30 | 40 | 50 |
| Average coach MRR (top 25) | £432 | £500 | £600 | £750 | £1,000 |

## User Metrics

| Metric | Current | Q1 Target | Q2 Target | Q3 Target | Q4 Target |
|--------|---------|-----------|-----------|-----------|-----------|
| First-week 3+ day activation | ~40% | 45% | 55% | 60% | 65% |
| 30-day retention | ~47% | 50% | 55% | 58% | 60% |
| Blog read rate (Week 1) | ~15% | 25% | 40% | 50% | 55% |
| Live session attendance | ~5% | 8% | 15% | 20% | 25% |
| Free → paid conversion | Unknown | 5% | 8% | 10% | 12% |

## Platform Metrics

| Metric | Current | Q1 Target | Q2 Target | Q3 Target | Q4 Target |
|--------|---------|-----------|-----------|-----------|-----------|
| Monthly coach signups (real) | ~60 | 80 | 100 | 120 | 150 |
| Platform total GMV/month | ~£12K | £15K | £20K | £30K | £50K |
| KLIQ new service revenue/month | £0 | £3K | £7K | £11K | £23K |
| Affiliate brands onboarded | 0 | 0 | 5 | 25 | 40 |
| Brand deals active | 0 | 0 | 0 | 5 | 15 |

---

# COMPETITIVE POSITIONING

## KLIQ vs Competitors

| Feature | KLIQ (Current) | KLIQ (Roadmap) | Kajabi | Teachable | Thinkific |
|---------|---------------|---------------|--------|-----------|-----------|
| **Branded mobile app** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Web storefront** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Live streaming** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Community feed** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **AI blog from social** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **5-min store launch** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Managed PPC** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Affiliate marketplace** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Brand deal portal** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Content licensing** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Creator Fund** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Gamified activation** | ❌ | ✅ | Partial | ❌ | ❌ |
| **Churn prediction AI** | ❌ | ✅ | ❌ | ❌ | ❌ |

**KLIQ's unique moat:** No other platform offers a branded mobile app + managed growth services + affiliate/brand deal marketplace. This combination makes KLIQ the only platform where a coach can go from zero to a full business with multiple revenue streams.

---

# RISK REGISTER

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| AI blog quality too low | Medium | High | Human review step, coach approval required, A/B test quality |
| PPC costs too high for ROI | Medium | Medium | Start with proven niches (fitness), set minimum ARPU threshold |
| Brand partners slow to onboard | High | Medium | Start with affiliate networks (Awin, CJ) before direct deals |
| Engineering capacity insufficient | Medium | High | Prioritise ruthlessly — Q1 features only, defer Q3/Q4 if needed |
| Coach adoption of new features low | Medium | Medium | In-app education, onboarding tours, success stories |
| Bot signups continue | Low | Low | reCAPTCHA + email verification solves 90%+ |

---

# KEY PRINCIPLES

1. **Activate before monetise.** No point building affiliate marketplace if coaches churn in 90 days. Q1 is ALL about retention.
2. **AI removes every blank field.** Bio, blog, store name, pricing — AI should suggest everything. Coach edits, not creates from scratch.
3. **Web first, app second.** Get coaches to a live URL in 5 minutes. The branded app is the upsell.
4. **Blog is the heartbeat.** Every notification, every nudge, every onboarding step should lead to blog content. It's the #1 driver.
5. **Celebrate obsessively.** First subscriber, first £100, first blog read — every milestone gets confetti and a push notification.
6. **Data drives everything.** Every feature decision is backed by BigQuery data. No gut feelings, no pet projects.
7. **Coaches who earn, stay.** The fastest path to retention is revenue. Get coaches to their first sale ASAP.
8. **KLIQ earns when coaches earn.** Every new service is aligned — KLIQ's revenue grows only when coach revenue grows.
9. **Don't boil the ocean.** Ship Q1 features first. Validate. Then build Q2. Waterfall planning, agile execution.
10. **The 250 threshold.** Everything in Stages 1-2 is designed to get coaches to 250 subscribers — the point where affiliates, brand deals, and licensing become viable.

# KLIQ Product Roadmap: Automated Retention & Engagement System

## Data Foundation
All recommendations below are backed by analysis of 156 KLIQ apps (82 successful, 74 unsuccessful).
Key findings driving this roadmap:
- **Blog = #1 retention driver** (+23pp lift in 30-day retention)
- **3+ active days in first week = 75% retention** (vs 45% for 1 day)
- **20+ live sessions in 90 days = 4x success rate**
- **£5K GMV = 95% survival rate**
- **8+ users in first 30 days = 2x success rate**

---

## PHASE 1: User Lifecycle Notification Engine (Priority: Critical)

### 1.1 — New User Onboarding Sequence (Days 1-7)

**Goal:** Get every new user to 3+ active days in their first week (75% retention threshold)

| Trigger | Timing | Channel | Message | Why |
|---------|--------|---------|---------|-----|
| User signs up | Immediately | Push + Email | "Welcome to [App Name]! 🎉 [Coach] has written a guide to get you started → [Latest Blog Post]" | Blog is #1 retention driver. Get them reading immediately. |
| User signs up | +2 hours | Push | "📖 Check out: '[Blog Title]' — [Coach]'s most popular post" | Second touch. Drive blog engagement on day 1. |
| User has NOT opened app | +24 hours (Day 2) | Push + Email | "👋 [Coach] posted something new — don't miss it → [Blog/Community Post]" | Day 2 is critical. Users who don't return by day 2 drop to 45% retention. |
| User has NOT watched a video | Day 2 | Push | "🎥 [Coach] has a new video for you: '[Video Title]'" | Video library = #2 retention driver (+11pp). |
| User opened app but didn't engage | Day 3 | Push | "🔴 LIVE tomorrow! [Coach] is going live at [Time] — tap to set a reminder" | Live sessions drive recurring engagement. |
| User has NOT opened app Day 3 | Day 3 | Email | "You're missing out! [Coach] has [X] new posts, [Y] videos, and a live session coming up → Open App" | Day 3 is the make-or-break. 3 days = 75% retention. |
| User opened 1-2 days only | Day 5 | Push + Email | "💪 You're almost there! Open [App Name] today and check out [Coach]'s latest program" | Push toward 3+ active days. |
| User opened 3+ days | Day 7 | Push | "🏆 Great first week! You've been active [X] days. Here's what's coming next week → [Upcoming Live Session]" | Positive reinforcement. Lock in the habit. |
| User opened <3 days | Day 7 | Email | "We miss you! [Coach] has been busy — [X] new blogs, [Y] new videos. Come see what you've missed" | Last chance to re-engage before week 1 ends. |

### 1.2 — Blog Engagement Automation

**Goal:** Every user reads at least 1 blog post in their first week

| Trigger | Timing | Channel | Message |
|---------|--------|---------|---------|
| Coach publishes new blog | Immediately | Push (all users) | "📝 New from [Coach]: '[Blog Title]' — Read now" |
| User hasn't read any blog | Day 2 | Push | "📖 [Coach]'s top post: '[Most Popular Blog Title]' — 2 min read" |
| User read 1 blog | Day 4 | Push | "You liked '[Previous Blog]'? Try this one → '[Related Blog Title]'" |
| User read 2+ blogs | Day 6 | Push | "🔥 You're on a streak! New post just dropped: '[Blog Title]'" |

### 1.3 — Live Session Engagement Automation

**Goal:** Every user attends or watches at least 1 live session in their first 30 days

| Trigger | Timing | Channel | Message |
|---------|--------|---------|---------|
| Coach schedules live session | Immediately | Push + Email | "🔴 [Coach] is going LIVE on [Date] at [Time]: '[Session Title]' — Tap to RSVP" |
| 24 hours before live session | -24h | Push | "⏰ Reminder: [Coach] goes live TOMORROW at [Time] — '[Session Title]'" |
| 1 hour before live session | -1h | Push | "🔴 Starting in 1 hour! [Coach] is going live: '[Session Title]' — Don't miss it" |
| Live session starts | Now | Push | "🔴 LIVE NOW: [Coach] is live! Tap to join → '[Session Title]'" |
| User missed live session | +2h after end | Push | "Missed [Coach]'s live session? Watch the replay now → '[Session Title]'" |
| User hasn't attended any session | Day 14 | Email | "You haven't joined a live session yet! [Coach] has [X] upcoming — here's the schedule" |

### 1.4 — First Purchase Nudge Sequence

**Goal:** Convert free users to paying subscribers (45% of successful apps get first revenue in week 1)

| Trigger | Timing | Channel | Message |
|---------|--------|---------|---------|
| User active 3+ days, no purchase | Day 5 | Push | "🌟 Unlock everything [Coach] has to offer — Start your subscription today" |
| User watched live session, no purchase | After session | Push | "Loved the session? Get unlimited access to all of [Coach]'s content → Subscribe" |
| User read 3+ blogs, no purchase | Day 7 | Email | "You've been loving [Coach]'s content! Unlock [X] programs, [Y] videos, and weekly live sessions → Subscribe" |
| User completed a program workout, no purchase | After workout | Push | "Great workout! 💪 Subscribe to unlock the full [Program Name] and [X] more programs" |
| User visited pricing page but didn't buy | +1h | Push | "Still thinking? Here's what you get: [Key benefits list] → Subscribe now" |
| User trial ending (if applicable) | -48h | Push + Email | "⏳ Your free access ends in 2 days. Subscribe now to keep your progress" |
| User trial ending | -24h | Push | "⏳ Last day of free access! Don't lose your [X] workouts and [Y] saved items" |

---

## PHASE 1B: User Onboarding Experience & Growth Loops (Priority: Critical)

### 1.5 — Onboarding Form → Personalised Content Routing

**Goal:** Every new user completes a 30-second onboarding form that routes them to the most relevant content — starting with blog (the #1 retention driver)

**The Flow:**

1. **User opens app for the first time** → Full-screen onboarding form appears
2. **3-4 quick questions:**
   - "What's your main goal?" (e.g., Lose weight / Build muscle / Improve flexibility / Mental wellness)
   - "How experienced are you?" (Beginner / Intermediate / Advanced)
   - "How often do you want to train?" (2-3x/week / 4-5x/week / Daily)
   - "What content do you prefer?" (Reading / Watching videos / Live sessions / Programs)
3. **Personalised landing screen** based on answers:
   - Shows a **curated blog post** matching their goal (always blog first — +23pp retention)
   - Recommends a **program** matching their level
   - Highlights the **next live session** they should attend
   - Shows a **video** relevant to their interest

**Why this works:**
- Removes the "blank screen" problem — new users immediately see relevant content
- Forces a blog read on day 1 (the single most impactful action for retention)
- Creates a personalised experience that feels curated, not generic
- Captures user preferences for future notification targeting

**Coach setup required:**
- Tag blog posts, programs, and videos with categories (goal, difficulty level)
- Write at least 1 blog post per goal category before launch
- The system auto-matches content to user answers

| Step | Screen | Action |
|------|--------|--------|
| 1 | Welcome | "Welcome to [App]! Let's personalise your experience — takes 30 seconds" |
| 2 | Goal question | Single select with icons |
| 3 | Experience question | Single select |
| 4 | Frequency question | Single select |
| 5 | Content preference | Multi-select |
| 6 | Personalised home | "Based on your goals, [Coach] recommends:" → Blog post + Program + Next live session |

### 1.6 — User Matching & Social Accountability ("Find Your 3")

**Goal:** Match every new user with 3 similar users in the app to create social accountability and community stickiness

**How it works:**

1. **After onboarding form completion**, the system identifies 3 users with similar:
   - Goals (same primary goal selected)
   - Experience level (same tier)
   - Activity level (similar frequency)
   - Join date (ideally within 2 weeks of each other)

2. **"Meet Your Accountability Squad" screen:**
   - Shows 3 matched users with their first name, profile photo, and goal
   - "You and [Name] both want to [Goal]. You're in this together!"
   - Option to follow/connect with each matched user

3. **Ongoing engagement features:**
   - **Weekly check-in:** "Your squad's week: [User A] completed 3 workouts, [User B] read 2 blogs, [User C] attended a live session — how about you?"
   - **Activity feed:** See what your matched users are doing (completed a workout, read a blog, attended a session)
   - **Streak comparison:** "You're on a 5-day streak! [User A] is on 3 days — keep your lead!"
   - **Favourite features visibility:** "Your squad's most-used features this week: Programs (2/3 used), Blog (3/3 read), Live Sessions (1/3 attended)"

4. **Engagement data shared with matched users:**
   - Total workouts completed
   - Blogs read this week
   - Live sessions attended
   - Current streak
   - Favourite feature (most-used)

**Why this works:**
- Social accountability is the #1 predictor of fitness habit formation
- Users who see others being active feel compelled to keep up
- Creates organic community without requiring the coach to manage it
- Matched users become each other's retention mechanism — if one drops off, the others notice
- Visibility of favourite features drives cross-feature discovery (a user who only does programs sees their match reading blogs → tries blogs)

### 1.7 — Referral Loop: "Invite a Friend, Both Get 1 Month Free"

**Goal:** Turn activated users into acquisition channels. Each successful referral brings in a pre-qualified user AND re-engages the referrer.

**The Mechanics:**

| Element | Detail |
|---------|--------|
| **Who can refer** | Users who have been active 3+ days in their first week (activated users only — quality control) |
| **Trigger** | After completing their "Find Your 3" match, or after first week | 
| **Incentive** | Both referrer AND friend get 1 month free subscription |
| **Limit** | Max 3 referrals per user (keeps it exclusive and prevents abuse) |
| **Referral method** | Unique shareable link + in-app "Invite" button |

**The Flow:**

1. **Unlock trigger:** User hits 3+ active days → "You've been crushing it! Want to bring a friend along?"
2. **Referral screen:** 
   - "Invite a friend to [App Name]. When they sign up, you BOTH get 1 month free."
   - Unique referral link + share buttons (WhatsApp, iMessage, Instagram DM, Copy Link)
   - Shows remaining invites: "You have 3 invites left"
3. **Friend signs up via link:**
   - Friend goes through onboarding form (Phase 1.5)
   - Friend is auto-matched with referrer as one of their "3" (Phase 1.6)
   - Both get 1 month free applied automatically
4. **Confirmation:**
   - Referrer: "[Friend Name] just joined! You both got 1 month free. You have 2 invites left."
   - Friend: "Welcome! [Referrer Name] invited you. You've both got 1 month free."

**Why this works:**
- **Pre-qualified users:** Referred users are 3-5x more likely to convert than organic signups (industry benchmark)
- **Social connection from day 1:** Friend already knows someone in the app → instant community
- **Re-engages the referrer:** The act of inviting reinforces their own commitment
- **Coach gets free acquisition:** No ad spend required. Users do the marketing.
- **Matched pair retention:** Referrer and friend are matched together → mutual accountability
- **Revenue positive:** 1 month free costs the coach ~£10-30, but a retained subscriber is worth £120-360/year

**Notification sequence for referral:**

| Trigger | Timing | Channel | Message |
|---------|--------|---------|---------|
| User hits 3+ active days | Day 3-5 | In-app + Push | "You've been on fire! Invite a friend — you both get 1 month free" |
| User hasn't referred after 7 days | Day 10 | Push | "Your 3 invites are waiting! Share [App] with a friend → both get 1 month free" |
| Friend signs up | Immediately | Push | "[Friend Name] just joined! You both got 1 month free. 2 invites left." |
| Friend completes first workout | Within 24h | Push | "[Friend Name] just completed their first workout! Send them a high-five" |
| User used all 3 referrals | On 3rd referral | Push + Email | "You've built your squad! All 3 friends are in. You're a [App Name] ambassador." |

**Growth loop visualised:**

```
User signs up → Onboarding form → Matched with 3 users → Gets activated (3+ days)
    ↓
Unlocks referral → Invites friend → Friend signs up → Friend matched with referrer
    ↓                                                        ↓
Both get 1 month free ← ← ← ← ← ← ← ← ← ← ← ← ← ← Friend gets activated
    ↓                                                        ↓
Referrer re-engaged ← ← ← ← ← ← ← ← ← ← ← ← ← ← Friend invites THEIR friend
```

**This creates a viral loop:** Each activated user can bring in 3 more, who each bring in 3 more. Even at a modest 20% referral rate, this compounds significantly.

### 1.8 — User Engagement Visibility ("My Stats")

**Goal:** Give users a personal dashboard showing their usage, favourite features, and progress — making engagement visible and gamified

**What users see:**

| Stat | Display |
|------|---------|
| **Current streak** | "7-day streak! Your longest: 12 days" |
| **This week's activity** | "4/7 days active" with visual progress bar |
| **Features used** | Icons showing Blog (3 read), Video (2 watched), Live (1 attended), Program (5 workouts) |
| **Favourite feature** | "Your most-used feature: Programs" with usage count |
| **Squad comparison** | "You're #1 in your squad this week!" |
| **Monthly summary** | "This month: 18 days active, 12 blogs read, 8 videos watched, 3 live sessions" |

**Why this works:**
- Makes invisible engagement visible — users see their own habits
- Streak mechanics create loss aversion ("don't break the streak")
- Feature visibility encourages trying new features ("I've never tried a live session — let me try one")
- Squad comparison adds friendly competition
- Gives coaches data on what their users actually do

---

## PHASE 2: Coach Action Nudge System (Priority: High)

### 2.1 — Coach Onboarding Checklist Notifications

**Goal:** Guide coaches through the cheatsheet milestones automatically

| Trigger | Timing | Channel | Message |
|---------|--------|---------|---------|
| Coach creates app | Immediately | Email + In-app | "🚀 Your launch checklist: 1) Create 10 modules 2) Write 5 blog posts 3) Publish 2 programs 4) Upload 5 videos — You're 0/4 complete" |
| Coach creates 5 modules | On action | Push | "✅ 5 modules done! Create 5 more to hit the success threshold (10+). Apps with 20+ modules have 88% success rate" |
| Coach writes first blog | On action | Push | "✅ First blog published! Write 4 more before launch. Blog is the #1 feature for keeping users (70% retention)" |
| Coach has 0 blogs after 3 days | Day 3 | Email | "⚠️ You haven't written a blog yet. Blog is your #1 retention tool — coaches with 20+ blogs have 82% success rate. Write your first one now →" |
| Coach has 0 live sessions after week 1 | Day 8 | Email | "⚠️ You haven't scheduled a live session yet. Successful apps run 4 in week 1. Schedule your first one →" |
| Coach hasn't posted in community for 3 days | Rolling | Push | "Your community is quiet! Post an update to keep users engaged. Successful coaches post 5x/week" |

### 2.2 — Weekly Coach Scorecard (Email)

**Goal:** Keep coaches accountable to the cheatsheet milestones

Send every **Monday morning** via email:

```
Subject: Your Weekly App Scorecard — Week [X] of Launch

Hi [Coach],

Here's how your app performed this week:

📊 THIS WEEK
- Users active: [X] (target: 8+)
- Blog posts published: [X] (target: 2+)
- Live sessions run: [X] (target: 2-3)
- Community posts: [X] (target: 5+)
- New subscribers: [X]
- Revenue: £[X]

📈 CUMULATIVE (since launch)
- Total users: [X] / 26 (tipping point)
- Total modules: [X] / 20 (88% success threshold)
- Total blogs: [X] / 20 (82% success threshold)
- Total live sessions: [X] / 20 (magic number)
- Total GMV: £[X] / £5,000 (safe zone)

🎯 THIS WEEK'S PRIORITY:
[Dynamic based on what's lagging — e.g., "Write 2 blog posts — you're at 3/20"]

💡 TIP: [Rotating data-backed tip, e.g., "Users who read a blog in their first week are 23% more likely to stay"]
```

### 2.3 — Milestone Celebration Notifications

| Milestone | Channel | Message |
|-----------|---------|---------|
| First subscriber | Push + Email | "🎉 You got your first subscriber! 45% of successful apps hit this in week 1 — you're on track!" |
| £100 GMV | Push + Email | "💰 £100 GMV! 64% of apps at this level survive long-term. Keep going!" |
| £500 GMV | Push + Email | "🚀 £500 GMV! 70% survival rate. You're building something real." |
| £1,000 GMV | Push + Email | "🏆 £1,000 GMV! 73% of apps at this level are still active. You're in the top tier." |
| £5,000 GMV | Push + Email | "🔥 £5,000 GMV! You're in the SAFE ZONE — 95% of apps at this level never churn. Incredible work!" |
| 20 modules | Push | "📚 20 modules published! Apps with 20+ modules have an 88% success rate — you're one of them." |
| 20 blogs | Push | "📝 20 blog posts! 82% success rate. Your content library is a retention machine." |
| 20 live sessions | Push | "🔴 20 live sessions! You're 4x more likely to succeed than coaches who don't hit this number." |
| 26 users | Push | "👥 26 users! This is the tipping point — 76% of apps with 26+ users succeed." |

---

## PHASE 2B: Coach Onboarding & Activation Overhaul (Priority: Critical)

**Data Foundation — The Coach Problem:**
- **2,064 coaches registered** → only **182 retained at 90 days (8.8%)**
- **50% of coaches (1,022) never trigger a single event** — they register and ghost
- **667 coaches (64% of active ones) are gone the same day** they sign up
- **Mobile signups retain at 2.1%** vs desktop at **7.0%** (3.3x gap)
- **Only 1% preview their app**, **0.3% copy their URL**, **0.5% upload a profile image**
- **Blog engagement in week 1 = 50.8% coach retention** vs 7.5% without (+43pp lift)
- **Creating a live session in week 1 = 36.4% retention** vs 8.4% without (+28pp lift)
- **Coaches active 3+ days in week 1 = 50.9% retention** vs 7.7% without (+43pp lift)

### 2B.1 — Mobile → Desktop Bridge (Priority: Immediate)

**Problem:** 46% of coaches sign up on mobile, but mobile 90-day retention is only 2.1% vs 7.0% on desktop. Coaches can't build a business on their phone — they need to create modules, upload content, write blogs, and manage programs. Mobile is a discovery channel, not a building channel.

**Two-pronged approach: Improve mobile AND push to desktop**

#### A) Mobile Signup → Desktop Nudge

| Step | What Happens | Why |
|------|-------------|-----|
| 1 | Coach signs up on mobile | They found KLIQ via social media ad or organic |
| 2 | After signup, show: "Your store is ready! For the best experience building your content, continue on desktop" | Set expectation that building = desktop |
| 3 | **"Email me a link to continue on desktop"** button | One-tap sends a magic link to their email |
| 4 | Magic link email: "Continue setting up [App Name] on your laptop → [Link]" | Seamless handoff, no re-login required |
| 5 | Desktop landing: picks up exactly where mobile left off | Zero friction, no repeated steps |

**Notification sequence for mobile signups:**

| Trigger | Timing | Channel | Message |
|---------|--------|---------|---------|
| Mobile signup completed | Immediately | Email | "Welcome to KLIQ! 🚀 Continue building your store on desktop for the best experience → [Magic Link]" |
| Coach hasn't opened desktop | +4 hours | SMS/Push | "Your store is waiting! Open on your laptop to start adding content → [Magic Link]" |
| Coach hasn't opened desktop | +24 hours | Email | "Quick tip: coaches who build on desktop are 3x more likely to launch successfully. Continue here → [Magic Link]" |
| Coach opens on desktop | On open | In-app | "Welcome back! Let's get your store live in the next 30 minutes →" |

#### B) Mobile-Optimised Quick Wins

For coaches who stay on mobile, give them **3 things they CAN do on mobile** to feel progress:

| Quick Win | Time | What It Does |
|-----------|------|-------------|
| **Upload profile photo** | 30 sec | Camera is right there on mobile — use it. "Add your photo so users know who you are" |
| **Record a voice note for community** | 60 sec | "Say hello to your future community — record a 30-second intro" |
| **Connect social accounts** | 60 sec | "Connect your Instagram/TikTok to import your bio and content" → feeds into AI blog (2B.2) |

### 2B.2 — AI Blog Writer from Social Content (Priority: Immediate)

**Problem:** Blog engagement is the #1 retention driver for both users (+23pp) AND coaches (+43pp), but most coaches never write one. They already have content on social media — let's use it.

**The Flow:**

```
Coach connects Instagram/TikTok/YouTube
    ↓
System pulls recent posts, captions, video transcripts
    ↓
AI generates 3 blog post drafts from their existing content
    ↓
Coach reviews, edits (or approves as-is) in 1 tap
    ↓
Blog published to their store → Users get notified
```

**Detailed Implementation:**

| Step | Screen | Action |
|------|--------|--------|
| 1 | Onboarding | "You already have great content! Let's turn it into blogs for your store" |
| 2 | Connect socials | "Connect Instagram, TikTok, or YouTube" — OAuth flow |
| 3 | AI processing | "Analysing your content..." (10-15 seconds) |
| 4 | Blog preview | Show 3 AI-generated blog drafts with titles, images pulled from posts |
| 5 | Edit/Approve | Coach can edit or tap "Publish" on each |
| 6 | Published | "3 blogs published! Your store now has content for users to discover" |
| 7 | Ongoing | "New Instagram post detected → AI draft ready for review" (weekly prompt) |

**AI Blog Generation Rules:**
- Pull the coach's **top 5 performing social posts** (by likes/comments)
- Convert short captions into **300-500 word blog posts** with structure (intro, body, takeaway)
- Use the coach's **voice and tone** from their existing content
- Auto-tag blogs with categories matching the onboarding form goals (Phase 1.5)
- Include a **CTA at the end**: "Want more? Subscribe to [App Name] for full access"

**Why this works:**
- Removes the #1 barrier: "I don't have time to write blogs"
- Coaches already have content — they just need it reformatted
- Blog is published in under 2 minutes vs 30+ minutes to write from scratch
- Immediately gives the store content for users to discover
- Creates a recurring content pipeline (new social post → new blog draft)

### 2B.3 — Guided First Hour: "Launch in 60 Minutes" (Priority: High)

**Problem:** 64% of active coaches leave on the same day. The first hour is everything. Currently, coaches complete onboarding and then face a blank dashboard with no clear next step.

**The "Launch in 60 Minutes" Flow:**

| Minute | Step | What Coach Does | System Helps With |
|--------|------|----------------|-------------------|
| 0-2 | **Sign up** | Create account | Self-serve flow (existing) |
| 2-5 | **Profile setup** | Upload photo, write bio | Mobile: camera prompt. AI: generate bio from social profile |
| 5-10 | **Connect socials** | Link Instagram/TikTok/YouTube | OAuth — one tap per platform |
| 10-15 | **AI generates blogs** | Review 3 AI-written blog drafts | Auto-generated from social content (2B.2) |
| 15-20 | **Publish blogs** | Approve/edit and publish | One-tap publish per blog |
| 20-25 | **Create first module** | Upload a video or write content | AI suggests: "Turn your most popular post into a module" |
| 25-30 | **Set up subscription** | Choose pricing tier | Show benchmarks: "Most coaches in [category] charge £X-Y/month" |
| 30-35 | **Preview store** | See their web storefront live | Auto-generated preview with their content, branding, photo |
| 35-40 | **Copy & share URL** | Share store link on social media | Pre-written social post: "I just launched my coaching store! Check it out → [URL]" |
| 40-50 | **Schedule first live session** | Pick a date/time for first live | "Most successful coaches go live within their first week" |
| 50-60 | **Invite first users** | Share with existing audience | Pre-written email/DM template + QR code for in-person |

**Progress bar visible throughout:** "Your store is 40% ready — 3 steps to go!"

**Key design principles:**
- **Never show a blank screen** — every step has pre-filled content or AI suggestions
- **Every step has a "Skip for now"** — but the system nudges them back later
- **Celebrate each completion** — confetti, checkmark, encouraging message
- **Show the store updating in real-time** — as they add content, the preview updates

### 2B.4 — Coach Activation Scorecard (First 7 Days)

**Problem:** Coaches don't know what "good" looks like. Show them exactly what successful coaches do in their first week.

**In-app scorecard (visible from Day 1):**

```
┌─────────────────────────────────────────────┐
│  YOUR LAUNCH SCORECARD — Day [X] of 7       │
│                                              │
│  ✅ Profile photo uploaded          [Done]   │
│  ✅ 3 blogs published (AI-generated) [3/3]  │
│  ⬜ First module created             [0/1]   │
│  ⬜ Subscription pricing set         [0/1]   │
│  ⬜ Store previewed                  [0/1]   │
│  ⬜ URL shared on social media       [0/1]   │
│  ⬜ First live session scheduled     [0/1]   │
│  ⬜ First user invited               [0/1]   │
│                                              │
│  Progress: ████░░░░░░ 25%                    │
│                                              │
│  🏆 Coaches who complete 6+ items in week 1  │
│     are 5x more likely to still be active    │
│     at 90 days                               │
└─────────────────────────────────────────────┘
```

**Nudge sequence for incomplete items:**

| Trigger | Timing | Channel | Message |
|---------|--------|---------|---------|
| Scorecard < 50% after Day 1 | Day 2 morning | Email | "You're 25% through your launch checklist! Complete 2 more items today → [Deeplink to next step]" |
| No module created by Day 3 | Day 3 | Push | "Your store needs content! Create your first module in 5 minutes → [Deeplink]" |
| Store not previewed by Day 4 | Day 4 | Push | "Have you seen your store yet? Preview it now — it looks great → [Preview link]" |
| URL not shared by Day 5 | Day 5 | Push + Email | "Your store is ready but nobody knows about it! Share your link → [Pre-written social post]" |
| No live session by Day 6 | Day 6 | Push | "Successful coaches go live in week 1. Schedule your first session → [Deeplink]" |
| Scorecard 100% | On completion | Push + Email | "🎉 LAUNCH COMPLETE! You've done everything successful coaches do in week 1. You're 5x more likely to succeed!" |

### 2B.5 — "Store in 5 Minutes" — Web Storefront Fast Track

**Problem:** The web storefront is the quickest product to build and launch. Most coaches don't need a full app on Day 1 — they need a live URL they can share NOW.

**The Pitch:** "Get your coaching store live in 5 minutes. No app needed. Share your link today."

**Fast Track Flow:**

| Step | Time | What Happens |
|------|------|-------------|
| 1 | 30 sec | Sign up (name, email, password) |
| 2 | 30 sec | Choose template (3 options: Fitness / Wellness / Business) |
| 3 | 30 sec | Upload profile photo (or pull from social) |
| 4 | 60 sec | AI generates store name, bio, and 3 blog posts from connected social |
| 5 | 30 sec | Set subscription price (with benchmark guidance) |
| 6 | 30 sec | **Store is LIVE** — show the URL, show the preview |
| 7 | 60 sec | Share URL on social media (pre-written post provided) |

**Total: Under 5 minutes to a live, content-filled web storefront.**

**Why web storefront first:**
- **Instant gratification** — coach sees a live URL in minutes, not weeks
- **No app store approval** — removes the biggest friction point
- **Shareable immediately** — coach can post their link on Instagram/TikTok today
- **Upgradeable** — "Love your store? Upgrade to your own branded app" (upsell path)
- **Lower commitment** — coaches who aren't sure can test with a free web store before committing to an app

**Upsell trigger:**

| Trigger | Timing | Message |
|---------|--------|---------|
| Store gets 10+ visitors | On milestone | "Your store is getting traffic! Upgrade to your own app for push notifications and a premium experience → [Upgrade]" |
| First subscriber | On event | "You just got your first subscriber! Your own branded app would give them push notifications and a better experience → [Upgrade]" |
| 30 days active | Day 30 | "You've been live for a month! Coaches with their own app earn 2x more. Ready to upgrade? → [Upgrade]" |

---

## PHASE 3: Smart Re-engagement System (Priority: High)

### 3.1 — Churning User Detection & Win-back

| Trigger | Timing | Channel | Message |
|---------|--------|---------|---------|
| User inactive 3 days (was active) | Day 3 of inactivity | Push | "👋 [Coach] posted something new! Check it out →" |
| User inactive 7 days | Day 7 | Push + Email | "We miss you! Here's what you've missed: [X] new posts, [Y] new videos from [Coach]" |
| User inactive 14 days | Day 14 | Email | "It's been 2 weeks! [Coach] has been busy — [summary of new content]. Come back and see →" |
| User inactive 30 days | Day 30 | Email | "Your [App Name] account misses you. [Coach] has added [X] new items since you left. Special offer: [if applicable]" |
| User cancelled subscription | Immediately | Email | "We're sorry to see you go. Your content is still here if you change your mind. Here's what's coming up: [Upcoming live sessions]" |
| User cancelled subscription | +7 days | Email | "Since you left, [Coach] has posted [X] new items. Want to come back? →" |

### 3.2 — Engagement Depth Nudges

**Goal:** Push users from casual (1-2 features) to deep engagement (3+ features = 50+ events/user)

| Trigger | Channel | Message |
|---------|---------|---------|
| User only reads blogs, never watched video | Push | "🎥 [Coach] has [X] videos you haven't seen yet. Try '[Video Title]' — 5 min watch" |
| User only watches videos, never read blog | Push | "📖 [Coach] wrote about [Topic] — quick 2 min read →" |
| User never joined community | Push | "💬 [X] people are talking in [Coach]'s community right now. Join the conversation →" |
| User never started a program | Push | "🏋️ Ready for a challenge? Start '[Program Name]' — [X] people have completed it" |
| User engaged with 3+ features | Push | "🔥 You're a power user! You've used [X] features this week. Keep it up!" |

---

## PHASE 4: Technical Implementation Roadmap

### Quarter 1: Foundation + Coach Activation (Weeks 1-12)

| Week | Deliverable | Details |
|------|-------------|---------|
| 1-2 | **Event tracking audit** | Ensure all key events are tracked: blog_read, video_watched, live_session_joined, program_started, subscription_created, app_opened (with daily unique flag). Add coach events: store_previewed, url_copied, social_connected, ai_blog_generated |
| 3-4 | **"Store in 5 Minutes" web storefront fast track** (Phase 2B.5) | Template selection, AI bio/blog generation, instant live URL. This is the #1 priority — get coaches to a live store in under 5 minutes |
| 5-6 | **Mobile → Desktop bridge** (Phase 2B.1) | Magic link email system, device detection, cross-device session continuity. Mobile quick wins (photo, voice note, social connect) |
| 7-8 | **AI Blog Writer from social content** (Phase 2B.2) | Social OAuth (Instagram, TikTok, YouTube), content pull, AI blog generation pipeline, one-tap publish |
| 9-10 | **Coach Activation Scorecard** (Phase 2B.4) | In-app progress tracker, nudge sequence for incomplete items, "Launch in 60 Minutes" guided flow (Phase 2B.3) |
| 11-12 | **Push + email infrastructure** | Firebase Cloud Messaging (FCM) for push. SendGrid/Customer.io for email. Segment coaches AND users by lifecycle state |

### Quarter 2: User Engagement + Coach Growth (Weeks 13-24)

| Week | Deliverable | Details |
|------|-------------|---------|
| 13-14 | **New user onboarding sequence** (Phase 1.1) | 7-day push + email sequence driving blog reads and 3+ active days |
| 15-16 | **Blog engagement automation** (Phase 1.2) | Auto-notify on publish, nudge non-readers, streak mechanics |
| 17-18 | **Live session notifications** (Phase 1.3) | RSVP, reminders (-24h, -1h), live now, replay nudges |
| 19-20 | **First purchase sequence** (Phase 1.4) | Deploy conversion nudges based on engagement signals |
| 21-22 | **Weekly coach scorecard** (Phase 2.2) + **Milestone celebrations** (Phase 2.3) | Automated Monday email + GMV/content/user milestone triggers |
| 23-24 | **Web storefront → App upsell triggers** (Phase 2B.5) | Auto-prompt upgrade at 10+ visitors, first subscriber, 30 days active |

### Quarter 3: Intelligence + Growth Loops (Weeks 25-36)

| Week | Deliverable | Details |
|------|-------------|---------|
| 25-26 | **User onboarding form + personalised routing** (Phase 1.5) | 30-second form, content matching, personalised home screen |
| 27-28 | **"Find Your 3" user matching** (Phase 1.6) | Social accountability matching, squad activity feed, streak comparison |
| 29-30 | **Referral loop** (Phase 1.7) + **"My Stats" dashboard** (Phase 1.8) | Invite-a-friend mechanics, engagement visibility, gamification |
| 31-32 | **Churning user/coach detection** (Phase 3.1) | Build inactivity triggers + win-back sequences for both users AND coaches |
| 33-34 | **AI recurring blog pipeline** | Auto-detect new social posts → generate draft → notify coach for approval. Weekly cadence |
| 35-36 | **Predictive churn model** | Use first-week behaviour to predict 30-day churn for both coaches and users. Smart send-time optimization. Frequency capping (max 2 push/day, 3 email/week) |

---

## Notification Channel Strategy

| Channel | Best For | Frequency Cap | Open Rate Benchmark |
|---------|----------|---------------|---------------------|
| **Push notification** | Urgent/time-sensitive (live sessions, new content) | Max 2/day | 5-15% |
| **Email** | Longer content (weekly scorecard, win-back, onboarding) | Max 3/week | 20-30% |
| **In-app message** | Contextual nudges (upgrade prompts, feature discovery) | On relevant screen | 40-60% |
| **SMS** (future) | Critical alerts (trial ending, live starting in 5 min) | Max 1/week | 45-50% |

### Priority Order for Implementation:
1. **Push notifications** — highest immediacy, drives app opens (the #1 metric)
2. **Email** — best for longer sequences, coach scorecards, win-back
3. **In-app messages** — best conversion rate, but user must already be in app
4. **SMS** — highest open rate but most intrusive, save for critical moments

---

## Success Metrics for This Roadmap

### User Metrics

| Metric | Current Baseline | Target (6 months) | Target (12 months) |
|--------|-----------------|-------------------|---------------------|
| First-week 3+ day activation | ~40% of users | 55% | 65% |
| 30-day retention (blog readers) | 70% | 75% | 80% |
| 30-day retention (non-blog readers) | 47% | 55% | 60% |
| Users attending 1+ live session (30d) | ~5% | 15% | 25% |
| Free → paid conversion (30d) | Unknown | 8% | 12% |

### Coach Metrics

| Metric | Current Baseline | Target (6 months) | Target (12 months) |
|--------|-----------------|-------------------|---------------------|
| Coach 90-day retention | **8.8%** (182/2,064) | 20% | 30% |
| Coaches who complete onboarding | 50% | 75% | 85% |
| Coaches who create a module (week 1) | 13% | 40% | 55% |
| Coaches who publish a blog (week 1) | <5% (estimated) | 50% (via AI blog) | 70% |
| Coaches who preview their store | **1%** | 60% | 80% |
| Coaches who share their URL | **0.3%** | 40% | 60% |
| Coaches who schedule a live session (week 1) | 8% | 25% | 40% |
| Mobile signup → desktop conversion | Unknown | 40% | 55% |
| Time to live store | Unknown (most never launch) | Under 5 minutes | Under 5 minutes |
| AI blogs generated per coach (week 1) | 0 | 3 | 5 |
| Web storefront → App upgrade rate | N/A | 10% | 20% |

### Platform Metrics

| Metric | Current Baseline | Target (6 months) | Target (12 months) |
|--------|-----------------|-------------------|---------------------|
| Coach weekly scorecard open rate | N/A | 50% | 60% |
| Apps hitting 20+ blogs in 90 days | ~30% | 45% | 60% |
| Apps hitting 20+ live sessions in 90 days | ~25% | 40% | 55% |
| Apps reaching £5K GMV (12 months) | ~15% | 25% | 35% |

---

## Key Principles

1. **Blog first, always.** Every notification sequence should lead with blog content. It's the #1 retention driver for both users (+23pp) AND coaches (+43pp).
2. **3 days in 7.** The entire first-week strategy is about getting users AND coaches to be active 3+ times. 50.9% coach retention when they hit this vs 7.7% without.
3. **Web storefront first, app second.** Get coaches to a live URL in 5 minutes. The app is an upsell, not the starting point.
4. **AI removes friction.** Coaches don't write blogs — AI writes them from social content. Coaches don't write bios — AI generates them. Every blank field should have an AI-generated suggestion.
5. **Mobile discovers, desktop builds.** Mobile signups retain at 2.1% vs 7.0% on desktop. Bridge them to desktop seamlessly with magic links.
6. **Never show a blank screen.** Every step in the coach journey should have pre-filled content, AI suggestions, or clear next actions.
7. **Celebrate milestones.** Positive reinforcement at £100, £500, £1K, £5K keeps coaches motivated through the hard middle months.
8. **Don't spam.** Frequency caps are non-negotiable. A user who mutes notifications is worse than one who gets fewer.
9. **Measure everything.** Every notification should be tracked: sent, delivered, opened, action taken. A/B test copy and timing continuously.

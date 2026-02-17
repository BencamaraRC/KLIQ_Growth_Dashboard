# AVERY AI — Technical Specification (Part 2)
## Phases 4-6: Store Preview, Ongoing Assistant, Polish & A/B Testing

---

# PHASE 4: STORE PREVIEW & PROFILE SETUP (Weeks 7-8)

## Overview
Build the live-updating store preview panel (left side of split-screen) and implement profile/bio/template setup through conversation.

---

## Ticket 4.1: Live Store Preview Panel

**Type:** Frontend | **Estimate:** 4 days | **Priority:** P0

### Description
Left panel of full-screen onboarding shows a real-time preview of the coach's store. Updates instantly as Avery publishes blogs, changes bio, applies templates, etc.

### Component

```typescript
export function AveryStorePreview({ applicationId }) {
  const [storeData, setStoreData] = useState(null);
  const [changedFields, setChangedFields] = useState([]);
  const { lastMessage } = useAveryWebSocket();

  useEffect(() => {
    if (lastMessage?.type === 'store_preview_update') {
      setStoreData(prev => ({ ...prev, ...lastMessage.payload }));
      setChangedFields(lastMessage.payload.changedFields || []);
      setTimeout(() => setChangedFields([]), 2000);
    }
  }, [lastMessage]);

  return (
    <div className="store-preview-container">
      <div className="store-preview-header">
        <span className="preview-label">Live Preview</span>
        <span className="preview-url">{storeData?.url}</span>
        <button onClick={() => window.open(storeData?.url)}>Open ↗</button>
      </div>
      <div className="store-preview-frame">
        <StoreHero {...storeData} highlight={changedFields.includes('hero')} />
        <StorePricing price={storeData?.price} highlight={changedFields.includes('pricing')} />
        <StoreBlogGrid blogs={storeData?.blogs} highlight={changedFields.includes('blogs')} />
      </div>
    </div>
  );
}
```

### Backend: Push Updates After Store Changes

```typescript
const STORE_MODIFYING_FUNCTIONS = [
  'update_coach_profile', 'generate_blog_posts',
  'set_subscription_price', 'apply_store_template',
];

async function notifyStorePreviewUpdate(ws, applicationId, changedFields) {
  const storeData = await getFullStoreData(applicationId);
  ws.send(JSON.stringify({
    type: 'store_preview_update',
    payload: { ...storeData, changedFields }
  }));
}
```

### Highlight Animation

```css
.store-section--highlight {
  animation: pulse-highlight 2s ease-out;
}
@keyframes pulse-highlight {
  0% { box-shadow: 0 0 0 0 rgba(108, 92, 231, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(108, 92, 231, 0.1); }
  100% { box-shadow: 0 0 0 0 rgba(108, 92, 231, 0); }
}
```

### Acceptance Criteria
- [ ] Preview renders on left panel (60% width)
- [ ] Updates in real-time when blogs published, bio changed, price set, template applied
- [ ] Changed sections pulse with purple highlight for 2 seconds
- [ ] "Open in new tab" button works
- [ ] Store URL displayed in header
- [ ] Skeleton loading state
- [ ] Hidden on mobile (chat takes full width)

---

## Ticket 4.2: Template Application via Conversation

**Type:** Full-Stack | **Estimate:** 3 days | **Priority:** P1

### Niche → Template Mapping

```typescript
const NICHE_DEFAULT_TEMPLATES = {
  fitness: 'fitness_bold',
  wellness: 'wellness_calm',
  business: 'business_clean',
  lifestyle: 'creator_modern',
};

const TEMPLATE_VARIANTS = {
  fitness: ['fitness_bold', 'fitness_minimal', 'fitness_dark'],
  wellness: ['wellness_calm', 'wellness_nature', 'wellness_warm'],
  business: ['business_clean', 'business_modern', 'business_dark'],
  creator: ['creator_modern', 'creator_vibrant', 'creator_minimal'],
};
```

### Conversation Flow
```
AVERY: "I've applied a bold, energetic theme for your fitness store. Like it?"
       [Looks great!] [Try something different]

COACH: "Can you try something more minimal?"
→ Avery calls: apply_store_template({ template_id: 'fitness_minimal' })
→ Store preview updates instantly

AVERY: "Done! Switched to a cleaner, minimal look. Better?"
       [Love it ✅] [Show me the dark theme]
```

### Backend

```typescript
async function executeApplyTemplate(applicationId, args) {
  const templateId = args.template_id || NICHE_DEFAULT_TEMPLATES[args.niche];
  const template = await getTemplateConfig(templateId);

  await kliqApi.updateStoreTheme(applicationId, {
    primaryColor: template.primaryColor,
    secondaryColor: template.secondaryColor,
    fontFamily: template.fontFamily,
    heroStyle: template.heroStyle,
    bannerGradient: template.bannerGradient,
  });

  return { templateId, templateName: template.name };
}
```

---

## Ticket 4.3: Profile Photo via Conversation

**Type:** Full-Stack | **Estimate:** 2 days | **Priority:** P0

### Three Paths

| Path | Trigger | Implementation |
|------|---------|---------------|
| From social account | Coach clicks "Use my Instagram photo" | Backend fetches IG profile photo → downloads → resizes via sharp → uploads to KLIQ CDN |
| Upload from device | Coach clicks "Upload photo 📷" | Frontend file picker → upload to /api/upload → CDN URL returned |
| Take selfie (mobile) | Coach clicks "Take selfie 🤳" | Frontend camera API → capture → upload |

### Backend: Social Photo Import

```typescript
async function handleProfilePhotoFromSocial(coachId, applicationId, platform) {
  const connection = await getSocialConnection(coachId, platform);
  const profile = await getSocialService(platform).getUserProfile(connection.accessToken);

  // Download → resize → upload
  const imageBuffer = await downloadImage(profile.profilePictureUrl);
  const resized = await sharp(imageBuffer).resize(800, 800, { fit: 'cover' }).jpeg({ quality: 85 }).toBuffer();
  const cdnUrl = await uploadToCDN(applicationId, 'profile', resized);

  await kliqApi.updateProfile(applicationId, { profile_image_url: cdnUrl });
  await scorecardService.markComplete(coachId, applicationId, 'profile_photo');

  return { cdnUrl };
}
```

### Frontend: File Upload in Chat

```typescript
function PhotoUploadMessage({ onUpload }) {
  const fileInputRef = useRef(null);
  return (
    <div className="avery-upload-zone">
      <input ref={fileInputRef} type="file" accept="image/*" capture="user"
        onChange={async (e) => {
          const file = e.target.files[0];
          if (!file) return;
          const formData = new FormData();
          formData.append('photo', file);
          const { cdnUrl } = await fetch('/api/upload/profile-photo', { method: 'POST', body: formData }).then(r => r.json());
          averyWs.send(JSON.stringify({ type: 'photo_uploaded', payload: { cdnUrl } }));
        }}
        hidden
      />
      <button onClick={() => fileInputRef.current?.click()}>📷 Choose photo</button>
    </div>
  );
}
```

---

## Ticket 4.4: AI Bio Generation & Editing

**Type:** Backend | **Estimate:** 2 days | **Priority:** P0

### Bio Generation

```typescript
async function generateBio(context, tone) {
  const socialData = await getSocialProfileData(context.coachId);

  const response = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [
      { role: 'system', content: `Write short bios for coaches. 2-4 sentences. No clichés. Match the tone. Return ONLY the bio text.` },
      { role: 'user', content: `Bio for ${context.preferredName}.\nNiche: ${context.niche}\nSpecialty: ${context.specialty}\nTone: ${tone || 'casual'}\n${socialData ? `IG bio: ${socialData.bio}, Followers: ${socialData.followerCount}` : ''}` }
    ],
    max_tokens: 200,
    temperature: 0.8,
  });

  return response.choices[0].message.content.trim();
}
```

### Tone Editing via Free-Text

```
COACH: "Can you make it more casual?"
→ GPT-4o detects tone change request → regenerates bio with tone='casual'
→ Calls update_coach_profile({ bio: newBio }) → store preview updates

Supported tone keywords:
  casual: ['casual','relaxed','chill','informal','fun','friendly']
  professional: ['professional','formal','serious','polished']
  energetic: ['energetic','exciting','bold','punchy','hype']
  calm: ['calm','gentle','soft','peaceful','zen']
```

---

## Sprint 4 Definition of Done
- [ ] Live store preview renders on left panel
- [ ] Preview updates in real-time for all store-modifying functions
- [ ] Changed sections highlight with animation
- [ ] Template auto-applied based on niche, changeable via conversation
- [ ] Profile photo from social / upload / selfie working
- [ ] AI bio generation + tone editing via free-text
- [ ] All changes reflected in both preview AND actual live store

---
---

# PHASE 5: ONGOING ASSISTANT & NUDGES (Weeks 9-10)

## Overview
Avery transitions from onboarding guide to ongoing assistant. Daily check-ins, proactive nudges, reactive Q&A, analytics reporting.

---

## Ticket 5.1: Post-Onboarding Mode Switch

**Type:** Full-Stack | **Estimate:** 2 days | **Priority:** P0

### Onboarding Completion Handler

```typescript
async function completeOnboarding(ws, coachId) {
  const context = await getCoachContext(coachId);

  // 1. Mark complete
  await db.query(`UPDATE avery_coach_context SET onboarding_complete = TRUE, onboarding_completed_at = NOW() WHERE coach_id = $1`, [coachId]);

  // 2. Celebration message
  ws.send(JSON.stringify({ type: 'avery_message', payload: {
    content: `🎉 You did it, ${context.preferredName}! Your store is live and looking amazing.\n\nI'm always here — just click my icon. I can write blogs, help plan live sessions, and give you growth tips.\n\nTalk soon! 💪`,
    progressPct: 100,
  }}));

  // 3. Confetti animation
  ws.send(JSON.stringify({ type: 'celebration', payload: { type: 'confetti', badge: 'Launch Champion', duration: 3000 } }));

  // 4. Transition to widget mode after 5 seconds
  setTimeout(() => ws.send(JSON.stringify({ type: 'mode_change', payload: { mode: 'minimised' } })), 5000);

  // 5. Schedule Day 2-7 nudges
  await scheduleOnboardingNudges(coachId);
}
```

### Post-Onboarding System Prompt

```
You are Avery, the AI assistant for {name} on KLIQ.
You are NO LONGER in onboarding mode. You are an ongoing assistant.

YOUR ROLE NOW:
- Answer questions about KLIQ features
- Write blog posts on request
- Share analytics and growth tips
- Help schedule live sessions
- Celebrate milestones

KEEP MESSAGES SHORT (1-3 sentences). Only elaborate if asked.

COACH STATS:
- Subscribers: {subscriberCount}
- Revenue: £{monthlyRevenue}/month
- Blogs: {blogCount}
- Last live: {lastLiveSession}
- Visitors this week: {weeklyVisitors}
```

---

## Ticket 5.2: Scheduled Nudge System

**Type:** Backend | **Estimate:** 3 days | **Priority:** P0

### First 7 Days Nudge Schedule

| Day | Nudge Type | Content | Buttons |
|-----|-----------|---------|---------|
| **Day 2** | `day2_morning` | "Your store had {visitors} visitors yesterday. {blog_views} read your blogs. Coaches who go live in Week 1 get subs 3x faster." | [Schedule live] [Not yet] |
| **Day 3** | `day3_stripe` | "Your store is getting traffic — {visitors} total. Haven't connected Stripe yet. Want me to walk you through it?" | [Set up Stripe] [Remind tomorrow] |
| **Day 5** | `day5_blogs` | "{draft_count} new blog drafts ready from your latest posts: {titles}" | [Review & publish] [Skip] |
| **Day 7** | `day7_recap` | "Week 1 recap: {visitors} visitors, {blogs} posts, {subscribers} subs. You're top {percentile}% of new coaches!" | [Plan this week] [I'm good] |

### Nudge Processor (Cron — Every 5 Minutes)

```typescript
async function processScheduledNudges() {
  const dueNudges = await db.query(`
    SELECT n.*, ac.preferred_name, ac.application_id
    FROM avery_nudges n
    JOIN avery_coach_context ac ON ac.coach_id = n.coach_id
    WHERE n.status = 'pending' AND n.scheduled_for <= NOW()
    ORDER BY n.scheduled_for ASC LIMIT 50
  `);

  for (const nudge of dueNudges.rows) {
    const analytics = await getStoreAnalytics(nudge.application_id);
    const content = hydrateTemplate(nudge.message_content, analytics);

    const ws = getActiveWebSocket(nudge.coach_id);
    if (ws) {
      // In-app via WebSocket
      ws.send(JSON.stringify({ type: 'avery_message', payload: { content, buttons: nudge.buttons } }));
    } else {
      // Push notification + queue as unread
      await sendPushNotification(nudge.coach_id, { title: 'Avery', body: content.substring(0, 100) + '...', deepLink: '/admin?avery=open' });
      await saveMessage(nudge.coach_id, 'avery', content, { buttons: nudge.buttons });
    }

    await db.query(`UPDATE avery_nudges SET status = 'sent', sent_at = NOW() WHERE id = $1`, [nudge.id]);
  }
}

function hydrateTemplate(template, analytics) {
  return template
    .replace('{visitors}', analytics.totalVisitors || 0)
    .replace('{blog_views}', analytics.blogViews || 0)
    .replace('{subscribers}', analytics.subscriberCount || 0)
    .replace('{blogs}', analytics.blogCount || 0)
    .replace('{percentile}', analytics.percentileRank || 50)
    .replace('{draft_count}', analytics.draftCount || 0)
    .replace('{draft_titles}', analytics.draftTitles?.map(t => `📝 "${t}"`).join('\n') || '');
}
```

---

## Ticket 5.3: Proactive Event-Driven Triggers

**Type:** Backend | **Estimate:** 3 days | **Priority:** P1

### Trigger Definitions

| Trigger | Check Type | Condition | Message | Cooldown |
|---------|-----------|-----------|---------|----------|
| **First subscriber** | Real-time event | subscriberCount === 1 | "🎉🎉🎉 You got your FIRST SUBSCRIBER! {name} just signed up. You're officially earning!" | None |
| **Subscriber milestone** | Real-time event | Count hits 10/25/50/100/250/500/1000 | "🎉 You hit {count} subscribers! That's £{revenue}/month." | None |
| **Revenue milestone** | Real-time event | Revenue crosses £100/500/1K/5K | "💰 You crossed £{amount} total revenue!" | None |
| **No login 3 days** | Daily cron | Last login ≥ 3 days ago | "Haven't seen you in a few days. {visitors} visitors while you were away." | 72 hours |
| **Churn risk (7+ days)** | Daily cron | Last login ≥ 7 days ago | "Your subscribers are asking about your next session. Want to schedule one?" | 72 hours |
| **Social post performing** | Weekly cron | New post with high engagement | "Your latest IG post is doing great! Want me to turn it into a blog?" | 168 hours |

### Real-Time Event Listener

```typescript
eventBus.on('new_subscriber', async (event) => {
  const { coachId, subscriberName, subscriberCount } = event;
  const ctx = await getCoachContext(coachId);

  // First subscriber — special celebration
  if (subscriberCount === 1) {
    const msg = `🎉🎉🎉 ${ctx.preferredName}, you just got your FIRST SUBSCRIBER! ${subscriberName} just signed up. This is HUGE!`;
    await sendAveryMessage(coachId, msg);
    return;
  }

  // Milestones
  if ([10, 25, 50, 100, 250, 500, 1000].includes(subscriberCount)) {
    const store = await getStoreState(ctx.applicationId);
    const revenue = subscriberCount * store.subscriptionPrice;
    const msg = `🎉 You just hit ${subscriberCount} subscribers! That's £${revenue.toFixed(2)}/month.`;
    await sendAveryMessage(coachId, msg);
  }
});

eventBus.on('payment_received', async (event) => {
  const { coachId, totalRevenue, previousRevenue } = event;
  const milestones = [100, 500, 1000, 5000];
  for (const m of milestones) {
    if (previousRevenue < m && totalRevenue >= m) {
      await sendAveryMessage(coachId, `💰 You just crossed £${m} in total revenue!`);
      break;
    }
  }
});
```

### Daily Cron: Churn Risk Detection

```typescript
// Runs daily at 9:00 AM UTC
async function checkChurnRisk() {
  const atRisk = await db.query(`
    SELECT ac.coach_id, ac.preferred_name, ac.application_id,
           EXTRACT(DAY FROM NOW() - ac.last_interaction_at) as days_inactive
    FROM avery_coach_context ac
    WHERE ac.onboarding_complete = TRUE
    AND ac.last_interaction_at < NOW() - INTERVAL '3 days'
    AND NOT EXISTS (
      SELECT 1 FROM avery_nudges n
      WHERE n.coach_id = ac.coach_id
      AND n.nudge_type IN ('no_login_3_days', 'churn_risk')
      AND n.sent_at > NOW() - INTERVAL '72 hours'
    )
  `);

  for (const coach of atRisk.rows) {
    const analytics = await getStoreAnalytics(coach.application_id);
    const nudgeType = coach.days_inactive >= 7 ? 'churn_risk' : 'no_login_3_days';

    let content;
    if (nudgeType === 'churn_risk') {
      content = `${coach.preferred_name}, your subscribers are asking when your next session is. Want me to help you schedule one?`;
    } else {
      content = `Hey ${coach.preferred_name}! Haven't seen you in a few days. Your store had ${analytics.recentVisitors} visitors while you were away.`;
    }

    await scheduleNudge(coach.coach_id, nudgeType, content, [
      { label: 'Schedule a session', action: 'start_live_scheduling', variant: 'primary' },
      { label: 'Snooze 3 days', action: 'snooze_nudge', variant: 'skip' },
    ], new Date());
  }
}
```

---

## Ticket 5.4: Reactive Q&A (Post-Onboarding)

**Type:** Backend | **Estimate:** 2 days | **Priority:** P1

### Common Patterns

| Coach Says | Avery Does |
|-----------|-----------|
| "How do I change my price?" | Asks new price → calls `set_subscription_price` |
| "Write a blog about meal prep" | Calls `generate_blog_posts(custom_topic: 'meal prep')` |
| "How am I doing?" | Calls `get_store_analytics` → formats stats + comparison |
| "Schedule a live session for Friday" | Calls `schedule_live_session` |
| "How do live sessions work?" | Explains feature (from system prompt knowledge) |
| "Can you write a post for me to share?" | Calls `generate_share_content` |
| "What should I do next?" | Analyses store state → suggests highest-impact action |

### "What should I do next?" Logic

```typescript
async function suggestNextAction(coachId, applicationId) {
  const store = await getStoreState(applicationId);
  const analytics = await getStoreAnalytics(applicationId);

  // Priority-ordered suggestions based on what's missing
  const suggestions = [];

  if (!store.stripeConnected && store.subscriberCount > 0)
    suggestions.push({ action: 'Connect Stripe — you have subscribers waiting to pay!', priority: 1 });

  if (store.blogCount < 5)
    suggestions.push({ action: `Publish more blogs (you have ${store.blogCount}). Blogs drive 6.8x retention.`, priority: 2 });

  if (!store.hasLiveSession)
    suggestions.push({ action: 'Schedule your first live session. Live sessions drive 28pp retention lift.', priority: 3 });

  if (analytics.daysSinceLastShare > 7)
    suggestions.push({ action: 'Share your store link again. Coaches who share weekly grow 3x faster.', priority: 4 });

  if (store.subscriberCount >= 50 && !store.hasGrowthServices)
    suggestions.push({ action: `You have ${store.subscriberCount} subs — eligible for KLIQ Growth Services!`, priority: 5 });

  return suggestions.sort((a, b) => a.priority - b.priority).slice(0, 3);
}
```

---

## Sprint 5 Definition of Done
- [ ] Onboarding → ongoing mode transition (full-screen → widget)
- [ ] Celebration animation (confetti + badge) at 100%
- [ ] Post-onboarding system prompt active
- [ ] Day 2/3/5/7 nudges scheduled and delivered
- [ ] Nudge processor cron running every 5 minutes
- [ ] Push notifications for offline coaches
- [ ] First subscriber celebration
- [ ] Subscriber/revenue milestone messages
- [ ] Churn risk detection (3-day + 7-day)
- [ ] Reactive Q&A working (price change, blog writing, analytics)
- [ ] "What should I do next?" smart suggestions
- [ ] Nudge snooze functionality

---
---

# PHASE 6: POLISH, A/B TESTING & LAUNCH (Weeks 11-12)

## Overview
Edge case handling, performance optimisation, A/B testing framework, analytics dashboard, and production hardening.

---

## Ticket 6.1: A/B Testing Framework

**Type:** Full-Stack | **Estimate:** 3 days | **Priority:** P0

### Variant Assignment

```typescript
// On coach signup, assign to a variant
async function assignOnboardingVariant(coachId) {
  const random = Math.random();
  let variant;

  if (random < 0.30) variant = 'control';        // Current: niche question → empty dashboard
  else if (random < 0.60) variant = 'scorecard';  // Static scorecard + 5-min storefront
  else variant = 'avery';                          // Conversational AI onboarding

  await db.query(`
    INSERT INTO ab_test_assignments (coach_id, test_name, variant, assigned_at)
    VALUES ($1, 'onboarding_v1', $2, NOW())
  `, [coachId, variant]);

  return variant;
}

// Frontend checks variant on admin panel load
async function getOnboardingExperience(coachId) {
  const assignment = await db.query(`
    SELECT variant FROM ab_test_assignments
    WHERE coach_id = $1 AND test_name = 'onboarding_v1'
  `, [coachId]);

  switch (assignment.rows[0]?.variant) {
    case 'control': return null;                    // No changes
    case 'scorecard': return 'scorecard_widget';    // Show scorecard widget
    case 'avery': return 'avery_fullscreen';        // Launch Avery full-screen
    default: return null;
  }
}
```

### Metrics Tracking

```sql
CREATE TABLE ab_test_assignments (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL,
    test_name VARCHAR(100) NOT NULL,
    variant VARCHAR(50) NOT NULL,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(coach_id, test_name)
);

CREATE TABLE ab_test_metrics (
    id BIGSERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL,
    test_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_ab_metrics ON ab_test_metrics(test_name, metric_name, recorded_at);
```

### Metrics to Track Per Variant

| Metric | How Measured | Target (Avery) |
|--------|-------------|----------------|
| **Onboarding completion rate** | All phases done / total signups | 65% |
| **Time to first blog** | signup → first blog published | < 5 minutes |
| **Time to first subscriber** | signup → first subscriber | < 14 days |
| **Blog count (Day 7)** | Blogs published in first week | ≥ 3 |
| **Store share rate** | Coaches who shared URL in Day 1 | 40% |
| **7-day return rate** | Logged in again within 7 days | 60% |
| **30-day retention** | Still active at Day 30 | 25% |
| **90-day retention** | Still active at Day 90 | 15% |
| **Revenue (Month 1)** | Total GMV in first month | £50 avg |

### Statistical Significance Calculator

```typescript
// Minimum sample size per variant for 95% confidence, 80% power
// Baseline: 8.8% 30-day retention, MDE: 50% relative lift (to 13.2%)
// Required: ~800 per variant → ~2,400 total → 6-8 weeks at current signup rate

function calculateSignificance(control, variant) {
  const pooledP = (control.successes + variant.successes) / (control.total + variant.total);
  const se = Math.sqrt(pooledP * (1 - pooledP) * (1/control.total + 1/variant.total));
  const z = (variant.rate - control.rate) / se;
  const pValue = 2 * (1 - normalCDF(Math.abs(z)));

  return {
    controlRate: control.rate,
    variantRate: variant.rate,
    lift: ((variant.rate - control.rate) / control.rate * 100).toFixed(1) + '%',
    pValue: pValue.toFixed(4),
    significant: pValue < 0.05,
    sampleSize: { control: control.total, variant: variant.total },
  };
}
```

---

## Ticket 6.2: Analytics Dashboard (Internal)

**Type:** Full-Stack | **Estimate:** 2 days | **Priority:** P1

### Avery Performance Dashboard

```sql
-- Daily Avery metrics view (for Power BI or internal dashboard)

CREATE VIEW avery_daily_metrics AS
SELECT
  DATE(e.created_at) as date,
  COUNT(DISTINCT CASE WHEN e.event_name = 'avery_conversation_started' THEN e.coach_id END) as conversations_started,
  COUNT(DISTINCT CASE WHEN e.event_name = 'avery_onboarding_completed' THEN e.coach_id END) as onboardings_completed,
  COUNT(CASE WHEN e.event_name = 'avery_message_sent' AND e.properties->>'role' = 'coach' THEN 1 END) as coach_messages,
  COUNT(CASE WHEN e.event_name = 'avery_message_sent' AND e.properties->>'role' = 'avery' THEN 1 END) as avery_messages,
  COUNT(CASE WHEN e.event_name = 'avery_button_clicked' THEN 1 END) as button_clicks,
  COUNT(CASE WHEN e.event_name = 'avery_free_text_used' THEN 1 END) as free_text_messages,
  COUNT(CASE WHEN e.event_name = 'avery_function_executed' THEN 1 END) as functions_executed,
  COUNT(CASE WHEN e.event_name = 'avery_blog_generated' THEN 1 END) as blogs_generated,
  COUNT(CASE WHEN e.event_name = 'avery_skip_clicked' THEN 1 END) as skips,
  COUNT(CASE WHEN e.event_name = 'avery_error' THEN 1 END) as errors,
  AVG(CASE WHEN e.event_name = 'avery_onboarding_completed'
    THEN (e.properties->>'duration_seconds')::numeric END) as avg_onboarding_seconds,
  -- Cost tracking
  SUM(CASE WHEN e.event_name = 'avery_api_call'
    THEN (e.properties->>'cost_usd')::numeric END) as total_api_cost_usd
FROM avery_events e
GROUP BY DATE(e.created_at);
```

### Key Dashboard Panels

| Panel | Metrics |
|-------|---------|
| **Funnel** | Started → Phase 1 → Phase 2 → ... → Complete (with drop-off %) |
| **Completion Rate** | Daily/weekly onboarding completion rate by variant |
| **Time Distribution** | Histogram of onboarding duration (target: under 5 min) |
| **Function Usage** | Which functions Avery calls most (bar chart) |
| **Free-Text vs Buttons** | Ratio of typed messages vs button clicks |
| **Skip Rate** | Which phases get skipped most |
| **Error Rate** | Errors per day, by type |
| **Cost** | Daily OpenAI API cost, cost per coach |
| **Nudge Performance** | Nudges sent vs responded, by type |
| **Retention Impact** | 7/30/90-day retention by variant (the money chart) |

---

## Ticket 6.3: Performance Optimisation

**Type:** Backend | **Estimate:** 2 days | **Priority:** P1

### Response Time Targets

| Action | Target | Optimisation |
|--------|--------|-------------|
| First message (welcome) | < 500ms | Pre-cached, no AI call |
| Text response (no function) | < 2 seconds | GPT-4o streaming, max_tokens=500 |
| Response with function call | < 5 seconds | Parallel function execution where possible |
| Blog generation (3 posts) | < 30 seconds | Parallel API calls, show progress |
| Store preview update | < 200ms | WebSocket push, no polling |

### Caching Strategy

```typescript
// Cache frequently accessed data to reduce DB queries

const CACHE_CONFIG = {
  'coach_context': { ttl: 300, store: 'redis' },      // 5 min
  'store_state': { ttl: 60, store: 'redis' },          // 1 min (changes during onboarding)
  'niche_benchmarks': { ttl: 86400, store: 'redis' },  // 24 hours (changes rarely)
  'template_configs': { ttl: 86400, store: 'memory' }, // 24 hours
  'system_prompt': { ttl: 3600, store: 'memory' },     // 1 hour
};

// Invalidate cache when data changes
async function invalidateCache(key, coachId) {
  await redis.del(`${key}:${coachId}`);
}
```

### Cost Optimisation

```typescript
// Use GPT-4o-mini for simple queries, GPT-4o for generation

function selectModel(phase, messageType) {
  // GPT-4o for content generation
  if (['content_import', 'profile_setup'].includes(phase)) return 'gpt-4o';
  if (messageType === 'blog_generation') return 'gpt-4o';
  if (messageType === 'bio_generation') return 'gpt-4o';

  // GPT-4o-mini for everything else (cheaper, faster)
  return 'gpt-4o-mini';
}

// Estimated cost per model:
// GPT-4o: $2.50/1M input, $10/1M output
// GPT-4o-mini: $0.15/1M input, $0.60/1M output
// Using mini for 70% of calls reduces cost by ~60%
```

---

## Ticket 6.4: Edge Case Handling

**Type:** Backend | **Estimate:** 2 days | **Priority:** P0

### Edge Cases Matrix

| Scenario | Detection | Handling |
|----------|-----------|---------|
| Coach closes browser mid-onboarding | WebSocket disconnect | Save state. Resume on next visit: "Welcome back! We were on..." |
| Coach returns after 30+ days | last_interaction_at check | "Hey! It's been a while. Your store still has {visitors} visitors. Want to pick up where we left off?" |
| Coach sends same message repeatedly | Dedup by content + 5s window | Ignore duplicates, respond once |
| Conversation loops (3+ similar exchanges) | Count similar intents in last 5 messages | "Hmm, let me try a different approach. Want to skip this step?" |
| Coach sends inappropriate content | OpenAI moderation API | "I can't help with that. Let's get back to setting up your store!" |
| Very long message (1000+ chars) | Character count check | Truncate to 500 chars for API, extract key intent |
| Multiple tabs open | WebSocket session management | Only one active WS per coach. New tab takes over. |
| Coach has no social AND skips templates | Phase skip tracking | Generate 3 generic niche blogs. Use default template. Still functional. |
| API rate limit (50 msg/hour) | Counter in Redis | "I need a quick break! I'll be back in a few minutes. In the meantime, check out your store preview!" |
| Coach asks about competitor platforms | Intent detection | Redirect: "I'm not sure about [competitor], but here's what KLIQ offers..." |

---

## Ticket 6.5: Production Hardening

**Type:** DevOps/Backend | **Estimate:** 2 days | **Priority:** P0

### Checklist

```
Infrastructure:
- [ ] WebSocket server behind load balancer with sticky sessions
- [ ] Redis for session state + caching (ElastiCache or equivalent)
- [ ] OpenAI API key in secrets manager (not env vars)
- [ ] Social OAuth credentials in secrets manager
- [ ] Database connection pooling (pgBouncer)
- [ ] WebSocket heartbeat (ping/pong every 30s)

Monitoring:
- [ ] OpenAI API latency + error rate alerts
- [ ] WebSocket connection count dashboard
- [ ] Function execution success rate alerts (< 95% = alert)
- [ ] Cost per day alert (> $50/day = alert)
- [ ] Nudge delivery rate monitoring

Security:
- [ ] WebSocket authentication via JWT
- [ ] Rate limiting: 50 messages/hour per coach
- [ ] Input sanitisation on all coach messages
- [ ] Content moderation on all AI-generated text
- [ ] Social tokens encrypted at rest (AES-256)
- [ ] GDPR: data deletion endpoint for coach data
- [ ] No PII in logs (redact coach names, emails)

Logging:
- [ ] Structured JSON logs for all Avery interactions
- [ ] OpenAI request/response logging (for prompt debugging)
- [ ] Function execution audit trail
- [ ] Error tracking (Sentry or equivalent)
```

---

## Sprint 6 Definition of Done
- [ ] A/B test framework assigning coaches to 3 variants
- [ ] All metrics tracked per variant
- [ ] Internal analytics dashboard live
- [ ] Response times meeting targets (< 2s text, < 5s function)
- [ ] GPT-4o-mini used for 70% of calls (cost reduction)
- [ ] All edge cases handled gracefully
- [ ] WebSocket reconnection working
- [ ] Rate limiting active
- [ ] Content moderation on all outputs
- [ ] Production monitoring + alerts configured
- [ ] Load tested to 100 concurrent coaches
- [ ] GDPR data deletion endpoint working

---
---

# APPENDIX: FULL TICKET SUMMARY

## All Tickets by Sprint

| Sprint | Ticket | Title | Type | Days | Priority |
|--------|--------|-------|------|------|----------|
| **1** | 1.1 | Chat Widget Component | Frontend | 3 | P0 |
| **1** | 1.2 | Real-Time Messaging (WebSocket) | Full-Stack | 3 | P0 |
| **1** | 1.3 | Conversation State Machine | Backend | 2 | P0 |
| **1** | 1.4 | Database Tables | Backend | 1 | P0 |
| **1** | 1.5 | Scripted Fallback (No AI) | Backend | 2 | P1 |
| **2** | 2.1 | OpenAI Service Layer | Backend | 3 | P0 |
| **2** | 2.2 | Function Executor (12 Tools) | Backend | 4 | P0 |
| **2** | 2.3 | Prompt Engineering & Testing | Backend/AI | 3 | P0 |
| **2** | 2.4 | Error Handling & Fallbacks | Backend | 2 | P0 |
| **3** | 3.1 | Instagram OAuth | Full-Stack | 4 | P0 |
| **3** | 3.2 | TikTok OAuth | Full-Stack | 3 | P1 |
| **3** | 3.3 | YouTube OAuth | Full-Stack | 2 | P2 |
| **3** | 3.4 | AI Blog Generation Pipeline | Backend | 4 | P0 |
| **3** | 3.5 | Weekly Blog Cron Job | Backend | 1 | P1 |
| **4** | 4.1 | Live Store Preview Panel | Frontend | 4 | P0 |
| **4** | 4.2 | Template Application | Full-Stack | 3 | P1 |
| **4** | 4.3 | Profile Photo via Conversation | Full-Stack | 2 | P0 |
| **4** | 4.4 | AI Bio Generation & Editing | Backend | 2 | P0 |
| **5** | 5.1 | Post-Onboarding Mode Switch | Full-Stack | 2 | P0 |
| **5** | 5.2 | Scheduled Nudge System | Backend | 3 | P0 |
| **5** | 5.3 | Proactive Event-Driven Triggers | Backend | 3 | P1 |
| **5** | 5.4 | Reactive Q&A | Backend | 2 | P1 |
| **6** | 6.1 | A/B Testing Framework | Full-Stack | 3 | P0 |
| **6** | 6.2 | Analytics Dashboard | Full-Stack | 2 | P1 |
| **6** | 6.3 | Performance Optimisation | Backend | 2 | P1 |
| **6** | 6.4 | Edge Case Handling | Backend | 2 | P0 |
| **6** | 6.5 | Production Hardening | DevOps | 2 | P0 |

**Total: 27 tickets | 66 dev-days | 12 weeks (with 2-person team)**

---

## Dependencies Graph

```
Sprint 1 (Chat UI + State Machine + DB)
    ↓
Sprint 2 (OpenAI + Function Calling)
    ↓
Sprint 3 (Social OAuth + Blog Gen)  ←  Meta App Review (submit Week 1!)
    ↓
Sprint 4 (Store Preview + Profile)
    ↓
Sprint 5 (Ongoing Assistant + Nudges)
    ↓
Sprint 6 (A/B Test + Polish + Launch)
```

## Critical Path Items
1. **Meta App Review** — Submit Instagram app for review in Week 1. Takes 2-4 weeks.
2. **KLIQ Internal APIs** — Audit which APIs exist (blog create, profile update, pricing, theme) in Week 1. Build missing ones in parallel.
3. **Prompt Engineering** — Budget 2 full weeks of iteration. First version WILL feel robotic.
4. **WebSocket Infrastructure** — Needs sticky sessions behind load balancer. Plan infrastructure in Week 1.

## Environment Variables Required

```
# OpenAI
OPENAI_API_KEY=sk-...

# Instagram (Meta)
INSTAGRAM_APP_ID=...
INSTAGRAM_APP_SECRET=...
INSTAGRAM_REDIRECT_URI=https://admin.joinkliq.io/auth/instagram/callback

# TikTok
TIKTOK_CLIENT_KEY=...
TIKTOK_CLIENT_SECRET=...
TIKTOK_REDIRECT_URI=https://admin.joinkliq.io/auth/tiktok/callback

# YouTube (Google)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
YOUTUBE_REDIRECT_URI=https://admin.joinkliq.io/auth/youtube/callback

# Redis
REDIS_URL=redis://...

# WebSocket
WS_PORT=8080
WS_PATH=/avery

# BigQuery (for niche benchmarks)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

# Engagement Features

Sources: Intercom Developer Documentation, Intercom Product Tours/Surveys/Checklists docs
Covers: product tours, surveys, checklists, news items, tickets, articles, Help Center, onboarding patterns.

---

## Feature Comparison

| Feature | Method | ID Source | Must Be | Key Gotcha |
|---------|--------|-----------|---------|------------|
| Tour | `startTour(id)` | Dashboard URL | Published + "Use everywhere" | Series tours fail silently |
| Survey | `startSurvey(id)` | "Share" section | Live | 5-7 second delay |
| Checklist | `startChecklist(id)` | Dashboard URL | Published | None |
| News | `showNews(id)` | Dashboard URL | Published | None |
| Ticket | `showTicket(id)` | API/Dashboard | Existing | Opens messenger if closed |
| Article | `showArticle(id)` | Dashboard URL | Published | Invalid ID opens Home |

---

## Product Tours

### startTour(tourId)

`window.Intercom('startTour', tourId)` triggers a published product tour programmatically. The `tourId` is the numeric ID visible in the Intercom dashboard URL when editing the tour (e.g., `/tours/12345/edit` — the ID is `12345`).

**Prerequisites:**
- The tour must be published (not draft).
- The tour must have "Use tour everywhere" enabled in its settings. Tours without this setting only display on the specific URL they were configured for, and calling `startTour()` from any other page silently does nothing.

**Critical gotcha — Series tours:** Tours that belong to an Intercom Series cannot be triggered via `startTour()`. The call returns no error and no visible feedback — it simply fails silently. If a tour is part of a Series, duplicate it as a standalone tour outside the Series, then use the duplicate's ID for programmatic triggering.

```javascript
function launchWelcomeTour(tourId) {
  if (!tourId) {
    console.warn('Intercom: no tourId provided');
    return;
  }
  window.Intercom('startTour', tourId);
}

// Usage — ID comes from dashboard URL
launchWelcomeTour(12345);
```

**When to use:** Feature discovery after a new release, guided setup flows, contextual walkthroughs triggered by a user action (e.g., clicking "Show me how").

**Debugging:** If the tour does not appear, verify in the dashboard that (1) the tour is published, (2) "Use tour everywhere" is checked, and (3) the tour is not inside a Series. There is no JavaScript error thrown on failure.

---

## Surveys

### startSurvey(surveyId)

`window.Intercom('startSurvey', surveyId)` displays a survey to the current user. The `surveyId` is found in the Intercom dashboard under the survey's "Additional ways to share" section — not in the URL.

**Prerequisites:**
- The survey must be in "Live" status. Draft surveys do not display.

**Critical gotcha — delay:** There is a known delay of approximately 5 to 7 seconds between calling `startSurvey()` and the survey appearing on screen. This is an Intercom platform behavior, not a network issue. Do not call `startSurvey()` multiple times assuming the first call failed — doing so queues duplicate surveys. Inform the user that the survey is loading if the delay would otherwise feel broken.

```javascript
function requestFeedback(surveyId) {
  // Show immediate feedback so the user knows something is happening.
  // The survey itself will appear after ~5-7 seconds.
  showLoadingIndicator('Loading feedback survey...');

  window.Intercom('startSurvey', surveyId);

  // Hide the indicator after a safe buffer — the survey handles itself from here.
  setTimeout(() => hideLoadingIndicator(), 8000);
}
```

**When to use:** NPS collection after a milestone (e.g., first export, first publish), post-onboarding satisfaction, feature-specific feedback triggered by a button click.

**Targeting note:** `startSurvey()` bypasses Intercom's audience targeting rules. The survey fires for whoever is currently identified, regardless of the survey's configured audience filters. Use this intentionally — it is a feature, not a bug — but ensure the user context is correct before calling.

For trackEvent patterns that complement survey triggers, see `references/events-and-workflows.md`.

---

## Checklists

### startChecklist(checklistId)

`window.Intercom('startChecklist', checklistId)` opens a specific onboarding checklist. The `checklistId` is the numeric ID in the dashboard URL when editing the checklist.

**Prerequisites:**
- The checklist must be published.

```javascript
window.Intercom('startChecklist', 67890);
```

**Show all active checklists:** `window.Intercom('showSpace', 'tasks')` opens the Tasks space in the messenger, which lists all checklists currently active for the user. Use this for a "View your setup checklist" CTA rather than targeting a specific checklist ID.

```javascript
// Open the tasks space to show all active checklists
document.getElementById('view-checklist-btn').addEventListener('click', () => {
  window.Intercom('showSpace', 'tasks');
});
```

**When to use:** Activation flows, setup wizards, feature adoption tracking. Checklists are more persistent than tours — users can return to them at any time via the messenger.

---

## News and Announcements

### showNews(newsItemId) and showSpace('news')

`window.Intercom('showNews', newsItemId)` opens a specific news item inside the messenger. The `newsItemId` is the numeric ID in the dashboard URL when viewing the news item.

`window.Intercom('showSpace', 'news')` opens the full news feed without targeting a specific item.

**Creating news items:** News items are created in the Intercom dashboard (Outbound > News) or via the Intercom REST API server-side. There is no client-side API for creating news items — creation always happens server-side or through the dashboard.

```javascript
// Open a specific announcement — e.g., from a "What's new" button
document.getElementById('whats-new-btn').addEventListener('click', () => {
  window.Intercom('showSpace', 'news');
});

// Deep-link to a specific release note
function openReleaseNote(newsItemId) {
  window.Intercom('showNews', newsItemId);
}
```

**When to use:**
- Product launch announcements triggered from a banner or notification dot.
- Feature update changelogs surfaced from a "What's new" badge.
- Seasonal or time-sensitive announcements.

News items support rich text, images, and reactions. They persist in the news feed so users can revisit them.

---

## Tickets

### showTicket(ticketId) and showSpace('tickets')

`window.Intercom('showTicket', ticketId)` opens a specific support ticket inside the messenger. If the messenger is closed, it opens automatically. The `ticketId` comes from the Intercom REST API response when a ticket is created, or from the dashboard.

`window.Intercom('showSpace', 'tickets')` opens the Tickets space, listing all tickets associated with the current user.

**Creating tickets:** Tickets are created via the Intercom REST API server-side. Never expose your Intercom API token to the browser — ticket creation must go through your backend. The backend creates the ticket and returns the `ticketId` to the frontend for display.

```javascript
// After backend creates a ticket and returns the ID
async function createAndShowTicket(issueDescription) {
  const response = await fetch('/api/support/tickets', {
    method: 'POST',
    body: JSON.stringify({ description: issueDescription }),
  });
  const { ticketId } = await response.json();

  // Surface the ticket in the messenger
  window.Intercom('showTicket', ticketId);
}

// Show all tickets for the current user
document.getElementById('my-tickets-btn').addEventListener('click', () => {
  window.Intercom('showSpace', 'tickets');
});
```

**When to use:**
- Support request tracking — show users their open tickets after submission.
- Feature request workflows — create a ticket on form submit, then surface it.
- "Check your request status" CTAs in the app.

---

## Articles and Help Center

### showArticle(articleId) and showSpace('help')

`window.Intercom('showArticle', articleId)` opens a specific Help Center article inside the messenger. The `articleId` is the numeric ID in the dashboard URL when editing the article (e.g., `/articles/12345-article-title` — the ID is `12345`).

`window.Intercom('showSpace', 'help')` opens the Help Center search interface inside the messenger.

**Critical gotcha — invalid IDs:** If `articleId` does not correspond to a published article, Intercom silently opens the Messenger Home instead of showing an error. There is no thrown exception and no console warning. Always verify article IDs against published articles before shipping. Unpublished or deleted articles also trigger this fallback behavior.

```javascript
// Contextual help — open the relevant article for the current feature
function showContextualHelp(articleId) {
  window.Intercom('showArticle', articleId);
}

// Generic help — open the Help Center search
document.getElementById('help-btn').addEventListener('click', () => {
  window.Intercom('showSpace', 'help');
});

// Open help article from a tooltip or "?" icon using data attributes
document.querySelectorAll('[data-help-article]').forEach((el) => {
  el.addEventListener('click', () => {
    const articleId = parseInt(el.dataset.helpArticle, 10);
    window.Intercom('showArticle', articleId);
  });
});
```

**When to use:**
- Contextual help icons ("?") next to complex UI elements.
- Error states — surface the relevant troubleshooting article.
- Onboarding — link to setup guides from within the product.
- Reduce support volume by surfacing self-serve answers at the point of confusion.

For messenger UI customization (custom launcher, hide default launcher), see `references/messenger-ui.md`.

---

## Conversations

### showConversation, showMessages, showNewMessage

`window.Intercom('showConversation', conversationId)` opens a specific conversation. The `conversationId` comes from the Intercom REST API or webhook payloads — it is not available client-side without a prior API call.

`window.Intercom('showMessages')` opens the message list (inbox view) inside the messenger.

`window.Intercom('showNewMessage', prepopulatedText)` opens the new message composer. Pass a string to pre-fill the message body — useful for support CTAs that include context.

```javascript
// "Continue your conversation" CTA — ID from backend
function openConversation(conversationId) {
  window.Intercom('showConversation', conversationId);
}

// Open the inbox
document.getElementById('messages-btn').addEventListener('click', () => {
  window.Intercom('showMessages');
});

// Pre-filled support message from an error state
function reportError(errorCode) {
  const message = `I encountered error ${errorCode} while using the app.`;
  window.Intercom('showNewMessage', message);
}
```

**When to use:**
- "Continue your conversation" CTAs in transactional emails or in-app notifications.
- Support follow-up prompts after a failed action.
- Pre-filled messages from error states to reduce friction in reporting issues.

---

## Onboarding Pattern

Combine engagement features to build a complete onboarding flow. The pattern below sequences a tour, checklist, event tracking, and survey across a user's first session and beyond.

```javascript
// onboarding.js — called after successful login for new users

const ONBOARDING = {
  welcomeTourId: 11111,         // Published standalone tour (not in a Series)
  activationChecklistId: 22222, // Published checklist
  npsSurveyId: 33333,           // Live survey
};

function startOnboarding(user) {
  if (user.isNewUser && !user.hasSeenWelcomeTour) {
    // Step 1: Launch the welcome tour immediately on first login.
    // Ensure the tour has "Use tour everywhere" enabled.
    window.Intercom('startTour', ONBOARDING.welcomeTourId);

    // Step 2: After the tour, surface the activation checklist.
    // Stagger with a delay — firing both simultaneously overwhelms the user.
    setTimeout(() => {
      window.Intercom('startChecklist', ONBOARDING.activationChecklistId);
    }, 30000); // 30 seconds — enough time for the tour to complete
  }
}

// Step 3: Track activation milestones as the user completes checklist items.
// See references/events-and-workflows.md for trackEvent patterns.
function onUserCompletedStep(stepName) {
  window.Intercom('trackEvent', `completed-${stepName}`);

  // Update a custom attribute to gate downstream features
  window.Intercom('update', {
    onboarding_step: stepName,
    [`completed_${stepName}`]: true,
  });
}

// Step 4: After the user completes onboarding, request NPS feedback.
// The ~5-7 second delay is expected — do not retry.
function requestPostOnboardingFeedback() {
  window.Intercom('startSurvey', ONBOARDING.npsSurveyId);
}

// Step 5: Gate a feature behind checklist completion.
// Check the custom attribute set in step 3.
function canAccessAdvancedFeature(user) {
  return user.intercomAttributes?.completed_setup === true;
}
```

**Sequencing principles:**
- Do not fire a tour, checklist, and survey simultaneously. Users dismiss everything when overwhelmed.
- Use `setTimeout` or event-driven triggers (e.g., fire the checklist after the tour's final step event) to stagger engagement.
- Store onboarding state in Intercom custom attributes via `update()` so it persists across sessions and devices.
- Use `showSpace('tasks')` as the entry point for returning users who want to resume their checklist — do not re-call `startChecklist()` on every login.

---

## Targeting and Timing

Use custom attributes and events to control when engagement features appear, rather than firing them unconditionally.

**Pattern — attribute-gated triggers:**

```javascript
// Set the user's onboarding step on login
window.Intercom('update', {
  onboarding_step: user.onboardingStep, // e.g., 'invited', 'activated', 'retained'
  plan_type: user.plan,
  days_since_signup: user.daysSinceSignup,
});

// Trigger a tour only for users on a specific step
function maybeShowFeatureTour(user, tourId) {
  if (user.onboardingStep === 'activated' && !user.hasSeenFeatureTour) {
    window.Intercom('startTour', tourId);
  }
}

// Show a contextual article when a user hits an error for the first time
function onFirstTimeError(errorType, articleId) {
  window.Intercom('update', { [`encountered_${errorType}`]: true });
  window.Intercom('showArticle', articleId);
}
```

**Avoid:**
- Calling `startTour()`, `startSurvey()`, or `startChecklist()` on every page load without a guard. These calls are not idempotent — repeated calls re-trigger the feature.
- Relying solely on Intercom's audience targeting for critical onboarding flows. Combine client-side guards with Intercom's targeting for reliability.
- Firing engagement features before `Intercom('boot', ...)` completes. Wrap calls in an `onload` callback or defer until the messenger is ready.

For trackEvent patterns and event-driven workflows, see `references/events-and-workflows.md`.
For messenger UI customization and launcher control, see `references/messenger-ui.md`.

# Dynamic Domain Detection - Testing Examples

## How to Test

Restart your server and try these messages in the chat interface:

### 1. Software Development Domain
**Try:**
- "I want to build an API to automate report generation"
- "We need a dashboard to track developer productivity"
- "Can we create a mobile app for our field workers?"

**Expected:**
- 🎯 Console shows: "Detected domain: software"
- AI asks about tech stack, scalability, integration

---

### 2. Engineering/Construction Domain
**Try:**
- "We need to build a new warehouse facility"
- "I have an idea to improve our manufacturing equipment"
- "Can we redesign the office structure for better safety?"

**Expected:**
- 🎯 Console shows: "Detected domain: engineering"
- AI asks about materials, safety standards, construction timeline

---

### 3. HR/People Domain
**Try:**
- "We need a better employee onboarding process"
- "I want to improve team morale and engagement"
- "Can we create a training program for new managers?"

**Expected:**
- 🎯 Console shows: "Detected domain: hr"
- AI asks about affected employees, culture impact, rollout timeline

---

### 4. Finance Domain
**Try:**
- "We should automate invoice processing"
- "I have an idea to reduce procurement costs"
- "Can we improve our budget forecasting system?"

**Expected:**
- 🎯 Console shows: "Detected domain: finance"
- AI asks about ROI, cost savings, compliance requirements

---

### 5. General (Fallback)
**Try:**
- "I have an idea"
- "We have a problem with delays"
- "Can we improve communication?"

**Expected:**
- No domain detected (uses general prompt)
- AI asks general questions about the problem and impact

---

## How It Works

1. **Keyword Matching**: The `detect_domain()` function scans your message for domain-specific keywords
2. **Scoring**: Each domain gets a score based on keyword matches
3. **Selection**: The domain with the highest score is selected
4. **Prompt Switching**: The appropriate system prompt is loaded
5. **Console Log**: You'll see "🎯 Detected domain: X" in your server console

## Adding New Domains

To add a new domain (e.g., "marketing", "legal"):

1. Add to `SYSTEM_PROMPTS` dict in `llm_client.py`
2. Add keywords to `DOMAIN_KEYWORDS` dict
3. Restart server - that's it!

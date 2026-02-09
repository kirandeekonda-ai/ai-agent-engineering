# Testing Guide - Week 23 Idea Chatbot

## ✅ Complete Testing Checklist

### Prerequisites
- [ ] Server running: `uvicorn main:app --reload`
- [ ] `.env` file with valid `GROQ_API_KEY`
- [ ] Both `prototype-chat.html` and `prototype-dashboard.html` accessible

---

## Test 1: Basic Chat Functionality

**Goal**: Verify chat interface works

1. Open `prototype-chat.html`
2. Send message: "Hello"
3. **Expected**: AI responds within 2-3 seconds
4. **Check**: Message appears in chat area
5. **Check**: Session ID visible in network tab

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 2: Domain Detection

**Goal**: Verify AI detects conversation domain

**Test Software Domain:**
1. Send: "I want to build an API"
2. **Check server console**: `🎯 Detected domain: software`

**Test Engineering Domain:**
1. Start new chat (refresh page)
2. Send: "I want to build a warehouse"
3. **Check console**: `🎯 Detected domain: engineering`

**Test HR Domain:**
1. Start new chat
2. Send: "I want to improve our onboarding process"
3. **Check console**: `🎯 Detected domain: hr`

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 3: AI Auto-Submission (THE BIG ONE!)

**Goal**: Verify AI automatically saves ideas when ready

**Follow this exact conversation:**

**Message 1:**
```
I want to build an automated report generation system
```
- **Check console**: Readiness check should say FALSE (not enough detail yet)

**Message 2 (AI responds, then you send):**
```
It will automatically pull data from our database and create weekly sales reports for the management team. Right now, our team spends 5 hours every week manually creating these reports in Excel.
```
- **Check console**: Might still be FALSE (needs estimates)

**Message 3 (AI responds,  then you send):**
```
I think we can build this in about 3 weeks with 2 backend developers. It would cost around $15,000 but save 20 hours per month across the team.
```

**Expected After Message 3:**
- **Console shows**:
  ```
  🤖 Readiness check: True - Has clear idea, problem, estimates
  ✨ Auto-extracting and saving idea...
  ✅ Idea auto-saved with ID: 1
  ```
- **Toast notification** appears bottom-right: "✨ Idea #1 saved automatically!"
- **Toast stays for 5 seconds** then fades out

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 4: Database Persistence

**Goal**: Verify idea was saved to database

1. Check that `ideas.db` file exists in project root
2. Open http://localhost:8000/docs
3. Try GET `/ideas` endpoint
4. Click "Try it out" → "Execute"

**Expected Response:**
```json
{
  "ideas": [
    {
      "id": 1,
      "title": "Automated Report Generation System",
      "description": "...",
      "time_estimate": "3 weeks",
      "cost_estimate": "$15,000",
      ...
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0,
  "has_more": false
}
```

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 5: Dashboard Display

**Goal**: Verify dashboard shows saved ideas

1. Open `prototype-dashboard.html`
2. **Check**: Page says "Loading ideas..." briefly
3. **Expected**: Idea card appears with:
   - ✅ Title: "Automated Report Generation System"
   - ✅ Description (truncated)
   - ✅ Domain badge: "💻 Software"
   - ✅ Complexity dot (colored)
   - ✅ Time: "3 weeks"
   - ✅ Cost: "$15,000"
   - ✅ Status badge: "Pending" (yellow)
4. **Check stats**: "1 idea submitted • 1 pending • 0 under review • 0 approved"

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 6: Dashboard Filtering

**Goal**: Verify status filters work

1. On dashboard, click "Pending" filter
2. **Expected**: Idea still shows (it's pending)
3. Click "Under Review" filter
4. **Expected**: No ideas shown (none in review)
5. Click "All" filter
6. **Expected**: Idea reappears

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 7: Navigation

**Goal**: Verify sidebar navigation works

1. On dashboard, click chat icon (left sidebar)
2. **Expected**: Opens `prototype-chat.html`
3. Click dashboard icon (left sidebar)
4. **Expected**: Opens `prototype-dashboard.html`

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 8: Multi-turn Conversation

**Goal**: Verify conversation memory works

1. Start fresh chat
2. Send: "My name is John"
3. AI responds
4. Send: "What's my name?"
5. **Expected**: AI says "John" or similar

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 9: Error Handling

**Test 9a: API Offline**
1. Stop the server (`Ctrl+C`)
2. Try to send a chat message
3. **Expected**: Error message appears in chat
4. **Expected**: Console shows connection error

**Test 9b: Invalid API Key**
1. Edit `.env`, set wrong API key
2. Restart server
3. Send message
4. **Expected**: Error response from backend

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 10: Theme Toggle

**Goal**: Verify dark/light mode works

1. On chat page, click sun/moon icon (top right)
2. **Expected**: Page switches to dark mode
3. Click again
4. **Expected**: Back to light mode
5. Try on dashboard too

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 11: Idea NOT Ready (Negative Test)

**Goal**: Verify AI doesn't save incomplete ideas

1. Start fresh chat
2. Send only: "I have an idea"
3. **Check console**: `🤖 Readiness check: False - Just started conversation`
4. **Expected**: NO auto-save happens
5. **Expected**: NO toast notification

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 12: Multiple Ideas

**Goal**: Verify system handles multiple ideas

1. Complete Test 3 again with a different idea
2. Example: "I want to build a Slack bot for approvals. It will cost $5K and take 2 weeks."
3. **Expected**: Second idea auto-saves
4. **Expected**: Toast shows "Idea #2"
5. Check dashboard
6. **Expected**: 2 ideas show
7. **Check stats**: "2 ideas submitted..."

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 13: API Documentation

**Goal**: Verify interactive docs work

1. Visit http://localhost:8000/docs
2. **Check**: Swagger UI loads
3. **Check**: 7+ endpoints visible
4. Try `/health` endpoint
5. **Expected**: `{"status": "healthy"}`

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 14: Edge Cases

**Test 14a: Very Long Message**
1. Send 500-word message
2. **Expected**: AI responds normally

**Test 14b: Special Characters**
1. Send: "Cost: $10,000-$15,000 (20% discount!)"
2. **Expected**: Handles $ and % correctly

**Test 14c: Empty Input**
1. Try to send empty message
2. **Expected**: Nothing happens / validation prevents

**Status**: ⬜ Pass / ⬜ Fail

---

## Test 15: Performance

**Goal**: Verify acceptable response times

**Timing Chat Response:**
1. Send message
2. Time until AI responds
3. **Target**: < 3 seconds

**Timing Auto-Save:**
1. Trigger auto-save
2. Time until toast appears
3. **Target**: < 5 seconds total

**Dashboard Load:**
1. Refresh dashboard
2. Time until ideas display
3. **Target**: < 1 second

**Status**: ⬜ Pass / ⬜ Fail

---

## Overall Test Results

| Test # | Feature | Status |
|--------|---------|--------|
| 1 | Basic Chat | ⬜ |
| 2 | Domain Detection | ⬜ |
| 3 | **AI Auto-Submission** | ⬜ |
| 4 | Database Persistence | ⬜ |
| 5 | Dashboard Display | ⬜ |
| 6 | Dashboard Filtering | ⬜ |
| 7 | Navigation | ⬜ |
| 8 | Multi-turn Memory | ⬜ |
| 9 | Error Handling | ⬜ |
| 10 | Theme Toggle | ⬜ |
| 11 | Idea NOT Ready | ⬜ |
| 12 | Multiple Ideas | ⬜ |
| 13 | API Docs | ⬜ |
| 14 | Edge Cases | ⬜ |
| 15 | Performance | ⬜ |

**Total Passed**: _____ / 15

---

## Known Limitations

1. **In-memory sessions** - Lost on server restart (upgrade to database in future)
2. **No authentication** - Anyone can access (add in production)
3. **Single-threaded** - For learning purposes only
4. **SQLite** - Use PostgreSQL for production

---

## Success Criteria

**Minimum Viable (MUST PASS):**
- ✅ Test 1: Basic Chat
- ✅ Test 3: AI Auto-Submission
- ✅ Test 4: Database Save
- ✅ Test 5: Dashboard Display

**Full Success (ALL SHOULD PASS):**
- All 15 tests pass
- No console errors
- Smooth user experience

---

**Happy Testing! 🧪**

# Next.js Setup Instructions

## PowerShell Execution Policy Issue

Windows is blocking `npx` from running due to PowerShell execution policy.

## Solution (Choose ONE):

### Option 1: Fix PowerShell Execution Policy (Recommended)

1. Open **PowerShell as Administrator**
2. Run:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
3. Type `Y` to confirm
4. Close and reopen your terminal

### Option 2: Use Git Bash or CMD

1. Open **Git Bash** or **Command Prompt (CMD)**
2. Navigate to project:
   ```bash
   cd "c:\Users\Kiran\AI Practice\Week 23 - Idea Chatbot"
   ```
3. Run the Next.js command:
   ```bash
   npx create-next-app@latest frontend --typescript --tailwind --app
   ```

### Option 3: Manual Next.js Setup

If neither works, I can create the Next.js structure manually.

---

## After Fixing, Run:

```bash
cd "c:\Users\Kiran\AI Practice\Week 23 - Idea Chatbot"
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --import-alias "@/*"
```

**Answer the prompts:**
- TypeScript: **Yes**
- ESLint: **Yes** 
- Tailwind CSS: **Yes**
- `src/` directory: **Yes**
- App Router: **Yes**
- Import alias: **Yes** (@/*)

Let me know when done!

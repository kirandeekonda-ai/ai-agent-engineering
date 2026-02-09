# Supabase Setup Guide

## Required Credentials

Please provide the following from your Supabase dashboard:

### 1. Database Connection String
**Location**: Project Settings → Database → Connection String → URI

Format:
```
postgresql://postgres:[YOUR_PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

### 2. Project URL
**Location**: Project Settings → API → Project URL

Format:
```
https://[PROJECT_REF].supabase.co
```

### 3. API Keys

**Location**: Project Settings → API

- **Anon Key** (public, safe for frontend)
  - Starts with `eyJ...`
  
- **Service Role Key** (secret, backend only)
  - Starts with `eyJ...`

---

## Add to .env File

Once you provide these, I'll add them to `.env`:

```bash
# Supabase Configuration
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJxxxxx...
SUPABASE_SERVICE_KEY=eyJxxxxx...
SUPABASE_DB_URL=postgresql://postgres:xxxxx@db.xxxxx.supabase.co:5432/postgres
```

---

## Next Steps After You Provide Credentials:

1. ✅ Install `psycopg2` for PostgreSQL
2. ✅ Create Supabase tables (migrate from SQLite)
3. ✅ Update `database.py` to use PostgreSQL
4. ✅ Test connection
5. ✅ Create Next.js frontend
6. ✅ Deploy to Render + Vercel

**Please share your Supabase credentials when ready!**

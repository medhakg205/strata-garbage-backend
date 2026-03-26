# Supabase Database Setup

## Project
**URL**: https://eclvmiklqhslpudxwwgw.supabase.co

## Environment Variables (.env)
SUPABASE_URL=https://eclvmiklqhslpudxwwgw.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjbHZtaWtscWhzbHB1ZHh3d2d3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ1MjQ4MTgsImV4cCI6MjA5MDEwMDgxOH0.NlbE-LuS263jBk3NkuXltSFZxhkKshDVZWkOYANu9pQ
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjbHZtaWtscWhzbHB1ZHh3d2d3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDUyNDgxOCwiZXhwIjoyMDkwMTAwODE4fQ.5qTwEMr2GJMo0BinBW9LZY0yYhvANtDFe3DGbBrUB7U

**Get keys**: Supabase Dashboard → **Settings** → **API** → Copy **anon** + **service_role**

## Test Credentials
collector@test.com / password123 (role: collector)
user@test.com / password123 (role: user)

## Features Deployed
- ✅ PostGIS geo queries
- ✅ Auto priority_score trigger  
- ✅ RLS policies (collectors full access)
- ✅ Images storage bucket
- ✅ Cron: update-pending-times (5min)

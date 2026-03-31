import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  "https://eclvmiklqhslpudxwwgw.supabase.co",
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjbHZtaWtscWhzbHB1ZHh3d2d3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ1MjQ4MTgsImV4cCI6MjA5MDEwMDgxOH0.NlbE-LuS263jBk3NkuXltSFZxhkKshDVZWkOYANu9pQ"
);

export default supabase;
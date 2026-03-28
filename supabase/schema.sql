-- COMPLETE SCHEMA - COPY ALL THIS
DROP TABLE IF EXISTS routes, garbage_reports CASCADE;

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  email TEXT UNIQUE,
  password_hash TEXT,
  role TEXT DEFAULT 'user' CHECK (role IN ('user', 'collector', 'admin')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO users (name, email, role) VALUES 
('Test Collector', 'collector@test.com', 'collector'),
('Test User', 'user@test.com', 'user');

CREATE TABLE garbage_reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  image_url TEXT,
  location GEOGRAPHY(POINT, 4326) NOT NULL,
  garbage_level TEXT CHECK (garbage_level IN ('low', 'medium', 'high')) DEFAULT 'medium',
  complaint_frequency INTEGER DEFAULT 0,
  reported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
  pending_minutes INTEGER,
  priority_score NUMERIC
);

CREATE OR REPLACE FUNCTION update_pending_minutes()
RETURNS TRIGGER AS $$
BEGIN
  NEW.pending_minutes = EXTRACT(EPOCH FROM (NOW() - NEW.reported_at))/60;
  NEW.priority_score = 
    (CASE WHEN NEW.garbage_level = 'high' THEN 3 WHEN NEW.garbage_level = 'medium' THEN 2 ELSE 1 END * 3) + 
    NEW.complaint_frequency * 2 + 
    COALESCE(NEW.pending_minutes, 0);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_pending BEFORE INSERT OR UPDATE ON garbage_reports FOR EACH ROW EXECUTE FUNCTION update_pending_minutes();

INSERT INTO garbage_reports (user_id, image_url, location, garbage_level) VALUES 
((SELECT id FROM users WHERE role='user'), 'test1.jpg', ST_SetSRID(ST_MakePoint(80.27, 13.08), 4326)::geography, 'high'),
((SELECT id FROM users WHERE role='user'), 'test2.jpg', ST_SetSRID(ST_MakePoint(80.28, 13.09), 4326)::geography, 'medium');

CREATE TABLE routes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  collector_id UUID REFERENCES users(id),
  report_ids UUID[],
  optimized_path JSONB,
  total_distance_km NUMERIC,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX garbage_geo_idx ON garbage_reports USING GIST (location);
CREATE INDEX garbage_priority_idx ON garbage_reports (priority_score DESC);
CREATE INDEX garbage_status_idx ON garbage_reports (status);

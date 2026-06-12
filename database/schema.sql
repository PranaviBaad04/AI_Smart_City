-- Supabase PostgreSQL Table Schema for AI Smart City Dashboard

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'citizen', -- 'admin', 'officer', 'citizen'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. TRAFFIC DATA TABLE
CREATE TABLE IF NOT EXISTS public.traffic_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location TEXT NOT NULL,
    vehicle_count INTEGER NOT NULL,
    avg_speed NUMERIC NOT NULL,
    congestion_level TEXT NOT NULL, -- 'Low', 'Medium', 'High'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. POLLUTION DATA TABLE
CREATE TABLE IF NOT EXISTS public.pollution_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location TEXT NOT NULL,
    aqi INTEGER NOT NULL,
    pm25 NUMERIC NOT NULL,
    pm10 NUMERIC NOT NULL,
    co2 NUMERIC NOT NULL,
    noise_level NUMERIC NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. SERVICE DATA TABLE
CREATE TABLE IF NOT EXISTS public.service_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name TEXT NOT NULL, -- 'Water Supply', 'Electricity', 'Waste Management', 'Road Maintenance'
    location TEXT NOT NULL,
    status TEXT NOT NULL, -- 'Operational', 'Maintenance', 'Outage', 'Under Repair'
    response_time NUMERIC NOT NULL, -- Average response time in hours
    issue_count INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. CITIZEN REPORTS TABLE
CREATE TABLE IF NOT EXISTS public.citizen_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    issue_type TEXT NOT NULL, -- 'Pothole Report', 'Garbage Issue', 'Water Leakage', 'Street Light Failure', 'Traffic Violation'
    description TEXT,
    location TEXT NOT NULL, -- Coordinates format "lat,lng" or text description
    image_url TEXT,
    status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending', 'In Progress', 'Resolved'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS for all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.traffic_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pollution_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.service_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.citizen_reports ENABLE ROW LEVEL SECURITY;

-- Setup simple RLS policies for Anon Access (Development/Demo)
DROP POLICY IF EXISTS "Allow all for anon" ON public.users;
DROP POLICY IF EXISTS "Allow all for anon" ON public.traffic_data;
DROP POLICY IF EXISTS "Allow all for anon" ON public.pollution_data;
DROP POLICY IF EXISTS "Allow all for anon" ON public.service_data;
DROP POLICY IF EXISTS "Allow all for anon" ON public.citizen_reports;

CREATE POLICY "Allow all for anon" ON public.users FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for anon" ON public.traffic_data FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for anon" ON public.pollution_data FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for anon" ON public.service_data FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for anon" ON public.citizen_reports FOR ALL TO anon USING (true) WITH CHECK (true);

-- Seed Initial Users (Passwords: admin123, officer123, citizen123)
-- PBKDF2 hashed values (Werkzeug Security compatibility)
INSERT INTO public.users (id, name, email, password_hash, role) VALUES
('a1a1a1a1-a1a1-a1a1-a1a1-a1a1a1a1a1a1', 'Super Admin', 'admin@smartcity.gov', 'scrypt:32768:8:1$u7h7mZ4c83N0S528$867290bc5beed0fae929729ff70a0b22a0ecf445389659b85a3c9b7ea5779c1626ebc8c7c98076595ee48fe05d6cb4f2c0fc8d172e26487e35bdfb676f2bc8de', 'admin'),
('b2b2b2b2-b2b2-b2b2-b2b2-b2b2b2b2b2b2', 'Officer John', 'officer@smartcity.gov', 'scrypt:32768:8:1$u7h7mZ4c83N0S528$c3d1f11c81ef407a514d3cc8cb7387d853e8529ce1121d5a86a6058e39dbb7d2cd807865cbb68595aee4b1509bc7373f7c469f3fe2b9f36f6d0f7c2ac64bc1ba', 'officer'),
('c3c3c3c3-c3c3-c3c3-c3c3-c3c3c3c3c3c3', 'Jane Citizen', 'jane@gmail.com', 'scrypt:32768:8:1$u7h7mZ4c83N0S528$073539e6a9ee86dc63d4db5cdcb17f698e6ec29a7b973c1c905391c496cbb22f87ee2617f6424e6de83d95cf350ee979c5040ebde249bf5cc22c67ad3a8fe99c', 'citizen')
ON CONFLICT (email) DO NOTHING;

-- Seed Traffic Data (15 records)
-- Coordinates for map placements in a mock smart city (e.g. Metroville area, lat ~ 40.7128, lng ~ -74.0060)
INSERT INTO public.traffic_data (location, vehicle_count, avg_speed, congestion_level, timestamp) VALUES
('Downtown Broadway & 5th Ave', 145, 12.5, 'High', NOW() - INTERVAL '1 hour'),
('Downtown Broadway & 5th Ave', 160, 9.2, 'High', NOW() - INTERVAL '2 hours'),
('Downtown Broadway & 5th Ave', 85, 25.0, 'Medium', NOW() - INTERVAL '3 hours'),
('Uptown Expressway Exit 4', 210, 18.0, 'High', NOW() - INTERVAL '30 minutes'),
('Uptown Expressway Exit 4', 90, 45.5, 'Low', NOW() - INTERVAL '4 hours'),
('Westside Ring Road Sector 2', 45, 55.2, 'Low', NOW() - INTERVAL '1 hour'),
('Westside Ring Road Sector 2', 55, 52.0, 'Low', NOW() - INTERVAL '5 hours'),
('East Bridge Link', 185, 15.4, 'High', NOW() - INTERVAL '1 hour'),
('East Bridge Link', 130, 22.1, 'Medium', NOW() - INTERVAL '6 hours'),
('Financial District Central Sub', 190, 8.5, 'High', NOW() - INTERVAL '15 minutes'),
('Financial District Central Sub', 70, 30.0, 'Medium', NOW() - INTERVAL '8 hours'),
('Industrial Park Flyover', 120, 28.5, 'Medium', NOW() - INTERVAL '2 hours'),
('Industrial Park Flyover', 65, 42.0, 'Low', NOW() - INTERVAL '10 hours'),
('North Suburbs Access Rd', 40, 48.0, 'Low', NOW() - INTERVAL '12 hours'),
('North Suburbs Access Rd', 55, 43.2, 'Low', NOW() - INTERVAL '24 hours');

-- Seed Pollution Data (15 records)
INSERT INTO public.pollution_data (location, aqi, pm25, pm10, co2, noise_level, timestamp) VALUES
('Industrial Park Sector A', 165, 82.5, 120.4, 620.5, 78.5, NOW() - INTERVAL '1 hour'),
('Industrial Park Sector A', 178, 91.2, 132.0, 650.1, 80.2, NOW() - INTERVAL '2 hours'),
('Downtown Broadway & 5th Ave', 110, 38.2, 55.4, 480.2, 72.1, NOW() - INTERVAL '1 hour'),
('Downtown Broadway & 5th Ave', 135, 48.5, 72.1, 510.4, 75.0, NOW() - INTERVAL '4 hours'),
('Westside Ring Road Sector 2', 95, 32.1, 45.0, 420.5, 68.4, NOW() - INTERVAL '2 hours'),
('Financial District Central Sub', 125, 45.0, 68.2, 495.0, 74.5, NOW() - INTERVAL '3 hours'),
('Uptown Residential Area', 52, 12.4, 20.1, 350.2, 55.2, NOW() - INTERVAL '1 hour'),
('Uptown Residential Area', 48, 10.5, 18.2, 345.8, 52.0, NOW() - INTERVAL '5 hours'),
('East Bridge Link', 105, 36.5, 52.0, 460.2, 71.2, NOW() - INTERVAL '30 minutes'),
('North Suburbs Parkside', 42, 9.2, 15.0, 330.4, 48.5, NOW() - INTERVAL '2 hours'),
('North Suburbs Parkside', 38, 8.0, 12.5, 325.0, 47.0, NOW() - INTERVAL '10 hours'),
('Waterfront Marina Blvd', 65, 18.5, 28.4, 380.0, 60.1, NOW() - INTERVAL '4 hours'),
('Waterfront Marina Blvd', 70, 21.2, 32.0, 392.5, 62.5, NOW() - INTERVAL '8 hours'),
('City Center Square', 120, 42.8, 64.0, 488.2, 73.0, NOW() - INTERVAL '1 hour'),
('City Center Square', 142, 53.0, 78.5, 520.1, 76.5, NOW() - INTERVAL '5 hours');

-- Seed Public Services Data (12 records)
INSERT INTO public.service_data (service_name, location, status, response_time, issue_count) VALUES
('Water Supply', 'Downtown Broadway & 5th Ave', 'Operational', 1.2, 0),
('Water Supply', 'Industrial Park Sector A', 'Operational', 2.8, 1),
('Water Supply', 'Westside Ring Road Sector 2', 'Maintenance', 4.5, 3),
('Electricity', 'Financial District Central Sub', 'Operational', 0.8, 0),
('Electricity', 'Uptown Residential Area', 'Outage', 3.2, 5),
('Electricity', 'North Suburbs Access Rd', 'Operational', 1.5, 1),
('Waste Management', 'City Center Square', 'Under Repair', 6.0, 4),
('Waste Management', 'Uptown Residential Area', 'Operational', 2.0, 1),
('Waste Management', 'Industrial Park Sector A', 'Operational', 3.5, 2),
('Road Maintenance', 'Downtown Broadway & 5th Ave', 'Operational', 24.0, 0),
('Road Maintenance', 'Uptown Expressway Exit 4', 'Under Repair', 18.5, 6),
('Road Maintenance', 'East Bridge Link', 'Maintenance', 12.0, 2);

-- Seed Citizen Reports Data (5 records)
-- Locations are stored as: "latitude,longitude,readable_address"
INSERT INTO public.citizen_reports (user_id, issue_type, description, location, image_url, status, timestamp) VALUES
('c3c3c3c3-c3c3-c3c3-c3c3-c3c3c3c3c3c3', 'Pothole Report', 'Huge pothole in the middle lane causing cars to swerve dangerously.', '40.7128,-74.0060,Downtown Broadway & 5th Ave', '/static/images/pothole_sample.jpg', 'Pending', NOW() - INTERVAL '2 hours'),
('c3c3c3c3-c3c3-c3c3-c3c3-c3c3c3c3c3c3', 'Street Light Failure', 'Entire street light segment is dark since Monday. Very unsafe at night.', '40.7250,-74.0100,Westside Ring Road Sector 2', '/static/images/dark_street.jpg', 'In Progress', NOW() - INTERVAL '1 day'),
('c3c3c3c3-c3c3-c3c3-c3c3-c3c3c3c3c3c3', 'Garbage Issue', 'Trash cans overflowing, waste spilling onto the sidewalk and attracting rodents.', '40.7180,-73.9980,City Center Square', '/static/images/overflowing_trash.jpg', 'Resolved', NOW() - INTERVAL '3 days'),
('c3c3c3c3-c3c3-c3c3-c3c3-c3c3c3c3c3c3', 'Water Leakage', 'Clean water has been gushing from the cracked pipe on the side of the road.', '40.7060,-74.0150,Financial District Central Sub', '/static/images/water_leak.jpg', 'Pending', NOW() - INTERVAL '5 hours'),
('c3c3c3c3-c3c3-c3c3-c3c3-c3c3c3c3c3c3', 'Traffic Violations', 'Delivery trucks parking double, blocking the active lane and creating a gridlock.', '40.7300,-73.9900,East Bridge Link', NULL, 'In Progress', NOW() - INTERVAL '8 hours');

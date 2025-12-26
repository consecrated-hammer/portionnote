-- Add comprehensive nutrition tracking to Foods table
ALTER TABLE Foods ADD COLUMN FibrePerServing REAL;
ALTER TABLE Foods ADD COLUMN CarbsPerServing REAL;
ALTER TABLE Foods ADD COLUMN FatPerServing REAL;
ALTER TABLE Foods ADD COLUMN SaturatedFatPerServing REAL;
ALTER TABLE Foods ADD COLUMN SugarPerServing REAL;
ALTER TABLE Foods ADD COLUMN SodiumPerServing REAL;

-- Add source tracking for AI-populated foods
ALTER TABLE Foods ADD COLUMN DataSource TEXT DEFAULT 'manual';  -- 'manual' or 'ai'
ALTER TABLE Foods ADD COLUMN CountryCode TEXT DEFAULT 'AU';  -- ISO country code

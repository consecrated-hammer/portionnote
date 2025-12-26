-- Split serving description into quantity and unit
-- Migration: 006_food_serving_split.sql

-- Add new columns
ALTER TABLE Foods ADD COLUMN ServingQuantity REAL DEFAULT 1.0;
ALTER TABLE Foods ADD COLUMN ServingUnit TEXT DEFAULT 'serving';

-- Migrate existing data (set default values for any existing foods)
UPDATE Foods SET ServingQuantity = 1.0, ServingUnit = 'serving' WHERE ServingQuantity IS NULL;

-- Note: ServingDescription is kept for backwards compatibility but will be deprecated
-- New code should use ServingQuantity + ServingUnit instead

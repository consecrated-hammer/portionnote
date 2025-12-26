-- Add weight tracking fields
-- Add WeightKg to Users table for initial/target weight
ALTER TABLE Users ADD COLUMN WeightKg real;

-- Add WeightKg to DailyLogs for daily weight entries
ALTER TABLE DailyLogs ADD COLUMN WeightKg real;

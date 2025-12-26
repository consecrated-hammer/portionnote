-- Add ShowStepsOnToday toggle to Settings table
ALTER TABLE Settings ADD COLUMN ShowStepsOnToday INTEGER NOT NULL DEFAULT 1;

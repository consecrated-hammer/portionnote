-- Add MealTemplateId column to MealEntries to support logging templates as distinct items
-- MealEntries can now link to either a Food OR a MealTemplate (mutually exclusive)

-- Step 1: Add MealTemplateId column
ALTER TABLE MealEntries ADD COLUMN MealTemplateId text;

-- Step 2: Create index on MealTemplateId
CREATE INDEX IF NOT EXISTS MealEntries_MealTemplateId_Idx ON MealEntries (MealTemplateId);

-- Step 3: Make FoodId nullable by recreating the table
-- SQLite doesn't support ALTER COLUMN, so we need to recreate the table

-- Create new table with FoodId nullable
CREATE TABLE MealEntries_New (
  MealEntryId text PRIMARY KEY,
  DailyLogId text NOT NULL,
  MealType text NOT NULL,
  FoodId text,
  MealTemplateId text,
  Quantity real NOT NULL DEFAULT 1,
  EntryNotes text,
  SortOrder integer NOT NULL DEFAULT 0,
  ScheduleSlotId text,
  CreatedAt text NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT MealEntries_MealType_Check CHECK (MealType IN ('Breakfast', 'Snack1', 'Lunch', 'Snack2', 'Dinner')),
  FOREIGN KEY (DailyLogId) REFERENCES DailyLogs(DailyLogId) ON DELETE CASCADE,
  FOREIGN KEY (FoodId) REFERENCES Foods(FoodId),
  FOREIGN KEY (MealTemplateId) REFERENCES MealTemplates(MealTemplateId)
);

-- Copy existing data
INSERT INTO MealEntries_New (
  MealEntryId, DailyLogId, MealType, FoodId, MealTemplateId, Quantity, EntryNotes, SortOrder, ScheduleSlotId, CreatedAt
)
SELECT 
  MealEntryId, DailyLogId, MealType, FoodId, MealTemplateId, Quantity, EntryNotes, SortOrder, ScheduleSlotId, CreatedAt
FROM MealEntries;

-- Drop old table
DROP TABLE MealEntries;

-- Rename new table
ALTER TABLE MealEntries_New RENAME TO MealEntries;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS MealEntries_DailyLogId_Idx ON MealEntries (DailyLogId);
CREATE INDEX IF NOT EXISTS MealEntries_ScheduleSlotId_Idx ON MealEntries (ScheduleSlotId);
CREATE INDEX IF NOT EXISTS MealEntries_MealTemplateId_Idx ON MealEntries (MealTemplateId);


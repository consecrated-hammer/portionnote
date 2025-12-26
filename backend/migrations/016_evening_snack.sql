-- Add Snack3 meal type and update check constraints

-- Update MealEntries check constraint (SQLite requires table rebuild)
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
  CONSTRAINT MealEntries_MealType_Check CHECK (MealType IN ('Breakfast', 'Snack1', 'Lunch', 'Snack2', 'Dinner', 'Snack3')),
  FOREIGN KEY (DailyLogId) REFERENCES DailyLogs(DailyLogId) ON DELETE CASCADE,
  FOREIGN KEY (FoodId) REFERENCES Foods(FoodId),
  FOREIGN KEY (MealTemplateId) REFERENCES MealTemplates(MealTemplateId)
);

INSERT INTO MealEntries_New (
  MealEntryId, DailyLogId, MealType, FoodId, MealTemplateId, Quantity, EntryNotes, SortOrder, ScheduleSlotId, CreatedAt
)
SELECT 
  MealEntryId, DailyLogId, MealType, FoodId, MealTemplateId, Quantity, EntryNotes, SortOrder, ScheduleSlotId, CreatedAt
FROM MealEntries;

DROP TABLE MealEntries;
ALTER TABLE MealEntries_New RENAME TO MealEntries;

CREATE INDEX IF NOT EXISTS MealEntries_DailyLogId_Idx ON MealEntries (DailyLogId);
CREATE INDEX IF NOT EXISTS MealEntries_ScheduleSlotId_Idx ON MealEntries (ScheduleSlotId);
CREATE INDEX IF NOT EXISTS MealEntries_MealTemplateId_Idx ON MealEntries (MealTemplateId);

-- Update ScheduleSlots check constraint (SQLite requires table rebuild)
CREATE TABLE ScheduleSlots_New (
  ScheduleSlotId text PRIMARY KEY,
  UserId text NOT NULL,
  SlotName text NOT NULL,
  SlotTime text NOT NULL,
  MealType text NOT NULL,
  SortOrder integer NOT NULL DEFAULT 0,
  CreatedAt text NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT ScheduleSlots_MealType_Check CHECK (
    MealType IN ('Breakfast', 'Snack1', 'Lunch', 'Snack2', 'Dinner', 'Snack3')
  )
);

INSERT INTO ScheduleSlots_New (
  ScheduleSlotId, UserId, SlotName, SlotTime, MealType, SortOrder, CreatedAt
)
SELECT 
  ScheduleSlotId, UserId, SlotName, SlotTime, MealType, SortOrder, CreatedAt
FROM ScheduleSlots;

DROP TABLE ScheduleSlots;
ALTER TABLE ScheduleSlots_New RENAME TO ScheduleSlots;

CREATE INDEX IF NOT EXISTS ScheduleSlots_UserId_Idx ON ScheduleSlots (UserId);
CREATE INDEX IF NOT EXISTS ScheduleSlots_UserId_SortOrder_Idx ON ScheduleSlots (UserId, SortOrder);

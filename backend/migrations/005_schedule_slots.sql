ALTER TABLE Settings ADD COLUMN StepTarget integer NOT NULL DEFAULT 8500;
ALTER TABLE Settings ADD COLUMN TodayLayout text;

ALTER TABLE MealEntries ADD COLUMN ScheduleSlotId text;

CREATE TABLE IF NOT EXISTS ScheduleSlots (
  ScheduleSlotId text PRIMARY KEY,
  UserId text NOT NULL,
  SlotName text NOT NULL,
  SlotTime text NOT NULL,
  MealType text NOT NULL,
  SortOrder integer NOT NULL DEFAULT 0,
  CreatedAt text NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT ScheduleSlots_MealType_Check CHECK (
    MealType IN ('Breakfast', 'Snack1', 'Lunch', 'Snack2', 'Dinner')
  )
);

CREATE INDEX IF NOT EXISTS ScheduleSlots_UserId_Idx ON ScheduleSlots (UserId);
CREATE INDEX IF NOT EXISTS ScheduleSlots_UserId_SortOrder_Idx ON ScheduleSlots (UserId, SortOrder);
CREATE INDEX IF NOT EXISTS MealEntries_ScheduleSlotId_Idx ON MealEntries (ScheduleSlotId);

CREATE TABLE IF NOT EXISTS Settings (
  SettingsId text PRIMARY KEY,
  DailyCalorieTarget integer NOT NULL,
  ProteinTargetMin real NOT NULL,
  ProteinTargetMax real NOT NULL,
  StepKcalFactor real NOT NULL,
  CreatedAt text NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Foods (
  FoodId text PRIMARY KEY,
  FoodName text NOT NULL,
  ServingDescription text NOT NULL,
  CaloriesPerServing integer NOT NULL,
  ProteinPerServing real NOT NULL,
  IsFavourite integer NOT NULL DEFAULT 0,
  CreatedAt text NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS Foods_FoodName_Ux ON Foods (FoodName);

CREATE TABLE IF NOT EXISTS DailyLogs (
  DailyLogId text PRIMARY KEY,
  LogDate text NOT NULL,
  Steps integer NOT NULL DEFAULT 0,
  StepKcalFactorOverride real,
  Notes text,
  CreatedAt text NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS DailyLogs_LogDate_Ux ON DailyLogs (LogDate);

CREATE TABLE IF NOT EXISTS MealEntries (
  MealEntryId text PRIMARY KEY,
  DailyLogId text NOT NULL,
  MealType text NOT NULL,
  FoodId text NOT NULL,
  Quantity real NOT NULL DEFAULT 1,
  EntryNotes text,
  SortOrder integer NOT NULL DEFAULT 0,
  CreatedAt text NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT MealEntries_MealType_Check CHECK (MealType IN ('Breakfast', 'Snack1', 'Lunch', 'Snack2', 'Dinner')),
  FOREIGN KEY (DailyLogId) REFERENCES DailyLogs(DailyLogId) ON DELETE CASCADE,
  FOREIGN KEY (FoodId) REFERENCES Foods(FoodId)
);

CREATE INDEX IF NOT EXISTS MealEntries_DailyLogId_Idx ON MealEntries (DailyLogId);

CREATE TABLE IF NOT EXISTS Suggestions (
  SuggestionId text PRIMARY KEY,
  DailyLogId text NOT NULL,
  SuggestionType text NOT NULL,
  Title text NOT NULL,
  Detail text NOT NULL,
  CreatedAt text NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (DailyLogId) REFERENCES DailyLogs(DailyLogId) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS Suggestions_DailyLogId_Idx ON Suggestions (DailyLogId);

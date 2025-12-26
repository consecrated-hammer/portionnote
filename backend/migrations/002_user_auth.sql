CREATE TABLE IF NOT EXISTS Users (
  UserId text PRIMARY KEY,
  Email text NOT NULL,
  FirstName text,
  LastName text,
  PasswordHash text,
  AuthProvider text NOT NULL,
  GoogleSubject text,
  IsAdmin integer NOT NULL DEFAULT 0,
  CreatedAt text NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT Users_AuthProvider_Check CHECK (AuthProvider IN ('Local', 'Google'))
);

CREATE UNIQUE INDEX IF NOT EXISTS Users_Email_Ux ON Users (Email);
CREATE UNIQUE INDEX IF NOT EXISTS Users_GoogleSubject_Ux ON Users (GoogleSubject) WHERE GoogleSubject IS NOT NULL;

ALTER TABLE Settings ADD COLUMN UserId text;
ALTER TABLE Foods ADD COLUMN UserId text;
ALTER TABLE DailyLogs ADD COLUMN UserId text;
ALTER TABLE Suggestions ADD COLUMN UserId text;

DROP INDEX IF EXISTS Foods_FoodName_Ux;
CREATE UNIQUE INDEX IF NOT EXISTS Foods_UserId_FoodName_Ux ON Foods (UserId, FoodName);
CREATE INDEX IF NOT EXISTS Foods_UserId_Idx ON Foods (UserId);

DROP INDEX IF EXISTS DailyLogs_LogDate_Ux;
CREATE UNIQUE INDEX IF NOT EXISTS DailyLogs_UserId_LogDate_Ux ON DailyLogs (UserId, LogDate);
CREATE INDEX IF NOT EXISTS DailyLogs_UserId_Idx ON DailyLogs (UserId);

CREATE UNIQUE INDEX IF NOT EXISTS Settings_UserId_Ux ON Settings (UserId);

CREATE INDEX IF NOT EXISTS Suggestions_UserId_Idx ON Suggestions (UserId);

CREATE TABLE IF NOT EXISTS MealTemplates (
  MealTemplateId text PRIMARY KEY,
  UserId text NOT NULL,
  TemplateName text NOT NULL,
  CreatedAt text NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (UserId) REFERENCES Users(UserId)
);

CREATE UNIQUE INDEX IF NOT EXISTS MealTemplates_UserId_Name_Ux ON MealTemplates (UserId, TemplateName);
CREATE INDEX IF NOT EXISTS MealTemplates_UserId_Idx ON MealTemplates (UserId);

CREATE TABLE IF NOT EXISTS MealTemplateItems (
  MealTemplateItemId text PRIMARY KEY,
  MealTemplateId text NOT NULL,
  FoodId text NOT NULL,
  MealType text NOT NULL,
  Quantity real NOT NULL,
  EntryNotes text,
  SortOrder integer NOT NULL DEFAULT 0,
  FOREIGN KEY (MealTemplateId) REFERENCES MealTemplates(MealTemplateId) ON DELETE CASCADE,
  FOREIGN KEY (FoodId) REFERENCES Foods(FoodId)
);

CREATE INDEX IF NOT EXISTS MealTemplateItems_Template_Idx ON MealTemplateItems (MealTemplateId);

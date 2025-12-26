-- Add entry quantity/unit to meal template items for flexible amounts
ALTER TABLE MealTemplateItems ADD COLUMN EntryQuantity real;
ALTER TABLE MealTemplateItems ADD COLUMN EntryUnit text;

UPDATE MealTemplateItems
SET EntryQuantity = Quantity
WHERE EntryQuantity IS NULL;

UPDATE MealTemplateItems
SET EntryUnit = 'serving'
WHERE EntryUnit IS NULL OR EntryUnit = '';

ALTER TABLE MealEntries ADD COLUMN EntryQuantity REAL;
ALTER TABLE MealEntries ADD COLUMN EntryUnit TEXT;
ALTER TABLE MealEntries ADD COLUMN ConversionDetail TEXT;

UPDATE MealEntries
SET EntryQuantity = Quantity,
    EntryUnit = 'serving'
WHERE EntryQuantity IS NULL;

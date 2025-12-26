-- Add BarOrder column to Settings table for drag-and-drop bar ordering
-- Default order: Calories, Protein, Steps, Fibre, Carbs, Fat, SaturatedFat, Sugar, Sodium

ALTER TABLE Settings ADD COLUMN BarOrder TEXT DEFAULT 'Calories,Protein,Steps,Fibre,Carbs,Fat,SaturatedFat,Sugar,Sodium';

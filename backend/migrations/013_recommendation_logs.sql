-- Migration 013: Add AI Recommendation Logs table
-- Tracks all AI recommendation requests and results for audit and history

CREATE TABLE IF NOT EXISTS RecommendationLogs (
    RecommendationLogId INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId TEXT NOT NULL,
    CreatedAt TEXT NOT NULL DEFAULT (datetime('now')),
    
    -- Profile snapshot at time of recommendation
    Age INTEGER NOT NULL,
    HeightCm REAL NOT NULL,
    WeightKg REAL NOT NULL,
    ActivityLevel TEXT NOT NULL,
    
    -- AI Recommendations
    DailyCalorieTarget INTEGER NOT NULL,
    ProteinTargetMin REAL NOT NULL,
    ProteinTargetMax REAL NOT NULL,
    FibreTarget REAL,
    CarbsTarget REAL,
    FatTarget REAL,
    SaturatedFatTarget REAL,
    SugarTarget REAL,
    SodiumTarget REAL,
    Explanation TEXT NOT NULL,
    
    FOREIGN KEY (UserId) REFERENCES Users(UserId) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_recommendation_logs_user_id ON RecommendationLogs(UserId);
CREATE INDEX IF NOT EXISTS idx_recommendation_logs_created_at ON RecommendationLogs(CreatedAt);

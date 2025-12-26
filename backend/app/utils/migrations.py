from pathlib import Path

from app.utils.database import ExecuteQuery, ExecuteScript, FetchAll

MigrationTableName = "SchemaMigrations"


def GetMigrationDirectory() -> Path:
    CurrentDirectory = Path(__file__).resolve().parent
    return CurrentDirectory.parent.parent / "migrations"


def EnsureMigrationTable() -> None:
    ExecuteQuery(
        f"""
        CREATE TABLE IF NOT EXISTS {MigrationTableName} (
            Name text PRIMARY KEY,
            AppliedAt text NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )


def GetAppliedMigrations() -> set[str]:
    Rows = FetchAll(f"SELECT Name FROM {MigrationTableName}")
    return {Row["Name"] for Row in Rows}


def ApplyMigration(FileName: str, SqlText: str) -> None:
    ExecuteScript(SqlText)
    ExecuteQuery(
        f"INSERT INTO {MigrationTableName} (Name) VALUES (?)",
        [FileName]
    )


def ColumnExists(TableName: str, ColumnName: str) -> bool:
    Rows = FetchAll(f"PRAGMA table_info({TableName})")
    return any(Row.get("name") == ColumnName for Row in Rows)


def AdjustMealTemplateEntriesMigration(SqlText: str) -> str:
    TargetStatement = "ALTER TABLE MealEntries ADD COLUMN MealTemplateId text;"
    return SqlText.replace(TargetStatement, "-- Skipped: MealTemplateId column already exists.")


def RunMigrations() -> None:
    EnsureMigrationTable()
    Directory = GetMigrationDirectory()
    Files = sorted(File for File in Directory.iterdir() if File.suffix == ".sql")
    Applied = GetAppliedMigrations()

    for FilePath in Files:
        if FilePath.name in Applied:
            continue
        SqlText = FilePath.read_text(encoding="utf-8")
        if FilePath.name == "015_meal_template_entries.sql" and ColumnExists("MealEntries", "MealTemplateId"):
            SqlText = AdjustMealTemplateEntriesMigration(SqlText)
        ApplyMigration(FilePath.name, SqlText)

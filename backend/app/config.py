from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    ApiPort: int = Field(default=8000, alias="API_PORT")
    WebOrigin: str = Field(default="http://localhost:5173", alias="WEB_ORIGIN")
    DatabaseFile: str = Field(default="./.data/portionnote.sqlite", alias="DATABASE_FILE")
    Environment: str = Field(default="development", alias="ENVIRONMENT")

    AdminEmail: str = Field(default="admin@portionnote.local", alias="ADMIN_EMAIL")
    AdminPassword: str = Field(default="ChangeMe123!", alias="ADMIN_PASSWORD")
    InviteCode: str = Field(default="invite-me", alias="INVITE_CODE")

    SessionSecret: str = Field(default="change-me", alias="SESSION_SECRET")
    SessionCookieName: str = Field(default="portionnote_session", alias="SESSION_COOKIE_NAME")
    SessionDays: int = Field(default=14, alias="SESSION_DAYS")

    GoogleClientId: str | None = Field(default=None, alias="GOOGLE_CLIENT_ID")
    GoogleClientSecret: str | None = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    GoogleRedirectUrl: str | None = Field(default=None, alias="GOOGLE_REDIRECT_URL")
    SeedInviteEmails: str = Field(default="", alias="SEED_INVITE_EMAILS")
    SeedGoogleUsers: str = Field(default="", alias="SEED_GOOGLE_USERS")
    SeedGoogleAdmins: str = Field(default="", alias="SEED_GOOGLE_ADMINS")
    OpenAiApiKey: str | None = Field(default=None, alias="OPENAI_API_KEY")
    OpenAiModel: str = Field(default="gpt-5-mini", alias="OPENAI_MODEL")
    OpenAiFallbackModels: str = Field(
        default="gpt-4.1,gpt-4o-mini",
        alias="OPENAI_FALLBACK_MODELS"
    )
    OpenAiBaseUrl: str = Field(
        default="https://api.openai.com/v1/chat/completions",
        alias="OPENAI_BASE_URL"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True
    )


Settings = AppSettings()

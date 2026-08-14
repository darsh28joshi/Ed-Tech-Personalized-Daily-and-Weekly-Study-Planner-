from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "mysql+asyncmy://root:password@localhost:3306/study_planner"
    
    # Constants
    EARLY_THRESHOLD: float = 0.15
    LATE_THRESHOLD: float = 0.85
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

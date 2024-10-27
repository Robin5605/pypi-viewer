from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvConfig(BaseSettings):
    """Default configuration for models that should load from .env files."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


class PyPIViewerSettings(EnvConfig, env_prefix="PYPI_VIEWER_"):
    """PyPI Viewer Settings."""

    # Number of references to distribution files to be held in memory at any time
    CACHE_SIZE: int = 4

    # Size of chunks int bytes when streaming downloads. Trades CPU cycles for memory
    CHUNK_SIZE: int = 4096


pypi_viewer_settings = PyPIViewerSettings.model_validate({})

"""Development settings."""
from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Allow the Vite dev server during local development.
CORS_ALLOW_ALL_ORIGINS = True

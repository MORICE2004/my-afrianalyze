import os

# Legacy connector tests rely on fixture mode. It is opt-in, never the default.
os.environ.setdefault("APP_ENV", "TEST")

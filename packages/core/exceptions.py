class ProductionDataViolation(Exception):
    """Raised when synthetic or mocked data leaks into a PRODUCTION environment."""
    pass

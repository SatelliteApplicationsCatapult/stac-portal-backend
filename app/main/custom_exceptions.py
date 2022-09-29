class Error(Exception):
    """Base class for other exceptions"""
    pass

class CatalogDoesNotExistError(Error):
    pass

class CatalogAlreadyExistsError(Error):
    pass
class Error(Exception):
    pass


class CatalogDoesNotExistError(Error):
    pass


class CatalogAlreadyExistsError(Error):
    pass

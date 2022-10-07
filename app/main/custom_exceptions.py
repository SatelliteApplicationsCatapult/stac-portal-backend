class Error(Exception):
    pass


class CatalogDoesNotExistError(Error):
    pass


class CatalogAlreadyExistsError(Error):
    pass


class MicroserviceIsNotAvailableError(Error):
    pass


class ConvertingTimestampError(Error):
    pass


class TemporalExtentError(Error):
    pass


class PrivateCollectionAlreadyExistsError(Error):
    pass


class InvalidCollectionPayloadError(Error):
    pass


class PrivateCollectionDoesNotExistError(Error):
    pass

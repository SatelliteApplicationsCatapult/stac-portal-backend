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


class CollectionAlreadyExistsError(Error):
    pass


class PrivateCollectionAlreadyExistsError(CollectionAlreadyExistsError):
    pass


class InvalidCollectionPayloadError(Error):
    pass


class CollectionDoesNotExistError(Error):
    pass


class PrivateCollectionDoesNotExistError(CollectionDoesNotExistError):
    pass

class ItemAlreadyExistsError(Error):
    pass
class PrivateItemAlreadyExistsError(ItemAlreadyExistsError):
    pass


class ItemDoesNotExistError(Error):
    pass

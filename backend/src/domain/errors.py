class FileExchangeError(Exception):
    """Base class for expected application errors."""


class FileNotFoundError(FileExchangeError):
    pass


class StoredFileNotFoundError(FileExchangeError):
    pass


class EmptyFileError(FileExchangeError):
    pass


class InvalidTitleError(FileExchangeError):
    pass

from abc import ABC, abstractmethod


class StorageService(ABC):
    """Provider-agnostic file storage interface. Resource rows only ever
    store the path this returns -- swapping providers later means writing a
    new implementation of this interface, not touching route/service code."""

    @abstractmethod
    def upload(self, path, file_bytes, content_type):
        """Uploads bytes to `path` in the backing store. Returns the stored path."""

    @abstractmethod
    def get_signed_url(self, path, expires_in):
        """Returns a time-limited URL for downloading the object at `path`."""

    @abstractmethod
    def delete(self, path):
        """Deletes the object at `path`."""

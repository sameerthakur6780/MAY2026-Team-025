import httpx
from storage3.exceptions import StorageApiError
from supabase import create_client

from app.services.storage_service import StorageService
from app.utils.errors import ApiError

NETWORK_ERRORS = (httpx.TimeoutException, httpx.TransportError)


class SupabaseStorageService(StorageService):
    def __init__(self, url, key, bucket):
        self._client = create_client(url, key)
        self._bucket_name = bucket

    def _bucket(self):
        return self._client.storage.from_(self._bucket_name)

    def upload(self, path, file_bytes, content_type):
        try:
            self._bucket().upload(path, file_bytes, {"content-type": content_type})
        except StorageApiError as exc:
            raise ApiError(f"File upload failed: {exc.message}", "storage_error", 502) from exc
        except NETWORK_ERRORS as exc:
            raise ApiError("File upload failed: the storage service didn't respond in time. Please try again.", "storage_timeout", 502) from exc
        return path

    def get_signed_url(self, path, expires_in):
        try:
            result = self._bucket().create_signed_url(path, expires_in)
        except StorageApiError as exc:
            raise ApiError(f"Could not generate a download link: {exc.message}", "storage_error", 502) from exc
        except NETWORK_ERRORS as exc:
            raise ApiError("Could not generate a download link: the storage service didn't respond in time.", "storage_timeout", 502) from exc
        # supabase-py returns a plain dict at runtime (not the SignedUrlResponse
        # model its own type stubs suggest) -- verified against the live API.
        return result["signedURL"]

    def delete(self, path):
        try:
            self._bucket().remove([path])
        except StorageApiError as exc:
            raise ApiError(f"File deletion failed: {exc.message}", "storage_error", 502) from exc
        except NETWORK_ERRORS as exc:
            raise ApiError("File deletion failed: the storage service didn't respond in time. Please try again.", "storage_timeout", 502) from exc

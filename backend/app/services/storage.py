from flask import current_app

from app.services.supabase_storage_service import SupabaseStorageService

_service = None


def get_storage_service():
    """Lazily builds the storage backend from app config on first use.
    Swapping providers later means changing this one construction call."""
    global _service
    if _service is None:
        _service = SupabaseStorageService(
            url=current_app.config["SUPABASE_URL"],
            key=current_app.config["SUPABASE_SERVICE_ROLE_KEY"],
            bucket=current_app.config["SUPABASE_BUCKET_NAME"],
        )
    return _service

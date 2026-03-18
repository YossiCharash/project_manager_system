"""AWS S3 file-upload and delete helpers."""
from __future__ import annotations

import logging
import uuid
from typing import BinaryIO

from backend.core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Thin wrapper around ``boto3`` for uploading and deleting files on S3.

    When AWS credentials are not configured the service degrades gracefully:
    uploads return a local relative path so the application can still run in
    development without real S3 access.
    """

    def __init__(self) -> None:
        self._client = None
        self._bucket = settings.AWS_S3_BUCKET

        if (
            settings.AWS_ACCESS_KEY_ID
            and settings.AWS_SECRET_ACCESS_KEY
            and self._bucket
        ):
            try:
                import boto3

                self._client = boto3.client(
                    "s3",
                    region_name=settings.AWS_REGION,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                )
            except ImportError:
                logger.warning(
                    "boto3 is not installed – S3 uploads will use local fallback."
                )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upload_file(
        self,
        *,
        prefix: str,
        file_obj: BinaryIO,
        filename: str,
        content_type: str | None = None,
    ) -> str:
        """Upload *file_obj* to S3 and return the public URL (or local path).

        The key is constructed as ``{prefix}/{uuid}_{filename}`` to avoid
        collisions.

        Args:
            prefix: S3 key prefix / "folder" (e.g. ``"suppliers/ABC"``).
            file_obj: File-like object opened for binary reading.
            filename: Original filename (used as the key suffix).
            content_type: MIME type forwarded to S3.  Defaults to
                ``"application/octet-stream"`` when not provided.

        Returns:
            The public URL of the uploaded file, or a relative path when S3 is
            not configured.
        """
        safe_name = filename.replace(" ", "_")
        key = f"{prefix}/{uuid.uuid4().hex}_{safe_name}"

        if self._client is None or self._bucket is None:
            # Fallback: save locally (development only)
            return self._local_fallback(key, file_obj)

        extra_args: dict = {}
        if content_type:
            extra_args["ContentType"] = content_type

        self._client.upload_fileobj(file_obj, self._bucket, key, ExtraArgs=extra_args)

        if settings.AWS_S3_BASE_URL:
            base = settings.AWS_S3_BASE_URL.rstrip("/")
            return f"{base}/{key}"

        region = settings.AWS_REGION
        return f"https://{self._bucket}.s3.{region}.amazonaws.com/{key}"

    def delete_file(self, file_path: str) -> None:
        """Delete a file from S3 by its URL or key.

        Silently ignores errors so that a missing file does not break the
        calling endpoint.
        """
        if self._client is None or self._bucket is None:
            return

        key = self._url_to_key(file_path)
        if not key:
            return

        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except Exception as exc:
            logger.warning("S3 delete failed for key %r: %s", key, exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url_to_key(self, url: str) -> str | None:
        """Extract the S3 object key from a full URL."""
        if settings.AWS_S3_BASE_URL and url.startswith(settings.AWS_S3_BASE_URL):
            return url[len(settings.AWS_S3_BASE_URL):].lstrip("/")
        if self._bucket:
            marker = f"{self._bucket}.s3"
            idx = url.find(marker)
            if idx != -1:
                after = url[idx + len(marker):]
                # strip ".amazonaws.com/<region>/" or similar
                slash = after.find("/")
                if slash != -1:
                    return after[slash + 1:]
        return None

    @staticmethod
    def _local_fallback(key: str, file_obj: BinaryIO) -> str:
        """Save *file_obj* to the local upload directory and return a relative path."""
        import os

        upload_dir = settings.FILE_UPLOAD_DIR
        local_path = os.path.join(upload_dir, key.replace("/", "_"))
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as fh:
            fh.write(file_obj.read())
        return local_path

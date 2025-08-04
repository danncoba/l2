import os
import io
from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional, Self

from dotenv import load_dotenv
from minio import Minio
from fastapi import UploadFile

load_dotenv()


class BaseUploader(ABC):

    @abstractmethod
    async def put_file(self, bucket_name: str, object_name: str, file: UploadFile) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get_file(self, bucket_name: str, object_name: str):
        raise NotImplementedError()


class UploaderType(Enum):
    MINIO = 0
    S3 = 1


class MinioUploader(BaseUploader):

    def __init__(self):
        secure_minio = True
        if os.getenv("MINIO_USE_SECURE") == "false":
            secure_minio = False
        self.client = Minio(
            os.getenv("MINIO_HOST"),  # MinIO server endpoint
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=secure_minio,  # Use secure connection (HTTPS)
        )

    async def put_file(self, bucket_name: str, object_name: str, file: UploadFile) -> str:
        """Upload file to MinIO"""
        try:
            # Ensure bucket exists
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
            
            # Upload file
            content = await file.read()
            self.client.put_object(
                bucket_name,
                object_name,
                io.BytesIO(content),
                length=len(content),
                content_type=file.content_type
            )
            return f"{bucket_name}/{object_name}"
        except Exception as e:
            raise Exception(f"Failed to upload file: {str(e)}")

    def get_file(self, bucket_name: str, object_name: str):
        """Get file from MinIO"""
        try:
            return self.client.get_object(bucket_name, object_name)
        except Exception as e:
            raise Exception(f"Failed to get file: {str(e)}")


class EmptyUploader(BaseUploader):

    async def put_file(self, bucket_name: str, object_name: str, file: UploadFile) -> str:
        return "empty_uploader"

    def get_file(self, bucket_name: str, object_name: str):
        return None


class UploaderFactory:

    def __init__(self):
        self.uploader_type: Optional[UploaderType] = None

    def set_uploader_type(self, uploader_type: UploaderType) -> Self:
        self.uploader_type = uploader_type
        return self

    def build(self) -> BaseUploader:
        if self.uploader_type == UploaderType.MINIO:
            return MinioUploader()
        else:
            return EmptyUploader()

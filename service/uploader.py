import os
from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional, Self

from dotenv import load_dotenv
from minio import Minio

load_dotenv()


class BaseUploader(ABC):

    @abstractmethod
    def put_file(self):
        raise NotImplementedError()

    @abstractmethod
    def get_file(self, file_path):
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

    def put_file(self):
        pass

    def get_file(self, file_path):
        pass


class EmptyUploader(BaseUploader):

    def put_file(self):
        pass

    def get_file(self, file_path):
        pass


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

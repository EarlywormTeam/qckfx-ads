import os
from dotenv import load_dotenv
import toolbox.services.blob_storage as blob_storage
import toolbox.services.image as image
import toolbox.services.logger as logger
import toolbox.services.llm as llm
from typing import Optional

class Services:
    _blob_storage: Optional[blob_storage.BlobStorageService] = None
    _logger: Optional[logger.Logger] = None
    _llm: Optional[llm.LLMService] = None
    _image_service: Optional[image.ImageService] = None

    def __init__(self):
        load_dotenv()  # Load environment variables from .env file

    @property
    def blob_storage(self) -> blob_storage.BlobStorageService:
        if self._blob_storage is None:
            self._blob_storage = blob_storage.BlobStorageService()
        return self._blob_storage

    @property
    def logger(self) -> logger.Logger:
        if self._logger is None:
            environment = os.getenv('ENVIRONMENT', 'development').lower()
            log_level = 'DEBUG' if environment == 'development' else 'INFO'
            self._logger = logger.create_logger(log_level)
        return self._logger

    @property
    def llm(self) -> llm.LLMService:
        if self._llm is None:
            self._llm = llm.LLMService()
        return self._llm

    @property
    def image_service(self) -> image.ImageService:
        if self._image_service is None:
            self._image_service = image.ImageService()
        return self._image_service


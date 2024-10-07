import os
from enum import Enum
from azure.storage.blob.aio import BlobServiceClient
from dotenv import load_dotenv
from azure.storage.blob import generate_container_sas, ContainerSasPermissions
from datetime import datetime, timedelta

load_dotenv()

connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

class ContainerName(Enum):
    IMAGES = "images"
    UPLOADS = "uploads"
    VERSIONS = "versions"
    PROCESSED = "processed"
    # Add other container names as needed
    # e.g., DOCUMENTS = "documents"

class BlobStorageService:
    def __init__(self):
        self.client = BlobServiceClient.from_connection_string(connection_string)
        self.default_container = ContainerName.IMAGES

    def get_blob_client(self, blob_name, container_name: ContainerName = None):
        if container_name is None:
            container_name = self.default_container
        return self.client.get_blob_client(container=container_name.value, blob=blob_name)

    async def get_blob_url(self, blob_name, container_name: ContainerName = None):
        blob_client = self.get_blob_client(blob_name, container_name)
        return blob_client.url

    async def upload_blob(self, blob_name, data, container_name: ContainerName = None):
        blob_client = self.get_blob_client(blob_name, container_name)
        await blob_client.upload_blob(data)
        return blob_name

    async def upload_blob_from_url(self, blob_name, source_url, container_name: ContainerName = None):
        blob_client = self.get_blob_client(blob_name, container_name)
        await blob_client.upload_blob_from_url(source_url)
        return blob_name

    async def download_blob_to_stream(self, blob_name, stream, container_name: ContainerName = None):
        blob_client = self.get_blob_client(blob_name, container_name)
        await blob_client.download_blob().readinto(stream)

    async def download_blob(self, blob_name, container_name: ContainerName = None):
        blob_client = self.get_blob_client(blob_name, container_name)
        blob_data = await blob_client.download_blob()
        return await blob_data.readall()

    async def delete_blob(self, blob_name, container_name: ContainerName = None):
        blob_client = self.get_blob_client(blob_name, container_name)
        await blob_client.delete_blob()

    def get_container_name(self, key: ContainerName) -> str:
        return key.value

    async def generate_container_sas(self, container_name: ContainerName = None, expiry_hours: int = 1, permission: ContainerSasPermissions = ContainerSasPermissions.READ):
        if container_name is None:
            container_name = self.default_container
        
        # Get the account name from the connection string
        account_name = self.client.account_name

        # Generate SAS token
        sas_token = generate_container_sas(
            account_name=account_name,
            container_name=container_name.value,
            account_key=self.client.credential.account_key,
            permission=permission,
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
        )

        # Construct the full URL with SAS token
        container_url = f"{self.client.url}{container_name.value}"
        container_url_with_sas = f"{container_url}?{sas_token}"
        return container_url_with_sas

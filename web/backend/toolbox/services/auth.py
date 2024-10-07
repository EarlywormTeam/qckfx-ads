import os
from typing import Dict, Any
from workos import WorkOSClient
from dotenv import load_dotenv
from models.organization import Organization

load_dotenv()

class AuthService:
    def __init__(self):
        self.workos_client = WorkOSClient(
            api_key=os.getenv('WORKOS_API_KEY'),
            client_id=os.getenv('WORKOS_CLIENT_ID')
        )

    async def create_organization(self, name: str, domain: str = None) -> Dict[str, Any]:
        """
        Create an organization using WorkOS and store it in the database.

        Args:
            name (str): The name of the organization.
            domain (str, optional): The domain of the organization.

        Returns:
            Dict[str, Any]: The created organization data.
        """
        try:
            # Create organization in WorkOS
            org_data = {
                "name": name,
            }
            if domain:
                org_data["domains"] = [
                    {
                        "domain": domain,
                        "state": "pending",
                    }
                ]
            workos_org = self.workos_client.organizations.create_organization(org_data)

            # Create and save Organization document
            org = Organization.from_workos(workos_org)
            await org.save()

            return org.model_dump()

        except Exception as e:
            # Handle any errors that occur during the process
            print(f"Error creating organization: {str(e)}")
            raise


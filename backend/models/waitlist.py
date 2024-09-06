from beanie import Document
from datetime import datetime

class WaitlistEntry(Document):
    email: str
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "waitlist"
import uuid
from datetime import datetime

class Booking:
    """
    Booking model representing a vehicle service booking.
    """

    def __init__(self, name, phone, vehicle_number, service_type, date, id=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.phone = phone
        self.vehicle_number = vehicle_number
        self.service_type = service_type
        self.date = date
        self.created_at = datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "vehicle_number": self.vehicle_number,
            "service_type": self.service_type,
            "date": self.date,
            "created_at": self.created_at
        }

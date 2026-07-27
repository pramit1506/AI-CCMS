from app.services.customer_service import CustomerService, customer_service as default_customer_service
from app.services.complaint_service import ComplaintService, complaint_service as default_complaint_service

def get_customer_service() -> CustomerService:
    return default_customer_service

def get_complaint_service() -> ComplaintService:
    return default_complaint_service

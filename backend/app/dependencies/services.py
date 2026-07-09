from app.services.hcp_service import HCPService, hcp_service as default_hcp_service
from app.services.interaction_service import InteractionService, interaction_service as default_interaction_service

def get_hcp_service() -> HCPService:
    return default_hcp_service

def get_interaction_service() -> InteractionService:
    return default_interaction_service

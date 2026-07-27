from typing import Optional
from datetime import date
import uuid
import re
from pydantic import BaseModel, Field
from app.tools.base_tool import BaseTool
from app.tools.context import ToolExecutionContext
from app.schemas.complaint import ComplaintCreate
from app.shared.enums import ComplaintStatus, ComplaintSource, Severity, Priority
from app.services.complaint_service import complaint_service
from app.repositories.customer_repository import customer_repository
from app.schemas.customer import CustomerCreate
from app.services.customer_service import customer_service

class SaveComplaintInput(BaseModel):
    customer_id: Optional[str] = Field(None, description="The UUID or business identifier of the customer/hospital.")
    customer_name: Optional[str] = Field(None, description="The name of the customer.")
    complaint_source: ComplaintSource = Field(..., description="The source of the complaint.")
    product_name: str = Field(..., description="The product name.")
    product_strength: Optional[str] = Field(None)
    batch_number: Optional[str] = Field(None)
    manufacturing_date: Optional[date] = Field(None)
    expiry_date: Optional[date] = Field(None)
    quantity_affected: Optional[str] = Field(None)
    complaint_type: Optional[str] = Field(None)
    complaint_date: date = Field(...)
    detailed_description: Optional[str] = Field(None)
    initial_severity: Optional[Severity] = Field(None)
    priority: Optional[Priority] = Field(None)
    
    risk_classification: Optional[str] = Field(None)
    root_cause_recommendation: Optional[str] = Field(None)
    capa_recommendation: Optional[str] = Field(None)
    risk_reasoning: Optional[str] = Field(None)

class SaveComplaintOutput(BaseModel):
    id: Optional[str]
    complaint_number: Optional[str]
    status: str
    message: str

class SaveComplaintTool(BaseTool):
    @property
    def name(self) -> str:
        return "save_complaint"
        
    @property
    def description(self) -> str:
        return "Create and save a new customer complaint record into the QMS ledger."
        
    @property
    def args_schema(self) -> type[BaseModel]:
        return SaveComplaintInput
        
    @property
    def return_schema(self) -> type[BaseModel]:
        return SaveComplaintOutput

    def get_required_fields(self) -> list[str]:
        return [
            "customer_name",
            "complaint_source",
            "product_name",
            "complaint_date",
        ]
        
    async def execute(self, context: ToolExecutionContext, **kwargs) -> dict:
        context.logger.info(f"[{context.request_id}] Executing SaveComplaintTool for customer {kwargs.get('customer_name')}")
        
        customer_name = (kwargs.get("customer_name") or "Unknown Customer").strip()
        customer = None
        raw_customer_id = kwargs.get("customer_id")
        if raw_customer_id:
            try:
                customer = await customer_repository.get_by_id(context.db, id=uuid.UUID(str(raw_customer_id)))
            except ValueError:
                customer = await customer_repository.get_by_customer_code(context.db, customer_code=str(raw_customer_id))

        if customer is None:
            normalized = re.sub(r"[^A-Za-z0-9]+", "-", customer_name.upper()).strip("-")[:35] or "CUSTOMER"
            customer_code = f"CUST-{normalized}"
            customer = await customer_repository.get_by_customer_code(context.db, customer_code=customer_code)

        if customer is None:
            customer = await customer_service.create(
                context.db,
                obj_in=CustomerCreate(
                    customer_code=customer_code,
                    customer_name=customer_name,
                ),
            )
        
        complaint_number = f"CMP-{uuid.uuid4().hex[:8].upper()}"
        
        create_schema = ComplaintCreate(
            complaint_number=complaint_number,
            customer_id=customer.id,
            complaint_source=kwargs["complaint_source"],
            product_name=kwargs["product_name"],
            product_strength=kwargs.get("product_strength"),
            batch_number=kwargs.get("batch_number"),
            manufacturing_date=kwargs.get("manufacturing_date"),
            expiry_date=kwargs.get("expiry_date"),
            quantity_affected=kwargs.get("quantity_affected"),
            complaint_type=kwargs.get("complaint_type"),
            complaint_date=kwargs["complaint_date"],
            detailed_description=kwargs.get("detailed_description"),
            initial_severity=kwargs.get("initial_severity"),
            priority=kwargs.get("priority"),
            risk_classification=kwargs.get("risk_classification"),
            root_cause_recommendation=kwargs.get("root_cause_recommendation"),
            capa_recommendation=kwargs.get("capa_recommendation"),
            risk_reasoning=kwargs.get("risk_reasoning"),
            status=ComplaintStatus.PENDING_TRIAGE
        )
        
        complaint = await complaint_service.create(context.db, obj_in=create_schema)
        
        return {
            "id": str(complaint.id),
            "complaint_number": complaint.complaint_number,
            "status": complaint.status.value,
            "customer_id": str(customer.id),
            "message": "Complaint successfully logged to the QMS ledger."
        }

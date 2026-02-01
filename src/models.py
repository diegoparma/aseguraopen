"""
Data models for insurance policies
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json

@dataclass
class Policy:
    """Policy state and metadata"""
    id: str
    state: str  # intake, exploration, quotation, acceptance, emission, finalization, closed
    intention: bool = False  # Si el cliente tiene intención de comprar
    insurance_type: Optional[str] = None  # auto, moto
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class ClientData:
    """Client information collected during intake"""
    id: str
    policy_id: str
    name: str
    email: str
    phone: str
    created_at: Optional[datetime] = None

@dataclass
class ExplorationData:
    """Exploration and validation data"""
    id: str
    policy_id: str
    validation_status: str  # pending, suspicious, validated
    anomalies: Optional[dict] = None
    created_at: Optional[datetime] = None
    
    def set_anomalies(self, anomalies: dict):
        self.anomalies = anomalies

@dataclass
class VehicleData:
    """Vehicle information for quotation"""
    id: str
    policy_id: str
    plate: str
    make: str
    model: str
    year: int
    engine_number: Optional[str] = None
    chassis_number: Optional[str] = None
    engine_displacement: Optional[int] = None
    created_at: Optional[datetime] = None

@dataclass
class QuotationData:
    """Quotation information"""
    id: str
    policy_id: str
    vehicle_id: Optional[str] = None
    coverage_type: Optional[str] = None
    coverage_level: Optional[str] = None
    monthly_premium: Optional[float] = None
    annual_premium: Optional[float] = None
    deductible: Optional[float] = None
    risk_level: Optional[str] = None
    selected: bool = False
    created_at: Optional[datetime] = None

@dataclass
class QuotationTemplate:
    """Base quotation template"""
    id: str
    insurance_type: str
    coverage_type: str
    coverage_level: str
    base_monthly_premium: float
    deductible: float
    created_at: Optional[datetime] = None

@dataclass
class StateTransition:
    """Audit trail of state changes"""
    id: str
    policy_id: str
    from_state: str
    to_state: str
    reason: str
    agent: str
    created_at: Optional[datetime] = None

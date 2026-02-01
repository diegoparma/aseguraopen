"""
Database repository for policies and related data
"""
import uuid
from datetime import datetime
from src.db.connection import DatabaseConnection
from src.models import Policy, ClientData, ExplorationData, VehicleData, QuotationData, QuotationTemplate, StateTransition

class PolicyRepository:
    """Manage policy data in database"""
    
    db = DatabaseConnection
    
    @classmethod
    def create_policy(cls, initial_state: str = "intake") -> Policy:
        """Create a new policy"""
        policy_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        query = """
            INSERT INTO policies (id, state, intention, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """
        
        cls.db.execute_update(query, (policy_id, initial_state, False, now, now))
        
        return Policy(
            id=policy_id,
            state=initial_state,
            intention=False,
            created_at=now,
            updated_at=now
        )
    
    @classmethod
    def get_policy(cls, policy_id: str) -> Policy:
        """Get policy by ID"""
        query = "SELECT id, state, intention, insurance_type, created_at, updated_at FROM policies WHERE id = ?"
        result = cls.db.execute_query(query, (policy_id,))
        
        if result:
            row = result[0]
            return Policy(
                id=row[0],
                state=row[1],
                intention=bool(row[2]),
                insurance_type=row[3],
                created_at=row[4],
                updated_at=row[5]
            )
        return None
    
    @classmethod
    def update_policy_state(cls, policy_id: str, new_state: str, reason: str, agent: str):
        """Update policy state and create transition record"""
        policy = cls.get_policy(policy_id)
        
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")
        
        old_state = policy.state
        now = datetime.now().isoformat()
        
        # Update policy state
        query = "UPDATE policies SET state = ?, updated_at = ? WHERE id = ?"
        cls.db.execute_update(query, (new_state, now, policy_id))
        
        # Record transition
        transition_id = str(uuid.uuid4())
        transition_query = """
            INSERT INTO state_transitions (id, policy_id, from_state, to_state, reason, agent, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cls.db.execute_update(
            transition_query,
            (transition_id, policy_id, old_state, new_state, reason, agent, now)
        )
        
        return StateTransition(
            id=transition_id,
            policy_id=policy_id,
            from_state=old_state,
            to_state=new_state,
            reason=reason,
            agent=agent,
            created_at=now
        )
    
    @classmethod
    def save_client_data(cls, policy_id: str, name: str, email: str, phone: str) -> ClientData:
        """Save client data from intake"""
        client_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        query = """
            INSERT INTO client_data (id, policy_id, name, email, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        cls.db.execute_update(query, (client_id, policy_id, name, email, phone, now))
        
        return ClientData(
            id=client_id,
            policy_id=policy_id,
            name=name,
            email=email,
            phone=phone,
            created_at=now
        )
    
    @classmethod
    def get_client_data(cls, policy_id: str) -> ClientData:
        """Get client data for a policy"""
        query = "SELECT id, policy_id, name, email, phone, created_at FROM client_data WHERE policy_id = ?"
        result = cls.db.execute_query(query, (policy_id,))
        
        if result:
            row = result[0]
            return ClientData(
                id=row[0],
                policy_id=row[1],
                name=row[2],
                email=row[3],
                phone=row[4],
                created_at=row[5]
            )
        return None
    
    @classmethod
    def update_client_data_partial(cls, policy_id: str, **fields) -> ClientData:
        """Update specific client data fields (name, email, phone) - saves partially"""
        client_data = cls.get_client_data(policy_id)
        
        if not client_data:
            # If no client data exists, create with provided fields
            name = fields.get('name')
            email = fields.get('email')
            phone = fields.get('phone')
            
            client_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            query = """
                INSERT INTO client_data (id, policy_id, name, email, phone, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            cls.db.execute_update(query, (client_id, policy_id, name, email, phone, now))
            
            return cls.get_client_data(policy_id)
        
        # Update existing record with provided fields
        update_parts = []
        update_values = []
        
        if 'name' in fields:
            update_parts.append("name = ?")
            update_values.append(fields['name'])
        
        if 'email' in fields:
            update_parts.append("email = ?")
            update_values.append(fields['email'])
        
        if 'phone' in fields:
            update_parts.append("phone = ?")
            update_values.append(fields['phone'])
        
        if not update_parts:
            return client_data
        
        update_values.append(policy_id)
        query = f"UPDATE client_data SET {', '.join(update_parts)} WHERE policy_id = ?"
        cls.db.execute_update(query, tuple(update_values))
        
        return cls.get_client_data(policy_id)
    
    @classmethod
    def save_exploration_data(cls, policy_id: str, validation_status: str, anomalies: dict = None) -> ExplorationData:
        """Save exploration/validation data"""
        exploration_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        anomalies_json = None
        
        if anomalies:
            import json
            anomalies_json = json.dumps(anomalies)
        
        query = """
            INSERT INTO exploration_data (id, policy_id, validation_status, anomalies, created_at)
            VALUES (?, ?, ?, ?, ?)
        """
        
        cls.db.execute_update(query, (exploration_id, policy_id, validation_status, anomalies_json, now))
        
        return ExplorationData(
            id=exploration_id,
            policy_id=policy_id,
            validation_status=validation_status,
            anomalies=anomalies,
            created_at=now
        )
    
    @classmethod
    def get_exploration_data(cls, policy_id: str) -> ExplorationData:
        """Get exploration data for a policy"""
        query = "SELECT id, policy_id, validation_status, anomalies, created_at FROM exploration_data WHERE policy_id = ?"
        result = cls.db.execute_query(query, (policy_id,))
        
        if result:
            import json
            row = result[0]
            anomalies = None
            if row[3]:
                anomalies = json.loads(row[3])
            
            return ExplorationData(
                id=row[0],
                policy_id=row[1],
                validation_status=row[2],
                anomalies=anomalies,
                created_at=row[4]
            )
        return None
    
    @classmethod
    def save_quotation_data(cls, policy_id: str, amount: float, risk_level: str, premium: float) -> QuotationData:
        """Save quotation data"""
        quotation_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        query = """
            INSERT INTO quotation_data (id, policy_id, amount, risk_level, premium, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        cls.db.execute_update(query, (quotation_id, policy_id, amount, risk_level, premium, now))
        
        return QuotationData(
            id=quotation_id,
            policy_id=policy_id,
            amount=amount,
            risk_level=risk_level,
            premium=premium,
            created_at=now
        )
    
    @classmethod
    def get_quotation_data(cls, policy_id: str) -> QuotationData:
        """Get quotation data for a policy"""
        query = "SELECT id, policy_id, amount, risk_level, premium, created_at FROM quotation_data WHERE policy_id = ?"
        result = cls.db.execute_query(query, (policy_id,))
        
        if result:
            row = result[0]
            return QuotationData(
                id=row[0],
                policy_id=row[1],
                amount=row[2],
                risk_level=row[3],
                premium=row[4],
                created_at=row[5]
            )
        return None
    
    @classmethod
    def set_intention(cls, policy_id: str, insurance_type: str) -> Policy:
        """Set intention flag and insurance type when customer shows interest"""
        policy = cls.get_policy(policy_id)
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")
        
        now = datetime.now().isoformat()
        query = "UPDATE policies SET intention = ?, insurance_type = ?, updated_at = ? WHERE id = ?"
        cls.db.execute_update(query, (True, insurance_type, now, policy_id))
        
        return cls.get_policy(policy_id)
    
    @classmethod
    def validate_client_data(cls, name: str, email: str, phone: str) -> dict:
        """Validate client data format"""
        errors = []
        
        if not name or len(name.strip()) < 2:
            errors.append("Nombre inválido: debe tener al menos 2 caracteres")
        
        if not email or "@" not in email or "." not in email:
            errors.append("Email inválido: debe ser un email válido")
        
        if not phone or len(phone.replace(" ", "").replace("+", "").replace("-", "")) < 8:
            errors.append("Teléfono inválido: debe tener al menos 8 dígitos")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "data": {
                "name": name.strip(),
                "email": email.strip(),
                "phone": phone.strip()
            }
        }
    
    @classmethod
    def get_all_policies(cls) -> list:
        """Get all policies"""
        query = "SELECT id, state, intention, insurance_type, created_at, updated_at FROM policies ORDER BY created_at DESC"
        results = cls.db.execute_query(query)
        
        policies = []
        if results:
            for row in results:
                policies.append({
                    "id": row[0] if isinstance(row, tuple) else row["id"],
                    "state": row[1] if isinstance(row, tuple) else row["state"],
                    "intention": bool(row[2] if isinstance(row, tuple) else row["intention"]),
                    "insurance_type": row[3] if isinstance(row, tuple) else row["insurance_type"],
                    "created_at": row[4] if isinstance(row, tuple) else row["created_at"],
                    "updated_at": row[5] if isinstance(row, tuple) else row["updated_at"]
                })
        return policies
    
    @classmethod
    def get_all_client_data(cls) -> list:
        """Get all client data"""
        query = "SELECT id, policy_id, name, email, phone, created_at FROM client_data ORDER BY created_at DESC"
        results = cls.db.execute_query(query)
        
        clients = []
        if results:
            for row in results:
                clients.append({
                    "id": row[0] if isinstance(row, tuple) else row["id"],
                    "policy_id": row[1] if isinstance(row, tuple) else row["policy_id"],
                    "name": row[2] if isinstance(row, tuple) else row["name"],
                    "email": row[3] if isinstance(row, tuple) else row["email"],
                    "phone": row[4] if isinstance(row, tuple) else row["phone"],
                    "created_at": row[5] if isinstance(row, tuple) else row["created_at"]
                })
        return clients
    
    @classmethod
    def get_all_state_transitions(cls) -> list:
        """Get all state transitions"""
        query = "SELECT id, policy_id, from_state, to_state, reason, agent, created_at FROM state_transitions ORDER BY created_at DESC"
        results = cls.db.execute_query(query)
        
        transitions = []
        if results:
            for row in results:
                transitions.append({
                    "id": row[0] if isinstance(row, tuple) else row["id"],
                    "policy_id": row[1] if isinstance(row, tuple) else row["policy_id"],
                    "from_state": row[2] if isinstance(row, tuple) else row["from_state"],
                    "to_state": row[3] if isinstance(row, tuple) else row["to_state"],
                    "reason": row[4] if isinstance(row, tuple) else row["reason"],
                    "agent": row[5] if isinstance(row, tuple) else row["agent"],
                    "created_at": row[6] if isinstance(row, tuple) else row["created_at"]
                })
        return transitions
    
    @classmethod
    def get_all_vehicle_data(cls) -> list:
        """Get all vehicle data"""
        query = "SELECT id, policy_id, plate, make, model, year, engine_number, chassis_number, engine_displacement FROM vehicles ORDER BY created_at DESC"
        results = cls.db.execute_query(query)
        
        vehicles = []
        if results:
            for row in results:
                vehicles.append({
                    "id": row[0] if isinstance(row, tuple) else row["id"],
                    "policy_id": row[1] if isinstance(row, tuple) else row["policy_id"],
                    "plate": row[2] if isinstance(row, tuple) else row["plate"],
                    "make": row[3] if isinstance(row, tuple) else row["make"],
                    "model": row[4] if isinstance(row, tuple) else row["model"],
                    "year": row[5] if isinstance(row, tuple) else row["year"],
                    "engine_number": row[6] if isinstance(row, tuple) else row["engine_number"],
                    "chassis_number": row[7] if isinstance(row, tuple) else row["chassis_number"],
                    "engine_displacement": row[8] if isinstance(row, tuple) else row["engine_displacement"]
                })
        return vehicles
    
    @classmethod
    def get_all_quotations(cls) -> list:
        """Get all quotations"""
        query = "SELECT id, policy_id, coverage_type, coverage_level, monthly_premium, annual_premium, deductible FROM quotations ORDER BY created_at DESC"
        results = cls.db.execute_query(query)
        
        quotations = []
        if results:
            for row in results:
                quotations.append({
                    "id": row[0] if isinstance(row, tuple) else row["id"],
                    "policy_id": row[1] if isinstance(row, tuple) else row["policy_id"],
                    "coverage_type": row[2] if isinstance(row, tuple) else row["coverage_type"],
                    "coverage_level": row[3] if isinstance(row, tuple) else row["coverage_level"],
                    "monthly_premium": row[4] if isinstance(row, tuple) else row["monthly_premium"],
                    "annual_premium": row[5] if isinstance(row, tuple) else row["annual_premium"],
                    "deductible": row[6] if isinstance(row, tuple) else row["deductible"]
                })
        return quotations
    
    @classmethod
    def save_vehicle_data(cls, policy_id: str, plate: str, make: str, model: str, year: int, 
                         engine_number: str = None, chassis_number: str = None, 
                         engine_displacement: int = None) -> VehicleData:
        """Save vehicle data for quotation"""
        vehicle_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        query = """
            INSERT INTO vehicle_data (id, policy_id, plate, make, model, year, engine_number, chassis_number, engine_displacement, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cls.db.execute_update(query, (vehicle_id, policy_id, plate, make, model, year, 
                                     engine_number, chassis_number, engine_displacement, now))
        
        return VehicleData(
            id=vehicle_id,
            policy_id=policy_id,
            plate=plate,
            make=make,
            model=model,
            year=year,
            engine_number=engine_number,
            chassis_number=chassis_number,
            engine_displacement=engine_displacement,
            created_at=now
        )
    
    @classmethod
    def get_vehicle_data(cls, policy_id: str) -> VehicleData:
        """Get vehicle data for a policy"""
        query = """SELECT id, policy_id, plate, make, model, year, engine_number, chassis_number, engine_displacement, created_at 
                   FROM vehicle_data WHERE policy_id = ?"""
        result = cls.db.execute_query(query, (policy_id,))
        
        if result:
            row = result[0]
            return VehicleData(
                id=row[0] if isinstance(row, tuple) else row["id"],
                policy_id=row[1] if isinstance(row, tuple) else row["policy_id"],
                plate=row[2] if isinstance(row, tuple) else row["plate"],
                make=row[3] if isinstance(row, tuple) else row["make"],
                model=row[4] if isinstance(row, tuple) else row["model"],
                year=row[5] if isinstance(row, tuple) else row["year"],
                engine_number=row[6] if isinstance(row, tuple) else row["engine_number"],
                chassis_number=row[7] if isinstance(row, tuple) else row["chassis_number"],
                engine_displacement=row[8] if isinstance(row, tuple) else row["engine_displacement"],
                created_at=row[9] if isinstance(row, tuple) else row["created_at"]
            )
        return None
    
    @classmethod
    def generate_quotations(cls, policy_id: str, insurance_type: str) -> list:
        """Generate quotations based on insurance type"""
        quotations = []
        vehicle = cls.get_vehicle_data(policy_id)
        
        if not vehicle:
            return quotations
        
        # Get base templates for this insurance type
        query = """SELECT id, insurance_type, coverage_type, coverage_level, base_monthly_premium, deductible 
                   FROM quotation_templates WHERE insurance_type = ? ORDER BY base_monthly_premium"""
        results = cls.db.execute_query(query, (insurance_type,))
        
        if not results:
            return quotations
        
        for template in results:
            template_id = template[0] if isinstance(template, tuple) else template["id"]
            coverage_type = template[2] if isinstance(template, tuple) else template["coverage_type"]
            coverage_level = template[3] if isinstance(template, tuple) else template["coverage_level"]
            base_premium = template[4] if isinstance(template, tuple) else template["base_monthly_premium"]
            deductible = template[5] if isinstance(template, tuple) else template["deductible"]
            
            # Calculate monthly premium with adjustments
            risk_factor = 1.0  # Can be adjusted based on vehicle/client
            monthly_premium = base_premium * risk_factor
            annual_premium = monthly_premium * 12
            
            quotation_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            query = """
                INSERT INTO quotation_data (id, policy_id, vehicle_id, coverage_type, coverage_level, 
                                           monthly_premium, annual_premium, deductible, risk_level, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cls.db.execute_update(query, (quotation_id, policy_id, vehicle.id, coverage_type, coverage_level,
                                         monthly_premium, annual_premium, deductible, "medium", now))
            
            quotations.append({
                "id": quotation_id,
                "coverage_type": coverage_type,
                "coverage_level": coverage_level,
                "monthly_premium": monthly_premium,
                "annual_premium": annual_premium,
                "deductible": deductible
            })
        
        return quotations
    
    @classmethod
    def get_quotations(cls, policy_id: str) -> list:
        """Get all quotations for a policy"""
        query = """SELECT id, coverage_type, coverage_level, monthly_premium, annual_premium, deductible, selected 
                   FROM quotation_data WHERE policy_id = ? ORDER BY monthly_premium"""
        results = cls.db.execute_query(query, (policy_id,))
        
        quotations = []
        if results:
            for row in results:
                quotations.append({
                    "id": row[0] if isinstance(row, tuple) else row["id"],
                    "coverage_type": row[1] if isinstance(row, tuple) else row["coverage_type"],
                    "coverage_level": row[2] if isinstance(row, tuple) else row["coverage_level"],
                    "monthly_premium": row[3] if isinstance(row, tuple) else row["monthly_premium"],
                    "annual_premium": row[4] if isinstance(row, tuple) else row["annual_premium"],
                    "deductible": row[5] if isinstance(row, tuple) else row["deductible"],
                    "selected": bool(row[6] if isinstance(row, tuple) else row["selected"])
                })
        return quotations
    
    @classmethod
    def seed_quotation_templates(cls):
        """Seed database with base quotation templates"""
        templates = [
            # Auto insurance - different coverage levels
            ("auto", "Responsabilidad Civil", "Básica", 45.00, 500.0),
            ("auto", "Responsabilidad Civil", "Intermedia", 65.00, 250.0),
            ("auto", "Todo Riesgo", "Básica", 95.00, 1000.0),
            ("auto", "Todo Riesgo", "Premium", 145.00, 0.0),
            # Moto insurance
            ("moto", "Responsabilidad Civil", "Básica", 25.00, 1000.0),
            ("moto", "Responsabilidad Civil", "Intermedia", 40.00, 500.0),
            ("moto", "Todo Riesgo", "Básica", 60.00, 1500.0),
            ("moto", "Todo Riesgo", "Premium", 95.00, 0.0),
        ]
        
        for insurance_type, coverage_type, coverage_level, premium, deductible in templates:
            # Check if already exists
            check_query = """SELECT id FROM quotation_templates 
                           WHERE insurance_type = ? AND coverage_type = ? AND coverage_level = ?"""
            existing = cls.db.execute_query(check_query, (insurance_type, coverage_type, coverage_level))
            
            if not existing:
                template_id = str(uuid.uuid4())
                now = datetime.now().isoformat()
                
                insert_query = """
                    INSERT INTO quotation_templates (id, insurance_type, coverage_type, coverage_level, base_monthly_premium, deductible, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                
                cls.db.execute_update(insert_query, (template_id, insurance_type, coverage_type, coverage_level, premium, deductible, now))    
    # ==================== Session Management (Persistent) ====================
    
    @classmethod
    def create_session(cls, session_id: str, policy_id: str) -> dict:
        """Create a new persistent session"""
        now = datetime.now().isoformat()
        
        query = """
            INSERT OR REPLACE INTO sessions (session_id, policy_id, messages, context_built, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        cls.db.execute_update(query, (session_id, policy_id, "[]", 0, now, now))
        
        return {
            "session_id": session_id,
            "policy_id": policy_id,
            "messages": [],
            "context_built": False
        }
    
    @classmethod
    def get_session(cls, session_id: str) -> dict or None:
        """Get session by ID"""
        query = "SELECT session_id, policy_id, messages, context_built FROM sessions WHERE session_id = ?"
        result = cls.db.execute_query(query, (session_id,))
        
        if result:
            row = result[0]
            import json
            session_id_val = row[0] if isinstance(row, tuple) else row["session_id"]
            policy_id_val = row[1] if isinstance(row, tuple) else row["policy_id"]
            messages_json = row[2] if isinstance(row, tuple) else row["messages"]
            context_built_val = row[3] if isinstance(row, tuple) else row["context_built"]
            
            # Parse JSON messages
            try:
                messages = json.loads(messages_json) if isinstance(messages_json, str) else messages_json
            except:
                messages = []
            
            return {
                "session_id": session_id_val,
                "policy_id": policy_id_val,
                "messages": messages,
                "context_built": bool(context_built_val)
            }
        
        return None
    
    @classmethod
    def update_session_messages(cls, session_id: str, messages: list):
        """Update session messages"""
        import json
        
        now = datetime.now().isoformat()
        messages_json = json.dumps(messages)
        
        query = """
            UPDATE sessions 
            SET messages = ?, updated_at = ?
            WHERE session_id = ?
        """
        
        cls.db.execute_update(query, (messages_json, now, session_id))
    
    @classmethod
    def update_session_context_built(cls, session_id: str, context_built: bool):
        """Mark that initial context has been built"""
        now = datetime.now().isoformat()
        
        query = """
            UPDATE sessions 
            SET context_built = ?, updated_at = ?
            WHERE session_id = ?
        """
        
        cls.db.execute_update(query, (1 if context_built else 0, now, session_id))
    
    @classmethod
    def delete_session(cls, session_id: str):
        """Delete a session"""
        query = "DELETE FROM sessions WHERE session_id = ?"
        cls.db.execute_update(query, (session_id,))
    
    @classmethod
    def get_all_sessions(cls) -> list:
        """Get all sessions"""
        query = "SELECT session_id, policy_id, messages, context_built, created_at, updated_at FROM sessions ORDER BY created_at DESC"
        results = cls.db.execute_query(query, ())
        
        import json
        sessions = []
        if results:
            for row in results:
                session_id_val = row[0] if isinstance(row, tuple) else row["session_id"]
                policy_id_val = row[1] if isinstance(row, tuple) else row["policy_id"]
                messages_json = row[2] if isinstance(row, tuple) else row["messages"]
                context_built_val = row[3] if isinstance(row, tuple) else row["context_built"]
                created_at_val = row[4] if isinstance(row, tuple) else row["created_at"]
                updated_at_val = row[5] if isinstance(row, tuple) else row["updated_at"]
                
                try:
                    messages = json.loads(messages_json) if isinstance(messages_json, str) else messages_json
                except:
                    messages = []
                
                sessions.append({
                    "session_id": session_id_val,
                    "policy_id": policy_id_val,
                    "messages_count": len(messages),
                    "context_built": bool(context_built_val),
                    "created_at": created_at_val,
                    "updated_at": updated_at_val
                })
        
        return sessions
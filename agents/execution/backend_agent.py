import asyncio
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, MessagePriority


@dataclass
class APIEndpoint:
    """API endpoint specification"""
    endpoint_id: str
    path: str
    method: str
    request_schema: Dict
    response_schema: Dict
    auth_required: bool
    rate_limit: Optional[int]
    implementation: str


@dataclass
class DatabaseSchema:
    """Database schema specification"""
    schema_id: str
    tables: List[Dict]
    relationships: List[Dict]
    indexes: List[Dict]
    migrations: List[str]


class BackendAgent(BaseAgent):
    """
    Ord-FullStack-B: Backend Lead Agent
    
    The infrastructure architect who builds robust APIs
    and manages data with precision. FullStack-B ensures
    everything scales beautifully.
    """
    
    def __init__(self, orchestrator=None, memory_manager=None):
        super().__init__(
            agent_id="ord-fullstack-b",
            name="Ord-FullStack-B",
            role="Backend Lead",
            layer=3,
            orchestrator=orchestrator,
            memory_manager=memory_manager
        )
        
        self.apis: Dict[str, APIEndpoint] = {}
        self.schemas: Dict[str, DatabaseSchema] = {}
        
        # Tech stack
        self.tech_stack = {
            "runtime": "Node.js / Python",
            "framework": "FastAPI / Express",
            "database": "PostgreSQL / Supabase",
            "cache": "Redis",
            "queue": "Bull / Celery",
            "deployment": "Docker / Vercel / AWS"
        }
        
        self.logger.info("🔧 Ord-FullStack-B initialized | Infrastructure Architect")
    
    def get_capabilities(self) -> List[str]:
        return [
            "api_design",
            "api_implementation",
            "database_design",
            "schema_migration",
            "devops",
            "deployment",
            "performance_optimization",
            "security_hardening",
            "infrastructure_management"
        ]
    
    async def design_api(self, spec: Dict) -> APIEndpoint:
        """Design API endpoint from specification"""
        endpoint_id = f"api-{int(time.time())}"
        
        path = spec.get("path", "/api/resource")
        method = spec.get("method", "GET")
        
        endpoint = APIEndpoint(
            endpoint_id=endpoint_id,
            path=path,
            method=method,
            request_schema=spec.get("request_schema", {}),
            response_schema=spec.get("response_schema", {}),
            auth_required=spec.get("auth_required", True),
            rate_limit=spec.get("rate_limit"),
            implementation=self._generate_api_implementation(path, method, spec)
        )
        
        self.apis[endpoint_id] = endpoint
        
        return endpoint
    
    def _generate_api_implementation(self, path: str, method: str, spec: Dict) -> str:
        """Generate API endpoint implementation"""
        resource = path.split("/")[-1] if "/" in path else "resource"
        
        if method == "GET":
            return f'''
@app.get("{path}")
async def get_{resource}(
    current_user: User = Depends(get_current_user)
):
    """Get {resource} list"""
    try:
        data = await db.query("SELECT * FROM {resource}")
        return {{"data": data, "status": "success"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''
        elif method == "POST":
            return f'''
@app.post("{path}")
async def create_{resource}(
    data: {resource.title()}Create,
    current_user: User = Depends(get_current_user)
):
    """Create new {resource}"""
    try:
        result = await db.insert("{resource}", data.dict())
        return {{"data": result, "status": "created"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''
        
        return "# Implementation pending"
    
    async def design_database(self, requirements: Dict) -> DatabaseSchema:
        """Design database schema from requirements"""
        schema_id = f"schema-{int(time.time())}"
        
        tables = [
            {
                "name": "users",
                "columns": [
                    {"name": "id", "type": "uuid", "primary": True},
                    {"name": "email", "type": "varchar", "unique": True},
                    {"name": "created_at", "type": "timestamp", "default": "now()"}
                ]
            },
            {
                "name": "projects",
                "columns": [
                    {"name": "id", "type": "uuid", "primary": True},
                    {"name": "name", "type": "varchar"},
                    {"name": "owner_id", "type": "uuid", "foreign": "users.id"},
                    {"name": "status", "type": "varchar"},
                    {"name": "created_at", "type": "timestamp"}
                ]
            }
        ]
        
        schema = DatabaseSchema(
            schema_id=schema_id,
            tables=tables,
            relationships=[
                {"from": "projects.owner_id", "to": "users.id", "type": "many-to-one"}
            ],
            indexes=[
                {"table": "users", "columns": ["email"]},
                {"table": "projects", "columns": ["owner_id", "status"]}
            ],
            migrations=[
                f"CREATE TABLE users (...)",
                f"CREATE TABLE projects (...)"
            ]
        )
        
        self.schemas[schema_id] = schema
        
        return schema
    
    async def generate_variation_backend(self, task: Dict) -> Dict:
        """Generate backend code for 20-variation experiment"""
        variation_id = task.get("variation_id")
        
        schema = await self.design_database({})
        
        api_code = f'''
# Variation {variation_id} - Backend API
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine

app = FastAPI(title="{task.get("project_name", "Project")}")

# Database setup
engine = create_engine(DATABASE_URL)

{chr(10).join([self._generate_api_implementation(f"/api/{{t['name']}}", "GET", {{}}) for t in schema.tables])}
'''
        
        return {
            "variation_id": variation_id,
            "api_code": api_code,
            "schema": schema,
            "files": ["main.py", "models.py", "schemas.py", "database.py"]
        }
    
    async def create_deployment_config(self, project_id: str) -> Dict:
        """Create deployment configuration"""
        dockerfile = '''
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
'''
        
        vercel_json = '''
{{
  "version": 2,
  "builds": [
    {{ "src": "package.json", "use": "@vercel/node" }}
  ],
  "routes": [
    {{ "src": "/(.*)", "dest": "/" }}
  ]
}}
'''
        
        return {
            "project_id": project_id,
            "dockerfile": dockerfile,
            "vercel_json": vercel_json,
            "environment_variables": [
                "DATABASE_URL",
                "REDIS_URL",
                "API_KEY"
            ]
        }
    
    async def process_task(self, task: Dict) -> Dict[str, Any]:
        """Process Backend-specific tasks"""
        task_type = task.get("type", "unknown")
        
        if task_type == "design_api":
            endpoint = await self.design_api(task.get("spec", {}))
            return {"endpoint_id": endpoint.endpoint_id, "implementation": endpoint.implementation}
        
        elif task_type == "design_database":
            schema = await self.design_database(task.get("requirements", {}))
            return {"schema_id": schema.schema_id, "tables": [t["name"] for t in schema.tables]}
        
        elif task_type == "20_variation_backend":
            return await self.generate_variation_backend(task)
        
        elif task_type == "create_deployment_config":
            return await self.create_deployment_config(task.get("project_id"))
        
        elif task_type == "get_tech_stack":
            return self.tech_stack
        
        return {"error": f"Unknown task type: {task_type}"}

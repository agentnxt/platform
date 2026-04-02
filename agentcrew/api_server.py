"""Lightweight FastAPI wrapper around CrewAI-Studio db_utils for MCP integration."""
import sys
import json
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Any

# Add the app directory to path so we can import db_utils
sys.path.insert(0, '/app/app')
sys.path.insert(0, '/app')

# Set required env vars before importing
os.environ.setdefault('CREWAI_STORAGE_DIR', '/app/data')

app = FastAPI(title="AgentCrew API", version="1.0.0")


def safe_import():
    """Lazily import db_utils to avoid startup issues."""
    import db_utils
    return db_utils


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/agents")
def list_agents():
    db = safe_import()
    agents = db.load_agents()
    return [{"id": a.id, "role": a.role, "goal": a.goal, "backstory": a.backstory} for a in agents]


@app.get("/tasks")
def list_tasks():
    db = safe_import()
    tasks = db.load_tasks()
    return [{"id": t.id, "description": t.description, "expected_output": t.expected_output} for t in tasks]


@app.get("/crews")
def list_crews():
    db = safe_import()
    crews = db.load_crews()
    return [{"id": c.id, "name": c.name, "process": c.process, "verbose": c.verbose} for c in crews]


@app.get("/tools")
def list_tools():
    db = safe_import()
    tools = db.load_tools()
    return [{"id": t.id, "name": t.name, "description": getattr(t, 'description', '')} for t in tools]


@app.get("/results")
def list_results():
    db = safe_import()
    results = db.load_results()
    return [{"id": r.id, "status": getattr(r, 'status', ''), "result": getattr(r, 'result', '')} for r in results]


class AgentCreate(BaseModel):
    role: str
    goal: str
    backstory: str
    llm: Optional[str] = None
    allow_delegation: bool = False
    verbose: bool = True


@app.post("/agents")
def create_agent(agent: AgentCreate):
    db = safe_import()
    from my_agent import MyAgent
    import uuid
    a = MyAgent(
        id=str(uuid.uuid4()),
        role=agent.role,
        goal=agent.goal,
        backstory=agent.backstory,
        llm=agent.llm,
        allow_delegation=agent.allow_delegation,
        verbose=agent.verbose,
    )
    db.save_agent(a)
    return {"id": a.id, "role": a.role}


class TaskCreate(BaseModel):
    description: str
    expected_output: str
    agent_id: Optional[str] = None


@app.post("/tasks")
def create_task(task: TaskCreate):
    db = safe_import()
    from my_task import MyTask
    import uuid
    t = MyTask(
        id=str(uuid.uuid4()),
        description=task.description,
        expected_output=task.expected_output,
    )
    db.save_task(t)
    return {"id": t.id, "description": t.description}


@app.delete("/agents/{agent_id}")
def delete_agent(agent_id: str):
    db = safe_import()
    db.delete_agent(agent_id)
    return {"deleted": True}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    db = safe_import()
    db.delete_task(task_id)
    return {"deleted": True}


@app.delete("/crews/{crew_id}")
def delete_crew(crew_id: str):
    db = safe_import()
    db.delete_crew(crew_id)
    return {"deleted": True}


@app.get("/export")
def export_all():
    """Export all data as JSON."""
    db = safe_import()
    import tempfile
    path = tempfile.mktemp(suffix='.json')
    db.export_to_json(path)
    with open(path) as f:
        data = json.load(f)
    os.unlink(path)
    return data


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8502)

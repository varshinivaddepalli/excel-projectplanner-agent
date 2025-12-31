"""
FastAPI for Project Planning Agent
Simple API to generate project plans from questionnaire responses.
"""
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph.graph import StateGraph, END
from state import GraphState, create_initial_state
from nodes.questionnaire import questionnaire_node_with_input
from nodes.validation import validation_node
from nodes.prompt import prompt_node
from nodes.orchestrator import orchestrator_node
from nodes.workers import category_worker_node
from nodes.aggregator import aggregator_node
from nodes.excel_generator import excel_generator_node

app = FastAPI(
    title="Construction Project Planner API",
    description="Generate comprehensive construction project plans",
    version="1.0.0"
)


# Request Models
class ProjectScale(BaseModel):
    """Project scale details - varies by project type"""
    # Highrise
    total_land_area: Optional[str] = None
    number_of_towers: Optional[int] = None
    floors_per_tower: Optional[int] = None
    average_flat_size: Optional[str] = None
    
    # Standalone/Commercial
    total_built_up_area: Optional[str] = None
    number_of_floors: Optional[int] = None
    purpose: Optional[str] = None
    usage_type: Optional[str] = None
    
    # Villa
    number_of_villas: Optional[int] = None
    average_villa_size: Optional[str] = None
    villa_floors: Optional[str] = None
    
    # Infrastructure
    infrastructure_type: Optional[str] = None
    approximate_length_or_area: Optional[str] = None
    estimated_duration_months: Optional[int] = None


class ProjectPlanRequest(BaseModel):
    """Request body for project plan generation"""
    location: str = Field(..., description="Project location")
    project_type: str = Field(..., description="Highrise, Standalone Building, Villa, Commercial, Infrastructure")
    project_scale: ProjectScale = Field(..., description="Project scale details")
    start_date: str = Field(default="Immediate", description="Immediate, Within 1 Month, or YYYY-MM-DD")
    plan_level: str = Field(default="High-level Plan", description="High-level Plan or Detailed Plan")


class ProjectPlanResponse(BaseModel):
    """Response for project plan generation"""
    success: bool
    message: str
    total_tasks: int = 0
    excel_file: Optional[str] = None
    download_url: Optional[str] = None
    generation_time_seconds: float = 0


# Build the graph once
def build_api_graph(responses: Dict[str, Any]):
    """Build graph with provided responses."""
    workflow = StateGraph(GraphState)
    
    def questionnaire_with_responses(state: GraphState) -> GraphState:
        return questionnaire_node_with_input(state, responses)
    
    workflow.add_node("questionnaire", questionnaire_with_responses)
    workflow.add_node("validation", validation_node)
    workflow.add_node("prompt", prompt_node)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("workers", category_worker_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("excel_generator", excel_generator_node)
    
    workflow.set_entry_point("questionnaire")
    workflow.add_edge("questionnaire", "validation")
    workflow.add_edge("validation", "prompt")
    workflow.add_edge("prompt", "orchestrator")
    workflow.add_edge("orchestrator", "workers")
    workflow.add_edge("workers", "aggregator")
    workflow.add_edge("aggregator", "excel_generator")
    workflow.add_edge("excel_generator", END)
    
    return workflow.compile()


@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "running",
        "service": "Construction Project Planner",
        "endpoints": {
            "generate": "POST /generate - Generate project plan",
            "download": "GET /download/{filename} - Download Excel file"
        }
    }


@app.post("/generate", response_model=ProjectPlanResponse)
async def generate_project_plan(request: ProjectPlanRequest):
    """
    Generate a construction project plan.
    
    Returns an Excel file with the complete project plan.
    """
    start_time = datetime.now()
    
    # Convert request to responses dict
    responses = {
        "location": request.location,
        "project_type": request.project_type,
        "project_scale": request.project_scale.model_dump(exclude_none=True),
        "start_date": request.start_date,
        "plan_level": request.plan_level
    }
    
    try:
        # Build and run the graph
        app_graph = build_api_graph(responses)
        initial_state = create_initial_state()
        
        final_state = app_graph.invoke(initial_state)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if final_state.get("excel_path"):
            filename = os.path.basename(final_state["excel_path"])
            return ProjectPlanResponse(
                success=True,
                message="Project plan generated successfully",
                total_tasks=final_state.get("aggregated_json", {}).get("total_tasks", 0),
                excel_file=filename,
                download_url=f"/download/{filename}",
                generation_time_seconds=round(duration, 2)
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=final_state.get("error_message", "Failed to generate project plan")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a generated Excel file."""
    file_path = os.path.join(os.path.dirname(__file__), "output", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



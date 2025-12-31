"""
LangGraph State Schema for Project Planning Agent
"""
from typing import TypedDict, Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ProjectScaleDetails(BaseModel):
    """Project scale details based on project type"""
    # Highrise specific
    total_land_area: Optional[str] = None
    number_of_towers: Optional[int] = None
    floors_per_tower: Optional[int] = None
    average_flat_size: Optional[str] = None
    
    # Standalone Building specific
    total_built_up_area: Optional[str] = None
    number_of_floors: Optional[int] = None
    purpose: Optional[str] = None
    
    # Villa specific
    number_of_villas: Optional[int] = None
    average_villa_size: Optional[str] = None
    villa_floors: Optional[str] = None
    
    # Commercial specific
    usage_type: Optional[str] = None
    
    # Infrastructure specific
    infrastructure_type: Optional[str] = None
    approximate_length_or_area: Optional[str] = None
    estimated_duration_months: Optional[int] = None


class QuestionnaireResponses(BaseModel):
    """Structured questionnaire responses"""
    location: str = Field(..., description="Project location")
    project_type: str = Field(..., description="Type of project: Highrise, Standalone Building, Villa, Commercial, Infrastructure")
    project_scale: ProjectScaleDetails = Field(default_factory=ProjectScaleDetails)
    start_date: str = Field(default="Immediate", description="Project start date preference")
    plan_level: str = Field(default="High-level Plan", description="High-level Plan or Detailed Plan")


class ValidationResult(BaseModel):
    """Validation result with status and errors"""
    is_valid: bool = True
    errors: List[str] = Field(default_factory=list)


class TaskItem(BaseModel):
    """Individual task item in the project plan"""
    # Common fields for both plan types
    phase_name: str
    activity_name: str
    task_name: str
    task_category: str
    task_duration: Optional[str] = None
    
    # Detailed plan fields
    task_start_date: Optional[str] = None
    task_end_date: Optional[str] = None
    work_quantity: Optional[float] = None
    work_rate: Optional[float] = None
    work_uom: Optional[str] = None
    task_description: Optional[str] = None
    priority: Optional[str] = None
    predecessor: Optional[str] = None
    dependency_type: Optional[str] = None
    successor: Optional[str] = None


class ProjectPlanJSON(BaseModel):
    """Final aggregated project plan in JSON format"""
    project_info: Dict[str, Any] = Field(default_factory=dict)
    plan_type: str = "high_level"
    tasks: List[TaskItem] = Field(default_factory=list)


class OrchestratorPlan(BaseModel):
    """Orchestrator's task distribution plan"""
    worker1_prompt: str = Field(default="", description="Prompt for Planning & Design phases")
    worker2_prompt: str = Field(default="", description="Prompt for Execution phases")
    worker3_prompt: str = Field(default="", description="Prompt for Closeout phases")


class WorkerOutputs(BaseModel):
    """Outputs from all worker nodes"""
    worker1_output: str = Field(default="", description="Planning & Design phase tasks")
    worker2_output: str = Field(default="", description="Execution phase tasks")
    worker3_output: str = Field(default="", description="Closeout phase tasks")


# Main LangGraph State using TypedDict for compatibility
class GraphState(TypedDict):
    """Main state that flows through the LangGraph"""
    # Questionnaire responses
    questionnaire_responses: Optional[Dict[str, Any]]

    # Validation status
    validation_result: Optional[Dict[str, Any]]

    # Enriched prompt with responses injected
    enriched_prompt: Optional[str]

    # Orchestrator's task distribution
    orchestrator_plan: Optional[Dict[str, Any]]

    # Worker outputs
    worker_outputs: Optional[Dict[str, Any]]

    # Aggregated JSON project plan
    aggregated_json: Optional[Dict[str, Any]]

    # Plan type
    plan_type: Optional[str]

    # Final excel output path
    excel_path: Optional[str]

    # Error message if any
    error_message: Optional[str]


def create_initial_state() -> GraphState:
    """Create initial empty state"""
    return GraphState(
        questionnaire_responses=None,
        validation_result=None,
        enriched_prompt=None,
        orchestrator_plan=None,
        worker_outputs=None,
        aggregated_json=None,
        plan_type=None,
        excel_path=None,
        error_message=None
    )


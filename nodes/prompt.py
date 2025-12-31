"""
Prompt Node - Injects questionnaire responses into fixed prompt template
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from state import GraphState
from config import PROMPTS_DIR, HIGH_LEVEL_COLUMNS, DETAILED_COLUMNS


def calculate_project_start_date(start_date_preference: str) -> str:
    """
    Calculate the actual project start date based on user preference.
    
    Args:
        start_date_preference: User's preference (Immediate, Within 1 Month, or custom date)
        
    Returns:
        Actual start date in YYYY-MM-DD format
    """
    today = datetime.now()
    
    if start_date_preference == "Immediate":
        # Start from next Monday for cleaner scheduling
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7  # If today is Monday, start next Monday
        start_date = today + timedelta(days=days_until_monday)
    elif start_date_preference == "Within 1 Month":
        # Start 1 month from now, on a Monday
        start_date = today + timedelta(days=30)
        days_until_monday = (7 - start_date.weekday()) % 7
        start_date = start_date + timedelta(days=days_until_monday)
    else:
        # Custom date - try to parse it
        try:
            start_date = datetime.strptime(start_date_preference, "%Y-%m-%d")
        except ValueError:
            # If parsing fails, default to next Monday
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            start_date = today + timedelta(days=days_until_monday)
    
    return start_date.strftime("%Y-%m-%d")


def format_project_scale_details(project_type: str, project_scale: Dict[str, Any]) -> str:
    """
    Format project scale details into a readable string.
    
    Args:
        project_type: Type of project
        project_scale: Project scale details dictionary
        
    Returns:
        Formatted string with project scale details
    """
    details = []
    
    if project_type == "Highrise":
        details.append(f"- Total Land Area: {project_scale.get('total_land_area', 'N/A')}")
        details.append(f"- Number of Towers: {project_scale.get('number_of_towers', 'N/A')}")
        details.append(f"- Floors per Tower: {project_scale.get('floors_per_tower', 'N/A')}")
        details.append(f"- Average Flat Size: {project_scale.get('average_flat_size', 'N/A')}")
    
    elif project_type == "Standalone Building":
        details.append(f"- Total Built-up Area: {project_scale.get('total_built_up_area', 'N/A')}")
        details.append(f"- Number of Floors: {project_scale.get('number_of_floors', 'N/A')}")
        details.append(f"- Purpose: {project_scale.get('purpose', 'N/A')}")
    
    elif project_type == "Villa":
        details.append(f"- Number of Villas: {project_scale.get('number_of_villas', 'N/A')}")
        details.append(f"- Average Villa Size: {project_scale.get('average_villa_size', 'N/A')}")
        details.append(f"- Number of Floors: {project_scale.get('villa_floors', 'N/A')}")
    
    elif project_type == "Commercial":
        details.append(f"- Total Built-up Area: {project_scale.get('total_built_up_area', 'N/A')}")
        details.append(f"- Number of Floors: {project_scale.get('number_of_floors', 'N/A')}")
        details.append(f"- Usage Type: {project_scale.get('usage_type', 'N/A')}")
    
    elif project_type == "Infrastructure":
        details.append(f"- Infrastructure Type: {project_scale.get('infrastructure_type', 'N/A')}")
        details.append(f"- Approximate Length/Area: {project_scale.get('approximate_length_or_area', 'N/A')}")
        details.append(f"- Estimated Duration: {project_scale.get('estimated_duration_months', 'N/A')} months")
    
    return "\n".join(details)


def get_output_format_instructions(plan_type: str, start_date: str = None, current_year: int = None) -> str:
    """
    Get output format instructions based on plan type.
    
    Args:
        plan_type: "high_level" or "detailed"
        start_date: The project start date
        current_year: The current year for date validation
        
    Returns:
        Formatted instructions string
    """
    if current_year is None:
        current_year = datetime.now().year
    if start_date is None:
        start_date = datetime.now().strftime("%Y-%m-%d")
        
    if plan_type == "detailed":
        columns = DETAILED_COLUMNS
        instructions = f"""
Generate a DETAILED project plan with the following columns for each task:

| Column | Description |
|--------|-------------|
| Phase Name | Major project phase (e.g., Planning, Design, Foundation, etc.) |
| Activity Name | Activity within the phase |
| Task Name | Specific task name |
| Task Category | Category of work (e.g., Civil, MEP, Finishing) |
| Task Start Date | Start date in YYYY-MM-DD format (MUST be {start_date} or later, year MUST be {current_year} or later) |
| Task End Date | End date in YYYY-MM-DD format (MUST be after start date, year MUST be {current_year} or later) |
| Work Quantity | Numerical quantity of work |
| Work Rate | Rate per unit |
| Work UOM | Unit of measurement |
| Task Description | Brief description of the task |
| Priority | Priority level (High, Medium, Low) |
| Predecessor | Task ID(s) that must complete before this task |
| Dependency Type | Type of dependency (FS, SS, FF, SF) |
| Successor | Task ID(s) that depend on this task |

IMPORTANT: All dates must start from {start_date} and be in year {current_year} or later!

Output Format:
```json
{{
  "tasks": [
    {{
      "phase_name": "...",
      "activity_name": "...",
      "task_name": "...",
      "task_category": "...",
      "task_start_date": "{start_date}",
      "task_end_date": "YYYY-MM-DD",
      "work_quantity": 0.0,
      "work_rate": 0.0,
      "work_uom": "...",
      "task_description": "...",
      "priority": "High|Medium|Low",
      "predecessor": "...",
      "dependency_type": "FS|SS|FF|SF",
      "successor": "..."
    }}
  ]
}}
```
"""
    else:
        columns = HIGH_LEVEL_COLUMNS
        instructions = """
Generate a HIGH-LEVEL project plan with the following columns for each task:

| Column | Description |
|--------|-------------|
| Phase Name | Major project phase (e.g., Planning, Design, Foundation, etc.) |
| Activity Name | Activity within the phase |
| Task Name | Specific task name |
| Task Category | Category of work (e.g., Civil, MEP, Finishing) |
| Task Duration | Duration in days or weeks (e.g., "5 days", "2 weeks") |

Output Format:
```json
{
  "tasks": [
    {
      "phase_name": "...",
      "activity_name": "...",
      "task_name": "...",
      "task_category": "...",
      "task_duration": "..."
    }
  ]
}
```
"""
    
    return instructions


def load_fixed_prompt() -> str:
    """
    Load the fixed prompt template from file.
    
    Returns:
        Fixed prompt template string
    """
    prompt_path = os.path.join(PROMPTS_DIR, "fixed_prompt.txt")
    
    try:
        with open(prompt_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback to default prompt if file not found
        return """
You are an expert construction project planner with deep knowledge of construction management, scheduling, and work breakdown structures (WBS).

## Project Information

**Location:** {location}
**Project Type:** {project_type}
**Plan Level:** {plan_level}

## Project Scale Details

{project_scale_details}

## Project Timeline

**Start Date:** {start_date}

## Your Task

Based on the project information above, create a comprehensive construction project plan for the **{phase_assignment}** phase(s).

### Output Requirements

{output_format_instructions}

### Guidelines

1. Ensure all tasks follow logical construction sequencing
2. Consider typical construction durations for the given project type and scale
3. Account for dependencies between tasks
4. Use industry-standard naming conventions for phases and activities
5. Be realistic about timeframes based on the project scale

Please generate the project plan tasks in JSON format.
"""


def prompt_node(state: GraphState) -> GraphState:
    """
    Main prompt node that injects responses into the fixed prompt template.
    
    Args:
        state: Current graph state with questionnaire_responses
        
    Returns:
        Updated state with enriched_prompt
    """
    responses = state.get("questionnaire_responses", {})
    plan_type = state.get("plan_type", "high_level")
    
    if not responses:
        state["error_message"] = "No questionnaire responses found for prompt generation"
        return state
    
    # Load fixed prompt template
    prompt_template = load_fixed_prompt()
    
    # Format project scale details
    project_scale_details = format_project_scale_details(
        responses.get("project_type", ""),
        responses.get("project_scale", {})
    )
    
    # Calculate actual project start date
    start_date_preference = responses.get("start_date", "Immediate")
    actual_start_date = calculate_project_start_date(start_date_preference)
    
    # Get current date for context
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_year = datetime.now().year
    
    # Get output format instructions with date context
    output_format_instructions = get_output_format_instructions(plan_type, actual_start_date, current_year)
    
    # Build the enriched prompt (without phase assignment - that comes from orchestrator)
    enriched_prompt = prompt_template.format(
        location=responses.get("location", "Not specified"),
        project_type=responses.get("project_type", "Not specified"),
        plan_level=responses.get("plan_level", "High-level Plan"),
        project_scale_details=project_scale_details,
        start_date=actual_start_date,
        current_date=current_date,
        current_year=current_year,
        phase_assignment="{phase_assignment}",  # Placeholder for orchestrator
        output_format_instructions=output_format_instructions
    )
    
    state["enriched_prompt"] = enriched_prompt
    
    print(f"\n📝 Prompt generated successfully")
    print(f"   - Current date: {current_date}")
    print(f"   - Project start date: {actual_start_date}")
    
    return state


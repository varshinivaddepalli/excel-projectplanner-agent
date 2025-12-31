"""
Validation Node - Validates questionnaire responses
"""
from typing import Dict, Any, List
from state import GraphState
from config import PROJECT_TYPES, PLAN_LEVELS


def validate_required_fields(responses: Dict[str, Any]) -> List[str]:
    """
    Validate that all required fields are present.
    
    Args:
        responses: Questionnaire responses dictionary
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Check mandatory fields
    if not responses.get("location"):
        errors.append("Location is required (Question 1)")
    
    if not responses.get("project_type"):
        errors.append("Project type is required (Question 2)")
    elif responses.get("project_type") not in PROJECT_TYPES:
        errors.append(f"Invalid project type. Must be one of: {', '.join(PROJECT_TYPES)}")
    
    return errors


def validate_project_scale(project_type: str, project_scale: Dict[str, Any]) -> List[str]:
    """
    Validate project scale details based on project type.
    
    Args:
        project_type: Type of project
        project_scale: Project scale details dictionary
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    if not project_scale:
        errors.append(f"Project scale details are required for {project_type} projects")
        return errors
    
    if project_type == "Highrise":
        if not project_scale.get("total_land_area"):
            errors.append("Total land area is required for Highrise projects")
        if not project_scale.get("number_of_towers"):
            errors.append("Number of towers is required for Highrise projects")
    
    elif project_type == "Standalone Building":
        if not project_scale.get("total_built_up_area"):
            errors.append("Total built-up area is required for Standalone Building projects")
        if not project_scale.get("number_of_floors"):
            errors.append("Number of floors is required for Standalone Building projects")
    
    elif project_type == "Villa":
        if not project_scale.get("number_of_villas"):
            errors.append("Number of villas is required for Villa projects")
    
    elif project_type == "Commercial":
        if not project_scale.get("total_built_up_area"):
            errors.append("Total built-up area is required for Commercial projects")
        if not project_scale.get("usage_type"):
            errors.append("Usage type is required for Commercial projects")
    
    elif project_type == "Infrastructure":
        if not project_scale.get("infrastructure_type"):
            errors.append("Infrastructure type is required for Infrastructure projects")
    
    return errors


def validate_numeric_fields(project_scale: Dict[str, Any]) -> List[str]:
    """
    Validate that numeric fields contain valid numbers.
    
    Args:
        project_scale: Project scale details dictionary
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    numeric_fields = [
        "number_of_towers",
        "floors_per_tower",
        "number_of_floors",
        "number_of_villas",
        "estimated_duration_months"
    ]
    
    for field in numeric_fields:
        value = project_scale.get(field)
        if value is not None:
            try:
                int_value = int(value)
                if int_value <= 0:
                    errors.append(f"{field.replace('_', ' ').title()} must be a positive number")
            except (ValueError, TypeError):
                errors.append(f"{field.replace('_', ' ').title()} must be a valid number")
    
    return errors


def validate_plan_level(plan_level: str) -> List[str]:
    """
    Validate plan level selection.
    
    Args:
        plan_level: Selected plan level
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    if plan_level and plan_level not in PLAN_LEVELS:
        errors.append(f"Invalid plan level. Must be one of: {', '.join(PLAN_LEVELS)}")
    
    return errors


def validation_node(state: GraphState) -> GraphState:
    """
    Main validation node that validates all questionnaire responses.
    
    Args:
        state: Current graph state with questionnaire_responses
        
    Returns:
        Updated state with validation_result
    """
    responses = state.get("questionnaire_responses", {})
    
    if not responses:
        state["validation_result"] = {
            "is_valid": False,
            "errors": ["No questionnaire responses found"]
        }
        state["error_message"] = "No questionnaire responses found"
        return state
    
    all_errors = []
    
    # Validate required fields
    all_errors.extend(validate_required_fields(responses))
    
    # Validate project scale based on type
    project_type = responses.get("project_type", "")
    project_scale = responses.get("project_scale", {})
    all_errors.extend(validate_project_scale(project_type, project_scale))
    
    # Validate numeric fields
    all_errors.extend(validate_numeric_fields(project_scale))
    
    # Validate plan level
    plan_level = responses.get("plan_level", "")
    all_errors.extend(validate_plan_level(plan_level))
    
    # Build validation result
    is_valid = len(all_errors) == 0
    
    state["validation_result"] = {
        "is_valid": is_valid,
        "errors": all_errors
    }
    
    if not is_valid:
        state["error_message"] = "; ".join(all_errors)
        print("\n❌ Validation Failed:")
        for error in all_errors:
            print(f"   - {error}")
    else:
        print("\n✅ Validation Passed")
    
    return state


"""
Questionnaire Node - Collects project information from user via CLI
"""
from typing import Dict, Any
from state import GraphState
from config import PROJECT_TYPES, PLAN_LEVELS, START_DATE_OPTIONS


def get_user_input(prompt: str, options: list = None, required: bool = True) -> str:
    """
    Get user input with optional validation against options list.
    
    Args:
        prompt: The prompt to display to user
        options: Optional list of valid options
        required: Whether the input is required
        
    Returns:
        User's input string
    """
    while True:
        if options:
            print(f"\n{prompt}")
            for i, option in enumerate(options, 1):
                print(f"  {i}. {option}")
            user_input = input("Enter your choice (number): ").strip()
            
            try:
                choice_idx = int(user_input) - 1
                if 0 <= choice_idx < len(options):
                    return options[choice_idx]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                # Check if they typed the option directly
                if user_input in options:
                    return user_input
                print("Please enter a valid number.")
        else:
            user_input = input(f"\n{prompt}: ").strip()
            if user_input or not required:
                return user_input
            print("This field is required. Please provide a value.")


def collect_highrise_details() -> Dict[str, Any]:
    """Collect details specific to Highrise projects"""
    print("\n🏢 Tell us the basic scale of the project:")
    return {
        "total_land_area": get_user_input("Total Land Area (Sq.ft / Acres)"),
        "number_of_towers": int(get_user_input("Number of Towers") or "1"),
        "floors_per_tower": int(get_user_input("Number of Floors per Tower") or "10"),
        "average_flat_size": get_user_input("Average Flat Size (Sq.ft)")
    }


def collect_standalone_details() -> Dict[str, Any]:
    """Collect details specific to Standalone Building projects"""
    print("\n🏬 Tell us the basic scale of the project:")
    return {
        "total_built_up_area": get_user_input("Total Built-up Area (Sq.ft)"),
        "number_of_floors": int(get_user_input("Number of Floors") or "5"),
        "purpose": get_user_input("Purpose", ["Residential", "Office", "Mixed"])
    }


def collect_villa_details() -> Dict[str, Any]:
    """Collect details specific to Villa projects"""
    print("\n🏘️ Tell us the basic scale of the project:")
    return {
        "number_of_villas": int(get_user_input("Number of Villas") or "10"),
        "average_villa_size": get_user_input("Average Villa Size (Sq.ft)"),
        "villa_floors": get_user_input("Number of Floors", ["G", "G+1", "G+2"])
    }


def collect_commercial_details() -> Dict[str, Any]:
    """Collect details specific to Commercial projects"""
    print("\n🏢 Tell us the basic scale of the project:")
    return {
        "total_built_up_area": get_user_input("Total Built-up Area (Sq.ft)"),
        "number_of_floors": int(get_user_input("Number of Floors") or "5"),
        "usage_type": get_user_input("Usage Type", ["Office", "Retail", "Mall", "Warehouse"])
    }


def collect_infrastructure_details() -> Dict[str, Any]:
    """Collect details specific to Infrastructure projects"""
    print("\n🚧 Tell us the basic scope:")
    return {
        "infrastructure_type": get_user_input("Project Type", ["Road", "Bridge", "Utility", "Metro", "Other"]),
        "approximate_length_or_area": get_user_input("Approximate Length or Area"),
        "estimated_duration_months": int(get_user_input("Estimated Duration (Months)") or "12")
    }


def get_start_date() -> str:
    """Get project start date from user"""
    choice = get_user_input("📅 When do you want to start the project?", START_DATE_OPTIONS, required=False)
    
    if choice == "Custom Date":
        return get_user_input("Enter custom date (YYYY-MM-DD)")
    
    return choice if choice else "Immediate"


def questionnaire_node(state: GraphState) -> GraphState:
    """
    Main questionnaire node that collects all project information from user.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with questionnaire_responses filled in
    """
    print("\n" + "=" * 60)
    print("  🏗️  PROJECT PLANNING QUESTIONNAIRE  🏗️")
    print("=" * 60)
    
    # Question 1: Location (Mandatory)
    print("\n--- Question 1 (Mandatory) ---")
    location = get_user_input("📍 Where is your project located?")
    
    # Question 2: Project Type (Mandatory)
    print("\n--- Question 2 (Mandatory) ---")
    project_type = get_user_input("🏗️ What type of project is this?", PROJECT_TYPES)
    
    # Question 3: Dynamic based on project type
    print("\n--- Question 3 (Project Details) ---")
    project_scale = {}
    
    if project_type == "Highrise":
        project_scale = collect_highrise_details()
    elif project_type == "Standalone Building":
        project_scale = collect_standalone_details()
    elif project_type == "Villa":
        project_scale = collect_villa_details()
    elif project_type == "Commercial":
        project_scale = collect_commercial_details()
    elif project_type == "Infrastructure":
        project_scale = collect_infrastructure_details()
    
    # Question 4: Start Date (Optional)
    print("\n--- Question 4 (Optional) ---")
    start_date = get_start_date()
    
    # Question 5: Plan Level (Optional)
    print("\n--- Question 5 (Optional) ---")
    plan_level = get_user_input("🎯 What level of plan do you want?", PLAN_LEVELS, required=False)
    if not plan_level:
        plan_level = "High-level Plan"
    
    # Build responses dictionary
    responses = {
        "location": location,
        "project_type": project_type,
        "project_scale": project_scale,
        "start_date": start_date,
        "plan_level": plan_level
    }
    
    print("\n" + "=" * 60)
    print("  ✅ Questionnaire Complete!")
    print("=" * 60)
    
    # Update state
    state["questionnaire_responses"] = responses
    state["plan_type"] = "detailed" if plan_level == "Detailed Plan" else "high_level"
    
    return state


def questionnaire_node_with_input(state: GraphState, responses: Dict[str, Any]) -> GraphState:
    """
    Alternative questionnaire node that accepts pre-defined responses (for testing).
    
    Args:
        state: Current graph state
        responses: Pre-defined questionnaire responses
        
    Returns:
        Updated state with questionnaire_responses filled in
    """
    state["questionnaire_responses"] = responses
    plan_level = responses.get("plan_level", "High-level Plan")
    state["plan_type"] = "detailed" if plan_level == "Detailed Plan" else "high_level"
    
    return state


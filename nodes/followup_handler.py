"""
Follow-up Handler Node - Manages the sequential follow-up question flow
Displays remaining questions, gets user selection, and routes to appropriate analyzer.
"""
from typing import List, Literal
from state import GraphState
from config import FOLLOWUP_QUESTIONS


def get_remaining_followups(completed: List[int]) -> List[dict]:
    """
    Get the list of follow-up questions that haven't been completed yet.
    
    Args:
        completed: List of completed follow-up IDs (1, 2, or 3)
        
    Returns:
        List of remaining follow-up question dictionaries
    """
    if completed is None:
        completed = []
    
    remaining = [q for q in FOLLOWUP_QUESTIONS if q["id"] not in completed]
    return remaining


def display_followup_questions(remaining: List[dict]) -> None:
    """
    Display the remaining follow-up questions to the user.
    
    Args:
        remaining: List of remaining follow-up question dictionaries
    """
    print("\n" + "=" * 70)
    print("   📋 FOLLOW-UP OPTIONS")
    print("=" * 70)
    print("\nWhat would you like to generate next?\n")
    
    for q in remaining:
        print(f"   {q['id']}. {q['question']}")
    
    print()


def get_user_selection(remaining: List[dict]) -> int:
    """
    Get the user's selection from the remaining follow-up options.
    
    Args:
        remaining: List of remaining follow-up question dictionaries
        
    Returns:
        Selected option ID (1, 2, or 3)
    """
    valid_ids = [str(q["id"]) for q in remaining]
    
    while True:
        try:
            choice = input(f"Enter your choice ({'/'.join(valid_ids)}): ").strip()
            if choice in valid_ids:
                selected = int(choice)
                selected_question = next(q["question"] for q in remaining if q["id"] == selected)
                print(f"\n✅ You selected: {selected_question}")
                return selected
            else:
                print(f"   Please enter one of: {', '.join(valid_ids)}")
        except ValueError:
            print("   Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n   Selection cancelled.")
            return None


def followup_handler_node(state: GraphState) -> GraphState:
    """
    Main follow-up handler node that displays remaining questions and gets user selection.
    
    This node:
    1. Checks which follow-ups have been completed
    2. Displays only the remaining options
    3. Gets user selection
    4. Updates state with the selection
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with current_followup_selection
    """
    # Initialize completed_followups if not set
    if state.get("completed_followups") is None:
        state["completed_followups"] = []
    
    # Initialize followup_excel_paths if not set
    if state.get("followup_excel_paths") is None:
        state["followup_excel_paths"] = []
    
    # Get remaining follow-ups
    completed = state.get("completed_followups", [])
    remaining = get_remaining_followups(completed)
    
    # Check if all follow-ups are complete
    if not remaining:
        print("\n✅ All follow-up analyses completed!")
        state["current_followup_selection"] = None
        return state
    
    # Display remaining questions
    display_followup_questions(remaining)
    
    # Get user selection
    selection = get_user_selection(remaining)
    
    if selection is None:
        # User cancelled - end the flow
        state["current_followup_selection"] = None
        return state
    
    # Update state with selection
    state["current_followup_selection"] = selection
    
    # Add to completed list (will be confirmed after Excel generation)
    # Note: We add it here to track selection, actual completion is after Excel
    
    return state


def should_continue_followup(state: GraphState) -> Literal["budget", "cost_breakup", "manpower", "end"]:
    """
    Conditional function to determine which analyzer to route to.
    
    Args:
        state: Current graph state
        
    Returns:
        Route to take: "budget", "cost_breakup", "manpower", or "end"
    """
    selection = state.get("current_followup_selection")
    
    if selection is None:
        return "end"
    elif selection == 1:
        return "budget"
    elif selection == 2:
        return "cost_breakup"
    elif selection == 3:
        return "manpower"
    else:
        return "end"


def check_followup_completion(state: GraphState) -> Literal["continue", "end"]:
    """
    Check if there are more follow-ups to process after generating an Excel.
    
    Args:
        state: Current graph state
        
    Returns:
        "continue" if more follow-ups remain, "end" if all are done
    """
    completed = state.get("completed_followups", [])
    
    # All 3 follow-ups completed
    if len(completed) >= 3:
        return "end"
    
    return "continue"


def mark_followup_complete(state: GraphState) -> GraphState:
    """
    Mark the current follow-up as complete after Excel generation.
    Called after followup_excel_generator_node.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with follow-up marked as complete
    """
    selection = state.get("current_followup_selection")
    
    if selection is not None:
        completed = state.get("completed_followups", [])
        if selection not in completed:
            completed.append(selection)
            state["completed_followups"] = completed
    
    return state

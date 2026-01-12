"""
Main LangGraph Workflow - Project Planning Agent
Production-ready version with comprehensive task generation.
"""
import sys
import os
from typing import Dict, Any, Literal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph.graph import StateGraph, END
from state import GraphState, create_initial_state
from nodes.questionnaire import questionnaire_node, questionnaire_node_with_input
from nodes.validation import validation_node
from nodes.prompt import prompt_node
from nodes.orchestrator import orchestrator_node
from nodes.workers import category_worker_node
from nodes.aggregator import aggregator_node
from nodes.excel_generator import excel_generator_node
from nodes.followup_handler import (
    followup_handler_node,
    should_continue_followup,
    check_followup_completion
)
from nodes.followup_analyzers import (
    budget_analyzer_node,
    cost_breakup_analyzer_node,
    manpower_analyzer_node
)
from nodes.followup_excel_generator import followup_excel_generator_node
from config import FOLLOWUP_QUESTIONS


def should_continue_after_validation(state: GraphState) -> Literal["continue", "error"]:
    """
    Determine if the workflow should continue after validation.
    """
    validation_result = state.get("validation_result", {})
    
    if validation_result.get("is_valid", False):
        return "continue"
    else:
        return "error"


def error_handler_node(state: GraphState) -> GraphState:
    """
    Handle errors in the workflow.
    """
    print("\n❌ Pipeline Error:")
    print(f"   {state.get('error_message', 'Unknown error')}")
    return state


def show_final_summary(final_state: GraphState) -> None:
    """
    Display final summary after all follow-ups are completed.
    
    Args:
        final_state: Final graph state
    """
    print("\n" + "=" * 70)
    print("   🎉 ALL ANALYSES COMPLETED!")
    print("=" * 70)
    
    # Show main project plan
    if final_state.get("excel_path"):
        print(f"\n📂 Project Plan: {final_state['excel_path']}")
        print(f"   Total tasks: {final_state.get('aggregated_json', {}).get('total_tasks', 0)}")
    
    # Show follow-up Excel files
    followup_paths = final_state.get("followup_excel_paths", [])
    if followup_paths:
        print(f"\n📊 Follow-up Analyses ({len(followup_paths)} files):")
        for path in followup_paths:
            print(f"   • {path}")
    
    print("\n" + "=" * 70)


def build_graph() -> StateGraph:
    """
    Build the LangGraph workflow with comprehensive task generation and follow-up processing.
    
    Flow:
    Questionnaire → Validation → Prompt → Orchestrator → 
    Category Workers → Aggregator → Excel Generator → 
    Follow-up Handler → [Budget/Cost/Manpower Analyzer] → 
    Follow-up Excel Generator → (loop back or END)
    """
    workflow = StateGraph(GraphState)
    
    # Add all nodes - Main workflow
    workflow.add_node("questionnaire", questionnaire_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("prompt", prompt_node)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("category_workers", category_worker_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("excel_generator", excel_generator_node)
    workflow.add_node("error_handler", error_handler_node)
    
    # Add follow-up nodes
    workflow.add_node("followup_handler", followup_handler_node)
    workflow.add_node("budget_analyzer", budget_analyzer_node)
    workflow.add_node("cost_breakup_analyzer", cost_breakup_analyzer_node)
    workflow.add_node("manpower_analyzer", manpower_analyzer_node)
    workflow.add_node("followup_excel_generator", followup_excel_generator_node)
    
    # Set entry point
    workflow.set_entry_point("questionnaire")
    
    # Define edges - Main workflow
    workflow.add_edge("questionnaire", "validation")
    
    # Conditional edge after validation
    workflow.add_conditional_edges(
        "validation",
        should_continue_after_validation,
        {
            "continue": "prompt",
            "error": "error_handler"
        }
    )
    
    workflow.add_edge("prompt", "orchestrator")
    workflow.add_edge("orchestrator", "category_workers")
    workflow.add_edge("category_workers", "aggregator")
    workflow.add_edge("aggregator", "excel_generator")
    
    # After main Excel generation, go to follow-up handler
    workflow.add_edge("excel_generator", "followup_handler")
    
    # Conditional edge from followup_handler to appropriate analyzer
    workflow.add_conditional_edges(
        "followup_handler",
        should_continue_followup,
        {
            "budget": "budget_analyzer",
            "cost_breakup": "cost_breakup_analyzer",
            "manpower": "manpower_analyzer",
            "end": END
        }
    )
    
    # All analyzers go to followup_excel_generator
    workflow.add_edge("budget_analyzer", "followup_excel_generator")
    workflow.add_edge("cost_breakup_analyzer", "followup_excel_generator")
    workflow.add_edge("manpower_analyzer", "followup_excel_generator")
    
    # After generating follow-up Excel, check if more follow-ups remain
    workflow.add_conditional_edges(
        "followup_excel_generator",
        check_followup_completion,
        {
            "continue": "followup_handler",  # Loop back for more follow-ups
            "end": END  # All 3 follow-ups done
        }
    )
    
    # Error handler goes to END
    workflow.add_edge("error_handler", END)
    
    return workflow


def run_interactive():
    """
    Run the project planner in interactive CLI mode.
    
    The workflow includes:
    1. Project questionnaire
    2. Task generation
    3. Main Excel generation
    4. Sequential follow-up analyses (budget, cost breakup, manpower)
    """
    print("\n" + "=" * 70)
    print("   🏗️  CONSTRUCTION PROJECT PLANNING AGENT  🏗️")
    print("   Production-Ready | Powered by LangGraph & Azure OpenAI")
    print("=" * 70)
    print("\n📋 This tool generates comprehensive project plans:")
    print("   • High-level Plan: 100+ tasks")
    print("   • Detailed Plan: 400+ tasks with dates & dependencies")
    print("   • Follow-up analyses: Budget, Cost Breakup, Manpower")
    print("=" * 70)
    
    # Build and compile the graph
    workflow = build_graph()
    app = workflow.compile()
    
    # Create initial state
    initial_state = create_initial_state()
    
    # Run the graph
    print("\n🚀 Starting project planning pipeline...\n")
    
    try:
        final_state = app.invoke(initial_state)
        
        # Check if we have a successful output
        if final_state.get("excel_path"):
            # Show final summary
            show_final_summary(final_state)
        else:
            print("\n" + "=" * 70)
            print("   ❌ PROJECT PLAN GENERATION FAILED")
            print("=" * 70)
            print(f"\nError: {final_state.get('error_message', 'Unknown error')}")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        raise


def run_with_responses(responses: Dict[str, Any], include_followups: bool = True):
    """
    Run the project planner with pre-defined responses (for testing/automation).
    
    Args:
        responses: Pre-defined questionnaire responses
        include_followups: Whether to include follow-up processing (default True)
        
    Returns:
        Final state dictionary
    """
    print("\n🚀 Starting project planning pipeline with pre-defined responses...")
    print(f"   Project Type: {responses.get('project_type')}")
    print(f"   Plan Level: {responses.get('plan_level')}")
    
    # Build the graph with modified questionnaire node
    workflow = StateGraph(GraphState)
    
    # Add modified questionnaire node that uses provided responses
    def questionnaire_with_responses(state: GraphState) -> GraphState:
        return questionnaire_node_with_input(state, responses)
    
    # Add main workflow nodes
    workflow.add_node("questionnaire", questionnaire_with_responses)
    workflow.add_node("validation", validation_node)
    workflow.add_node("prompt", prompt_node)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("category_workers", category_worker_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("excel_generator", excel_generator_node)
    workflow.add_node("error_handler", error_handler_node)
    
    # Add follow-up nodes if enabled
    if include_followups:
        workflow.add_node("followup_handler", followup_handler_node)
        workflow.add_node("budget_analyzer", budget_analyzer_node)
        workflow.add_node("cost_breakup_analyzer", cost_breakup_analyzer_node)
        workflow.add_node("manpower_analyzer", manpower_analyzer_node)
        workflow.add_node("followup_excel_generator", followup_excel_generator_node)
    
    workflow.set_entry_point("questionnaire")
    workflow.add_edge("questionnaire", "validation")
    
    workflow.add_conditional_edges(
        "validation",
        should_continue_after_validation,
        {
            "continue": "prompt",
            "error": "error_handler"
        }
    )
    
    workflow.add_edge("prompt", "orchestrator")
    workflow.add_edge("orchestrator", "category_workers")
    workflow.add_edge("category_workers", "aggregator")
    workflow.add_edge("aggregator", "excel_generator")
    
    if include_followups:
        # After main Excel generation, go to follow-up handler
        workflow.add_edge("excel_generator", "followup_handler")
        
        # Conditional edge from followup_handler to appropriate analyzer
        workflow.add_conditional_edges(
            "followup_handler",
            should_continue_followup,
            {
                "budget": "budget_analyzer",
                "cost_breakup": "cost_breakup_analyzer",
                "manpower": "manpower_analyzer",
                "end": END
            }
        )
        
        # All analyzers go to followup_excel_generator
        workflow.add_edge("budget_analyzer", "followup_excel_generator")
        workflow.add_edge("cost_breakup_analyzer", "followup_excel_generator")
        workflow.add_edge("manpower_analyzer", "followup_excel_generator")
        
        # After generating follow-up Excel, check if more follow-ups remain
        workflow.add_conditional_edges(
            "followup_excel_generator",
            check_followup_completion,
            {
                "continue": "followup_handler",
                "end": END
            }
        )
    else:
        workflow.add_edge("excel_generator", END)
    
    workflow.add_edge("error_handler", END)
    
    app = workflow.compile()
    initial_state = create_initial_state()
    
    return app.invoke(initial_state)


# Sample test responses for quick testing
SAMPLE_HIGHRISE_RESPONSES = {
    "location": "Mumbai, Maharashtra, India",
    "project_type": "Highrise",
    "project_scale": {
        "total_land_area": "5 Acres",
        "number_of_towers": 3,
        "floors_per_tower": 25,
        "average_flat_size": "1200 sq.ft"
    },
    "start_date": "Immediate",
    "plan_level": "High-level Plan"
}

SAMPLE_VILLA_RESPONSES = {
    "location": "Bangalore, Karnataka, India",
    "project_type": "Villa",
    "project_scale": {
        "number_of_villas": 50,
        "average_villa_size": "3000 sq.ft",
        "villa_floors": "G+1"
    },
    "start_date": "Within 1 Month",
    "plan_level": "Detailed Plan"
}

SAMPLE_COMMERCIAL_RESPONSES = {
    "location": "Hyderabad, Telangana, India",
    "project_type": "Commercial",
    "project_scale": {
        "total_built_up_area": "500000 sq.ft",
        "number_of_floors": 15,
        "usage_type": "Office"
    },
    "start_date": "Immediate",
    "plan_level": "Detailed Plan"
}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Construction Project Planning Agent")
    parser.add_argument(
        "--mode", 
        choices=["interactive", "test-highrise", "test-villa", "test-commercial"],
        default="interactive",
        help="Run mode: interactive (CLI) or test with sample data"
    )
    
    args = parser.parse_args()
    
    if args.mode == "interactive":
        run_interactive()
    elif args.mode == "test-highrise":
        print("\n" + "=" * 70)
        print("   Running with sample Highrise project data (High-level Plan)")
        print("=" * 70)
        result = run_with_responses(SAMPLE_HIGHRISE_RESPONSES)
        if result.get("excel_path"):
            print(f"\n✅ Success! Output: {result['excel_path']}")
            print(f"   Total tasks: {result.get('aggregated_json', {}).get('total_tasks', 0)}")
    elif args.mode == "test-villa":
        print("\n" + "=" * 70)
        print("   Running with sample Villa project data (Detailed Plan)")
        print("=" * 70)
        result = run_with_responses(SAMPLE_VILLA_RESPONSES)
        if result.get("excel_path"):
            print(f"\n✅ Success! Output: {result['excel_path']}")
            print(f"   Total tasks: {result.get('aggregated_json', {}).get('total_tasks', 0)}")
    elif args.mode == "test-commercial":
        print("\n" + "=" * 70)
        print("   Running with sample Commercial project data (Detailed Plan)")
        print("=" * 70)
        result = run_with_responses(SAMPLE_COMMERCIAL_RESPONSES)
        if result.get("excel_path"):
            print(f"\n✅ Success! Output: {result['excel_path']}")
            print(f"   Total tasks: {result.get('aggregated_json', {}).get('total_tasks', 0)}")

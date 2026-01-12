"""
Follow-up Analyzer Nodes - Use LLM to analyze project plan and generate follow-up data
Contains analyzers for budget estimates, cost breakup, and manpower estimates.
"""
import os
import json
import re
import traceback
from typing import Dict, Any, List
from state import GraphState
from config import get_llm, PROMPTS_DIR


def load_prompt_template(filename: str) -> str:
    """
    Load a prompt template from the prompts directory.
    
    Args:
        filename: Name of the prompt template file
        
    Returns:
        Prompt template string
    """
    prompt_path = os.path.join(PROMPTS_DIR, filename)
    try:
        with open(prompt_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")


def extract_json_from_response(response: str) -> Dict[str, Any]:
    """
    Extract JSON from LLM response with robust parsing.
    
    Args:
        response: LLM response string
        
    Returns:
        Parsed JSON dictionary
    """
    if not response:
        return {}
    
    # Clean the response
    cleaned = response.strip()
    
    # Try to find JSON in code blocks first
    json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    matches = re.findall(json_pattern, cleaned)
    
    if matches:
        for match in matches:
            try:
                json_str = match.strip()
                # Remove trailing commas before closing brackets (common LLM error)
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"   Debug: JSON decode error in code block: {str(e)[:50]}")
                continue
    
    # Try to find raw JSON object
    try:
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = cleaned[start:end + 1]
            # Remove trailing commas before closing brackets
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"   Debug: JSON decode error in raw extraction: {str(e)[:50]}")
    
    # Try to find JSON array if object not found
    try:
        start = cleaned.find('[')
        end = cleaned.rfind(']')
        if start != -1 and end != -1 and end > start:
            json_str = cleaned[start:end + 1]
            json_str = re.sub(r',\s*]', ']', json_str)
            arr = json.loads(json_str)
            # Wrap array in appropriate key based on content
            if arr and isinstance(arr, list):
                return {"items": arr}
    except json.JSONDecodeError as e:
        print(f"   Debug: JSON decode error in array extraction: {str(e)[:50]}")
    
    print(f"   Debug: Could not extract JSON. Response preview: {cleaned[:200]}...")
    return {}


def format_project_context(state: GraphState) -> Dict[str, str]:
    """
    Format project context for prompts.
    
    Args:
        state: Current graph state
        
    Returns:
        Dictionary with formatted context strings
    """
    responses = state.get("questionnaire_responses", {})
    aggregated = state.get("aggregated_json", {})
    
    # Basic project info
    location = responses.get("location", "Not specified")
    project_type = responses.get("project_type", "Not specified")
    plan_level = responses.get("plan_level", "High-level Plan")
    
    # Project scale details
    scale = responses.get("project_scale", {})
    scale_details = []
    for key, value in scale.items():
        if value:
            formatted_key = key.replace("_", " ").title()
            scale_details.append(f"- {formatted_key}: {value}")
    project_scale_details = "\n".join(scale_details) if scale_details else "Not specified"
    
    # Task summary
    tasks = aggregated.get("tasks", [])
    total_tasks = len(tasks)
    
    # Extract unique phases and categories
    phases = list(set(t.get("phase_name", "Unknown") for t in tasks if t.get("phase_name")))
    categories = list(set(t.get("task_category", "Unknown") for t in tasks if t.get("task_category")))
    
    # Format task details (summarized to avoid token limits)
    task_details = []
    for i, task in enumerate(tasks[:100]):  # Limit to first 100 tasks for context
        task_details.append(
            f"- Phase: {task.get('phase_name', 'N/A')}, "
            f"Activity: {task.get('activity_name', 'N/A')}, "
            f"Task: {task.get('task_name', 'N/A')}, "
            f"Category: {task.get('task_category', 'N/A')}"
        )
    
    if len(tasks) > 100:
        task_details.append(f"... and {len(tasks) - 100} more tasks")
    
    return {
        "location": location,
        "project_type": project_type,
        "plan_level": plan_level,
        "project_scale_details": project_scale_details,
        "total_tasks": str(total_tasks),
        "phases": ", ".join(phases),
        "categories": ", ".join(categories),
        "task_details": "\n".join(task_details)
    }


def budget_analyzer_node(state: GraphState) -> GraphState:
    """
    Analyze project plan and generate budget estimates using LLM.
    
    Args:
        state: Current graph state with aggregated_json
        
    Returns:
        Updated state with followup_analysis_result containing budget items
    """
    print("\n💰 Budget Analyzer: Generating budget estimates...")
    
    try:
        # Load prompt template
        prompt_template = load_prompt_template("budget_analysis_prompt.txt")
        
        # Format context
        context = format_project_context(state)
        
        # Build prompt
        prompt = prompt_template.format(**context)
        
        # Call LLM
        llm = get_llm()
        response = llm.invoke(prompt)
        
        # Extract JSON
        result = extract_json_from_response(response.content)
        # Try multiple possible keys for the items array
        budget_items = result.get("budget_items", result.get("items", result.get("data", [])))
        
        if not budget_items and isinstance(result, list):
            budget_items = result
        
        print(f"   ✅ Generated {len(budget_items)} budget line items")
        
        # Store in state
        state["followup_analysis_result"] = {
            "type": "budget",
            "items": budget_items,
            "total_items": len(budget_items)
        }
        
    except Exception as e:
        print(f"   ❌ Budget analysis error: {str(e)}")
        traceback.print_exc()
        state["followup_analysis_result"] = {
            "type": "budget",
            "items": [],
            "error": str(e)
        }
    
    return state


def cost_breakup_analyzer_node(state: GraphState) -> GraphState:
    """
    Analyze project plan and generate cost breakup by work category using LLM.
    
    Args:
        state: Current graph state with aggregated_json
        
    Returns:
        Updated state with followup_analysis_result containing cost items
    """
    print("\n📊 Cost Breakup Analyzer: Generating cost breakup by work category...")
    
    try:
        # Load prompt template
        prompt_template = load_prompt_template("cost_breakup_prompt.txt")
        
        # Format context
        context = format_project_context(state)
        
        # Build prompt
        prompt = prompt_template.format(**context)
        
        # Call LLM
        llm = get_llm()
        response = llm.invoke(prompt)
        
        # Extract JSON
        result = extract_json_from_response(response.content)
        # Try multiple possible keys for the items array
        cost_items = result.get("cost_items", result.get("items", result.get("data", [])))
        
        if not cost_items and isinstance(result, list):
            cost_items = result
        
        print(f"   ✅ Generated {len(cost_items)} cost breakup items")
        
        # Store in state
        state["followup_analysis_result"] = {
            "type": "cost_breakup",
            "items": cost_items,
            "total_items": len(cost_items)
        }
        
    except Exception as e:
        print(f"   ❌ Cost breakup analysis error: {str(e)}")
        traceback.print_exc()
        state["followup_analysis_result"] = {
            "type": "cost_breakup",
            "items": [],
            "error": str(e)
        }
    
    return state


def manpower_analyzer_node(state: GraphState) -> GraphState:
    """
    Analyze project plan and generate manpower estimates using LLM.
    
    Args:
        state: Current graph state with aggregated_json
        
    Returns:
        Updated state with followup_analysis_result containing manpower items
    """
    print("\n👷 Manpower Analyzer: Generating manpower estimates...")
    
    try:
        # Load prompt template
        prompt_template = load_prompt_template("manpower_analysis_prompt.txt")
        
        # Format context
        context = format_project_context(state)
        
        # Build prompt
        prompt = prompt_template.format(**context)
        
        # Call LLM
        llm = get_llm()
        response = llm.invoke(prompt)
        
        # Extract JSON
        result = extract_json_from_response(response.content)
        # Try multiple possible keys for the items array
        manpower_items = result.get("manpower_items", result.get("items", result.get("data", [])))
        
        if not manpower_items and isinstance(result, list):
            manpower_items = result
        
        print(f"   ✅ Generated {len(manpower_items)} manpower items")
        
        # Store in state
        state["followup_analysis_result"] = {
            "type": "manpower",
            "items": manpower_items,
            "total_items": len(manpower_items)
        }
        
    except Exception as e:
        print(f"   ❌ Manpower analysis error: {str(e)}")
        traceback.print_exc()
        state["followup_analysis_result"] = {
            "type": "manpower",
            "items": [],
            "error": str(e)
        }
    
    return state

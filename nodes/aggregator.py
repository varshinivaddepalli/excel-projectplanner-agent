"""
Aggregator Node - Combines worker outputs into final project plan.
No iteration - single pass aggregation with date calculation.
"""
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List
from state import GraphState


def parse_duration(duration_str: str) -> int:
    """Parse duration string to days."""
    if not duration_str:
        return 5
    
    duration_str = str(duration_str).lower()
    numbers = re.findall(r'\d+', duration_str)
    if not numbers:
        return 5
    
    num = int(numbers[0])
    
    if 'week' in duration_str:
        return num * 7
    elif 'month' in duration_str:
        return num * 30
    else:
        return max(1, num)


def calculate_sequential_dates(tasks: List[Dict[str, Any]], start_date: str) -> List[Dict[str, Any]]:
    """Calculate sequential dates for tasks."""
    try:
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        current_date = datetime.now()
    
    phase_dates = {}
    
    for task in tasks:
        phase = task.get("phase_name", "General")
        
        # Get duration
        duration_str = task.get("task_duration", "5 days")
        duration_days = parse_duration(duration_str)
        
        # Determine start date based on phase
        if phase in phase_dates:
            task_start = phase_dates[phase]
        else:
            task_start = current_date
        
        task_end = task_start + timedelta(days=duration_days)
        
        task["task_start_date"] = task_start.strftime("%Y-%m-%d")
        task["task_end_date"] = task_end.strftime("%Y-%m-%d")
        if not task.get("task_duration"):
            task["task_duration"] = f"{duration_days} days"
        
        phase_dates[phase] = task_end
        if task_end > current_date:
            current_date = task_end
    
    return tasks


def add_task_identifiers(tasks: List[Dict[str, Any]], plan_type: str) -> List[Dict[str, Any]]:
    """Add task IDs and dependencies."""
    phase_groups = {}
    
    for i, task in enumerate(tasks):
        task_id = f"T{i+1:04d}"
        task["task_id"] = task_id
        
        key = f"{task.get('phase_name', '')}|{task.get('activity_name', '')}"
        if key not in phase_groups:
            phase_groups[key] = []
        phase_groups[key].append((i, task_id))
    
    if plan_type == "detailed":
        for key, group in phase_groups.items():
            for idx, (task_idx, task_id) in enumerate(group):
                if idx > 0:
                    tasks[task_idx]["predecessor"] = group[idx - 1][1]
                    tasks[task_idx]["dependency_type"] = "FS"
                if idx < len(group) - 1:
                    tasks[task_idx]["successor"] = group[idx + 1][1]
    
    return tasks


def aggregator_node(state: GraphState) -> GraphState:
    """
    Combine all worker outputs - no iteration.
    """
    worker_outputs = state.get("worker_outputs", {})
    responses = state.get("questionnaire_responses", {})
    plan_type = state.get("plan_type", "high_level")
    orchestrator_plan = state.get("orchestrator_plan", {})
    
    if not worker_outputs:
        state["error_message"] = "No worker outputs found"
        return state
    
    min_tasks = orchestrator_plan.get("min_tasks", 100)
    
    print("\n📊 Aggregator: Combining outputs...")
    
    # Collect all tasks
    all_tasks = []
    
    for worker_key in sorted(worker_outputs.keys()):
        output = worker_outputs[worker_key]
        package_name = output.get("package_name", worker_key)
        tasks = output.get("tasks", [])
        
        # Ensure phase names are set
        for task in tasks:
            if not task.get("phase_name"):
                task["phase_name"] = package_name
        
        all_tasks.extend(tasks)
    
    print(f"   Total tasks: {len(all_tasks)}")
    
    # Add task IDs
    all_tasks = add_task_identifiers(all_tasks, plan_type)
    
    # Calculate dates for detailed plan
    if plan_type == "detailed":
        from nodes.prompt import calculate_project_start_date
        start_pref = responses.get("start_date", "Immediate")
        actual_start = calculate_project_start_date(start_pref)
        all_tasks = calculate_sequential_dates(all_tasks, actual_start)
    
    # Build final output
    aggregated_json = {
        "project_info": {
            "location": responses.get("location", ""),
            "project_type": responses.get("project_type", ""),
            "plan_level": responses.get("plan_level", ""),
            "start_date": responses.get("start_date", ""),
            "project_scale": responses.get("project_scale", {}),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "plan_type": plan_type,
        "tasks": all_tasks,
        "total_tasks": len(all_tasks)
    }
    
    state["aggregated_json"] = aggregated_json
    
    # Report status
    if len(all_tasks) >= min_tasks:
        print(f"   ✅ Met target: {len(all_tasks)} tasks (min: {min_tasks})")
    else:
        print(f"   ℹ️  Generated {len(all_tasks)} tasks (target: {min_tasks})")
    
    return state

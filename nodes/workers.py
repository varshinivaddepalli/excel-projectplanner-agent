"""
Worker Nodes - Generate project plan tasks in PARALLEL.
Uses concurrent execution for speed.
"""
import json
import re
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from state import GraphState
from config import get_llm


def extract_json_from_response(response: str) -> Dict[str, Any]:
    """Extract JSON from LLM response."""
    json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    matches = re.findall(json_pattern, response)
    
    if matches:
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
    
    try:
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1:
            return json.loads(response[start:end + 1])
    except json.JSONDecodeError:
        pass
    
    return {"tasks": []}


def process_single_worker(worker_key: str, worker_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single worker - called in parallel.
    
    Args:
        worker_key: Worker identifier
        worker_info: Worker configuration with prompt
        
    Returns:
        Worker output with tasks
    """
    package_name = worker_info.get("package_name", worker_key)
    prompt = worker_info.get("prompt", "")
    
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        result = extract_json_from_response(response.content)
        tasks = result.get("tasks", [])
        
        return {
            "worker_key": worker_key,
            "package_name": package_name,
            "tasks": tasks,
            "task_count": len(tasks),
            "success": True
        }
    except Exception as e:
        return {
            "worker_key": worker_key,
            "package_name": package_name,
            "tasks": [],
            "task_count": 0,
            "success": False,
            "error": str(e)[:50]
        }


def category_worker_node(state: GraphState) -> GraphState:
    """
    Process ALL workers in PARALLEL using ThreadPoolExecutor.
    """
    orchestrator_plan = state.get("orchestrator_plan", {})
    
    if not orchestrator_plan:
        state["error_message"] = "No orchestrator plan found"
        return state
    
    worker_prompts = orchestrator_plan.get("worker_prompts", {})
    num_workers = len(worker_prompts)
    
    print(f"\n🔧 Workers: Processing {num_workers} work packages in PARALLEL...")
    
    all_worker_outputs = {}
    total_tasks = 0
    completed = 0
    
    # Run all workers in parallel
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all workers
        futures = {
            executor.submit(process_single_worker, worker_key, worker_info): worker_key
            for worker_key, worker_info in worker_prompts.items()
        }
        
        # Collect results as they complete
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            worker_key = result["worker_key"]
            
            all_worker_outputs[worker_key] = {
                "package_name": result["package_name"],
                "tasks": result["tasks"],
                "task_count": result["task_count"]
            }
            
            total_tasks += result["task_count"]
            status = "✅" if result["success"] else "❌"
            print(f"   [{completed}/{num_workers}] {result['package_name']}: {status} {result['task_count']} tasks")
    
    state["worker_outputs"] = all_worker_outputs
    
    print(f"\n   📊 Total tasks generated: {total_tasks}")
    
    return state


# Legacy compatibility
def worker_planning_node(state: GraphState) -> GraphState:
    return category_worker_node(state)

def worker_execution_node(state: GraphState) -> GraphState:
    return state

def worker_closeout_node(state: GraphState) -> GraphState:
    return state

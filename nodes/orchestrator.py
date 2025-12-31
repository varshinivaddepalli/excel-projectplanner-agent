"""
Orchestrator Node - Uses LLM to dynamically create focused worker assignments
based on project type and required task count.
"""
import json
import re
from typing import Dict, Any
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
    
    return {}


def format_project_context(responses: Dict[str, Any]) -> str:
    """Format project details for the orchestrator prompt."""
    project_type = responses.get("project_type", "")
    location = responses.get("location", "")
    plan_level = responses.get("plan_level", "High-level Plan")
    start_date = responses.get("start_date", "")
    scale = responses.get("project_scale", {})
    
    context = f"""
Project Type: {project_type}
Location: {location}
Plan Level: {plan_level}
Start Date: {start_date}

Project Scale Details:
"""
    for key, value in scale.items():
        if value:
            formatted_key = key.replace("_", " ").title()
            context += f"- {formatted_key}: {value}\n"
    
    return context


def orchestrator_node(state: GraphState) -> GraphState:
    """
    Orchestrator that creates the right number of focused worker assignments.
    
    For high-level (100 tasks): 3 workers (~35 tasks each)
    For detailed (400 tasks): 10 workers (~40 tasks each)
    """
    enriched_prompt = state.get("enriched_prompt", "")
    responses = state.get("questionnaire_responses", {})
    plan_type = state.get("plan_type", "high_level")
    
    if not enriched_prompt:
        state["error_message"] = "No enriched prompt found for orchestration"
        return state
    
    project_context = format_project_context(responses)
    project_type = responses.get("project_type", "General")
    
    # Determine number of workers based on plan type
    # Each LLM call generates ~13 tasks on average
    if plan_type == "detailed":
        num_workers = 32  # 32 × 13 = 416 tasks (buffer for 400)
        tasks_per_worker = 13
        min_tasks = 400
    else:
        num_workers = 8  # 8 × 13 = ~104 tasks
        tasks_per_worker = 13
        min_tasks = 100
    
    print(f"\n🎯 Orchestrator: Creating {num_workers} focused work assignments...")
    
    # Ask LLM to create worker assignments
    orchestrator_prompt = f"""
You are a senior construction project manager. Create a work breakdown for this project.

{project_context}

Create exactly {num_workers} distinct work packages for generating a comprehensive project plan.
Each work package will be handled by a separate worker who will generate ~{tasks_per_worker} tasks.

IMPORTANT:
1. Each work package must be SPECIFIC and NON-OVERLAPPING
2. Together they must cover the ENTIRE project lifecycle
3. Consider all aspects: planning, procurement, construction, MEP, finishes, handover
4. Be specific to {project_type} projects

Return JSON:
```json
{{
    "work_packages": [
        {{
            "id": 1,
            "name": "Package name",
            "scope": "Detailed scope description - what phases/activities this covers",
            "key_deliverables": ["deliverable 1", "deliverable 2", ...]
        }},
        ...
    ]
}}
```

Create exactly {num_workers} work packages that comprehensively cover a {project_type} project.
"""
    
    try:
        llm = get_llm()
        response = llm.invoke(orchestrator_prompt)
        work_plan = extract_json_from_response(response.content)
        
        work_packages = work_plan.get("work_packages", [])
        
        if not work_packages:
            raise ValueError("No work packages received")
        
        print(f"\n   📋 Work Packages Created:")
        for pkg in work_packages:
            print(f"      {pkg.get('id', '?')}. {pkg.get('name', 'Unknown')}")
        
        # Create worker prompts
        worker_prompts = {}
        for pkg in work_packages:
            worker_key = f"worker_{pkg.get('id', len(worker_prompts)+1)}"
            worker_prompt = create_worker_prompt(
                enriched_prompt,
                pkg,
                responses,
                plan_type,
                tasks_per_worker
            )
            worker_prompts[worker_key] = {
                "prompt": worker_prompt,
                "package_name": pkg.get("name", ""),
                "scope": pkg.get("scope", ""),
                "target_tasks": tasks_per_worker
            }
        
        orchestrator_plan = {
            "worker_prompts": worker_prompts,
            "plan_type": plan_type,
            "min_tasks": min_tasks,
            "num_workers": len(worker_prompts),
            "tasks_per_worker": tasks_per_worker,
            "project_type": project_type
        }
        
        state["orchestrator_plan"] = orchestrator_plan
        print(f"\n   📊 Target: {len(worker_prompts)} workers × {tasks_per_worker} tasks = {len(worker_prompts) * tasks_per_worker} tasks")
        
    except Exception as e:
        print(f"   ❌ Orchestration error: {str(e)}")
        state["error_message"] = f"Orchestration failed: {str(e)}"
    
    return state


def create_worker_prompt(
    base_prompt: str,
    package: Dict[str, Any],
    responses: Dict[str, Any],
    plan_type: str,
    target_tasks: int
) -> str:
    """Create a focused prompt for a specific work package."""
    
    package_name = package.get("name", "")
    scope = package.get("scope", "")
    deliverables = package.get("key_deliverables", [])
    
    # Replace placeholder in base prompt
    worker_prompt = base_prompt.replace("{phase_assignment}", package_name)
    
    additional = f"""

## YOUR WORK PACKAGE: {package_name}

**Scope:** {scope}

**Key Deliverables:**
{chr(10).join([f'- {d}' for d in deliverables])}

**Requirements:**
1. Generate exactly {target_tasks} detailed, actionable tasks
2. Cover ALL aspects within your scope
3. Include: Planning, Procurement, Execution, Quality Check, Handover tasks
4. Each task must be specific and measurable
5. Use appropriate phase names that reflect {responses.get("project_type", "")} projects

**Task Quality Standards:**
- Tasks should be 1-5 days in duration typically
- Include material/equipment procurement tasks
- Include inspection and approval milestones
- Include coordination tasks with other trades
- Be specific (not generic like "do work")

Generate {target_tasks} high-quality tasks in the exact JSON format specified.
"""
    
    return worker_prompt + additional

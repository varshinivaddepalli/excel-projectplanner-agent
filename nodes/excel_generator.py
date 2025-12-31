"""
Excel Generator Node - Converts aggregated JSON to Excel file
"""
import os
from datetime import datetime
from typing import Dict, Any, List
from openpyxl import Workbook

from state import GraphState
from config import OUTPUT_DIR, HIGH_LEVEL_COLUMNS, DETAILED_COLUMNS
from utils.excel_helper import (
    create_workbook,
    format_excel_sheet,
    apply_data_formatting,
    add_project_info_sheet
)


def get_task_value(task: Dict[str, Any], column: str) -> Any:
    """
    Get the value for a specific column from a task dictionary.
    
    Args:
        task: Task dictionary
        column: Column header name
        
    Returns:
        Value for the column
    """
    # Map column names to dictionary keys
    column_key_map = {
        "Phase Name": "phase_name",
        "Activity Name": "activity_name",
        "Task Name": "task_name",
        "Task Category": "task_category",
        "Task Duration": "task_duration",
        "Task Start Date": "task_start_date",
        "Task End Date": "task_end_date",
        "Work Quantity": "work_quantity",
        "Work Rate": "work_rate",
        "Work UOM": "work_uom",
        "Task Description": "task_description",
        "Priority": "priority",
        "Predecessor": "predecessor",
        "Dependency Type": "dependency_type",
        "Successor": "successor"
    }
    
    key = column_key_map.get(column, column.lower().replace(" ", "_"))
    value = task.get(key, "")
    
    # Handle None values
    if value is None:
        return ""
    
    return value


def write_tasks_to_sheet(ws, tasks: List[Dict[str, Any]], columns: List[str]) -> int:
    """
    Write tasks to the worksheet.
    
    Args:
        ws: Worksheet to write to
        tasks: List of task dictionaries
        columns: List of column headers
        
    Returns:
        Number of rows written
    """
    row_idx = 2  # Start after header row
    
    for task in tasks:
        for col_idx, column in enumerate(columns, 1):
            value = get_task_value(task, column)
            ws.cell(row=row_idx, column=col_idx, value=value)
        row_idx += 1
    
    return row_idx - 2  # Return number of data rows


def excel_generator_node(state: GraphState) -> GraphState:
    """
    Main Excel generator node that creates the final Excel output.
    
    Args:
        state: Current graph state with aggregated_json
        
    Returns:
        Updated state with excel_path
    """
    aggregated_json = state.get("aggregated_json", {})
    
    if not aggregated_json:
        state["error_message"] = "No aggregated JSON found for Excel generation"
        return state
    
    print("\n📑 Excel Generator: Creating Excel file...")
    
    # Determine columns based on plan type
    plan_type = aggregated_json.get("plan_type", "high_level")
    columns = DETAILED_COLUMNS if plan_type == "detailed" else HIGH_LEVEL_COLUMNS
    
    # Create workbook
    wb = create_workbook()
    
    # Remove default sheet and create Project Plan sheet
    default_sheet = wb.active
    wb.remove(default_sheet)
    
    # Add Project Info sheet
    project_info = aggregated_json.get("project_info", {})
    add_project_info_sheet(wb, project_info)
    
    # Create main Project Plan sheet
    ws = wb.create_sheet("Project Plan")
    
    # Apply header formatting
    format_excel_sheet(ws, columns)
    
    # Write tasks
    tasks = aggregated_json.get("tasks", [])
    rows_written = write_tasks_to_sheet(ws, tasks, columns)
    
    print(f"   - Plan type: {plan_type}")
    print(f"   - Columns: {len(columns)}")
    print(f"   - Tasks written: {rows_written}")
    
    # Apply data formatting
    if rows_written > 0:
        apply_data_formatting(ws, 2, rows_written + 1, len(columns))
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_type = project_info.get("project_type", "project").replace(" ", "_")
    filename = f"project_plan_{project_type}_{timestamp}.xlsx"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Save workbook
    wb.save(filepath)
    
    state["excel_path"] = filepath
    
    print(f"   ✅ Excel file saved: {filepath}")
    
    return state


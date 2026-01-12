# Construction Project Planning Agent

A comprehensive AI-powered project planning system that generates detailed construction project plans, budget estimates, cost breakups, and manpower estimates using LangGraph and Azure OpenAI.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Interactive CLI Mode](#interactive-cli-mode)
  - [Test Mode](#test-mode)
  - [API Mode](#api-mode)
- [Project Structure](#project-structure)
- [Workflow](#workflow)
- [Output Files](#output-files)
- [Dependencies](#dependencies)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This project is an intelligent construction project planning agent that leverages LangGraph for orchestration and Azure OpenAI for task generation. It creates comprehensive project plans with:

- **High-level Plans**: 100+ tasks covering major project phases
- **Detailed Plans**: 400+ tasks with dates, dependencies, quantities, and rates
- **Follow-up Analyses**: Budget estimates, cost breakups, and manpower estimates

The system supports multiple project types:
- Highrise Buildings
- Standalone Buildings
- Villa Projects
- Commercial Buildings
- Infrastructure Projects

## ✨ Features

### Core Capabilities

1. **Interactive Questionnaire**: Collects project information through a structured questionnaire
2. **Intelligent Task Generation**: Uses LLM to generate contextually appropriate tasks
3. **Parallel Processing**: Orchestrates multiple workers to generate tasks in parallel
4. **Excel Generation**: Creates formatted Excel files with project plans
5. **Follow-up Analyses**: Generates additional analyses after main plan creation:
   - Budget Estimates
   - Cost Breakup by Work Category
   - Manpower Estimates

### Technical Features

- **LangGraph Workflow**: State-based workflow management
- **Azure OpenAI Integration**: Uses GPT-4 models for task generation
- **Validation**: Input validation and error handling
- **Modular Architecture**: Clean separation of concerns
- **FastAPI Support**: RESTful API for programmatic access

## 🏗️ Architecture

The system uses a LangGraph-based workflow with the following key components:

```
┌─────────────────┐
│  Questionnaire  │ → Collects project information
└────────┬────────┘
         │
┌────────▼────────┐
│   Validation    │ → Validates inputs
└────────┬────────┘
         │
┌────────▼────────┐
│     Prompt      │ → Enriches base prompt with project details
└────────┬────────┘
         │
┌────────▼────────┐
│  Orchestrator   │ → Creates work packages for parallel processing
└────────┬────────┘
         │
┌────────▼────────┐
│ Category Workers│ → Generate tasks in parallel (8-32 workers)
└────────┬────────┘
         │
┌────────▼────────┐
│   Aggregator    │ → Combines all worker outputs
└────────┬────────┘
         │
┌────────▼────────┐
│ Excel Generator │ → Creates formatted Excel file
└────────┬────────┘
         │
┌────────▼────────┐
│ Follow-up Handler│ → Manages follow-up analyses
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼───┐ ┌───────┐
│Budget │ │ Cost │ │Manpower│ → Analyzers
└───┬───┘ └──┬───┘ └───┬───┘
    └────────┴─────────┘
         │
┌────────▼────────┐
│Follow-up Excel  │ → Generates analysis Excel files
└─────────────────┘
```

### Key Components

1. **State Management** (`state.py`): Defines the GraphState TypedDict that flows through the workflow
2. **Nodes** (`nodes/`): Individual processing nodes for each workflow step
3. **Configuration** (`config.py`): Azure OpenAI setup and project constants
4. **Prompts** (`prompts/`): Template prompts for LLM interactions

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- Azure OpenAI account with API access
- pip package manager

### Step 1: Clone the Repository

```bash
cd /Users/varshini/Desktop/PM_final
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Set Up Environment Variables

Create a `.env` file in the project root:

```env
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_GPT_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_GPT_DEPLOYMENT=gpt-4o-mini
```

### Step 4: Create Output Directory

The system will automatically create the `output/` directory, but you can create it manually:

```bash
mkdir -p output
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key | Yes |
| `AZURE_OPENAI_GPT_ENDPOINT` | Your Azure OpenAI endpoint URL | Yes |
| `AZURE_OPENAI_GPT_DEPLOYMENT` | Deployment name (default: `gpt-4o-mini`) | No |

### Project Constants

Edit `config.py` to customize:

- **Project Types**: Add or modify supported project types
- **Plan Levels**: Modify plan level options
- **Column Definitions**: Customize Excel output columns
- **Follow-up Questions**: Modify or add follow-up analysis options

## 🚀 Usage

### Interactive CLI Mode

Run the interactive questionnaire:

```bash
python main.py --mode interactive
```

Or simply:

```bash
python main.py
```

The system will:
1. Prompt you for project information
2. Generate the project plan
3. Offer follow-up analyses (budget, cost breakup, manpower)

### Test Mode

Test with pre-defined sample data:

```bash
# Highrise project (High-level Plan)
python main.py --mode test-highrise

# Villa project (Detailed Plan)
python main.py --mode test-villa

# Commercial project (Detailed Plan)
python main.py --mode test-commercial
```

### API Mode

Start the FastAPI server:

```bash
python api.py
```

Or with uvicorn:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

#### API Endpoints

**1. Health Check**
```bash
GET http://localhost:8000/
```

**2. Generate Project Plan**
```bash
POST http://localhost:8000/generate
Content-Type: application/json

{
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
```

**3. Download Excel File**
```bash
GET http://localhost:8000/download/{filename}
```

**4. Get Follow-up Questions**
```bash
GET http://localhost:8000/followup-questions
```

#### Example API Usage

```python
import requests

# Generate plan
response = requests.post("http://localhost:8000/generate", json={
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
})

result = response.json()
print(f"Total tasks: {result['total_tasks']}")
print(f"Excel file: {result['excel_file']}")

# Download file
file_response = requests.get(f"http://localhost:8000/download/{result['excel_file']}")
with open(result['excel_file'], 'wb') as f:
    f.write(file_response.content)
```

## 📁 Project Structure

```
PM_final/
├── main.py                          # Main CLI entry point
├── api.py                           # FastAPI server
├── config.py                        # Configuration and Azure OpenAI setup
├── state.py                         # LangGraph state definitions
├── requirements.txt                 # Python dependencies
├── intake_questionaire.txt          # Questionnaire structure reference
│
├── nodes/                           # Workflow nodes
│   ├── __init__.py
│   ├── questionnaire.py             # Collects user input
│   ├── validation.py                # Validates inputs
│   ├── prompt.py                    # Enriches prompts
│   ├── orchestrator.py              # Creates work packages
│   ├── workers.py                   # Parallel task generation
│   ├── aggregator.py                # Combines worker outputs
│   ├── excel_generator.py           # Generates main Excel
│   ├── followup_handler.py          # Manages follow-up flow
│   ├── followup_analyzers.py        # Budget/Cost/Manpower analyzers
│   └── followup_excel_generator.py  # Generates follow-up Excel files
│
├── prompts/                         # LLM prompt templates
│   ├── fixed_prompt.txt             # Base prompt template
│   ├── budget_analysis_prompt.txt   # Budget analysis prompt
│   ├── cost_breakup_prompt.txt      # Cost breakup prompt
│   └── manpower_analysis_prompt.txt # Manpower analysis prompt
│
├── utils/                           # Utility functions
│   ├── __init__.py
│   └── excel_helper.py              # Excel generation utilities
│
└── output/                          # Generated Excel files
    ├── project_plan_*.xlsx          # Main project plans
    ├── budget_estimate_*.xlsx       # Budget estimates
    ├── cost_breakup_*.xlsx          # Cost breakups
    └── manpower_estimates_*.xlsx    # Manpower estimates
```

## 🔄 Workflow

### Main Workflow Steps

1. **Questionnaire** (`questionnaire_node`)
   - Collects project location, type, scale, start date, and plan level
   - Supports 5 project types with type-specific questions

2. **Validation** (`validation_node`)
   - Validates all inputs
   - Checks required fields
   - Returns validation result

3. **Prompt Enrichment** (`prompt_node`)
   - Loads base prompt template
   - Injects project-specific details
   - Sets date context

4. **Orchestration** (`orchestrator_node`)
   - Determines number of workers (8 for high-level, 32 for detailed)
   - Creates focused work packages
   - Generates worker-specific prompts

5. **Task Generation** (`category_worker_node`)
   - Executes workers in parallel
   - Each worker generates ~13 tasks
   - Tasks follow JSON schema

6. **Aggregation** (`aggregator_node`)
   - Combines all worker outputs
   - Validates task structure
   - Creates unified project plan JSON

7. **Excel Generation** (`excel_generator_node`)
   - Formats data into Excel
   - Uses appropriate columns based on plan level
   - Saves to `output/` directory

8. **Follow-up Handler** (`followup_handler_node`)
   - Presents remaining follow-up options
   - Routes to appropriate analyzer

9. **Follow-up Analyzers** (`budget_analyzer_node`, etc.)
   - Analyzes project plan
   - Generates analysis data

10. **Follow-up Excel Generation** (`followup_excel_generator_node`)
    - Creates analysis Excel files
    - Loops back for more follow-ups or ends

### Plan Levels

**High-level Plan:**
- ~100 tasks
- Columns: Phase Name, Activity Name, Task Name, Task Category, Task Duration
- Focuses on major milestones

**Detailed Plan:**
- ~400 tasks
- Columns: All high-level columns plus:
  - Task Start/End Dates
  - Work Quantity, Rate, UOM
  - Task Description
  - Priority, Predecessor, Dependency Type, Successor
- Includes dependencies and scheduling

## 📊 Output Files

### Main Project Plan

**File Format:** `project_plan_{ProjectType}_{Timestamp}.xlsx`

**High-level Plan Columns:**
- Phase Name
- Activity Name
- Task Name
- Task Category
- Task Duration

**Detailed Plan Columns:**
- Phase Name
- Activity Name
- Task Name
- Task Category
- Task Start Date
- Task End Date
- Work Quantity
- Work Rate
- Work UOM
- Task Description
- Priority
- Predecessor
- Dependency Type
- Successor

### Follow-up Analysis Files

**1. Budget Estimate**
- File: `budget_estimate_{ProjectType}_{Timestamp}.xlsx`
- Columns: Phase, Activity, Cost Head, Budget Type, Apx.Qty, Unit, Rate, Apx.Budget, Contingency %

**2. Cost Breakup**
- File: `cost_breakup_{ProjectType}_{Timestamp}.xlsx`
- Columns: Work Name, Description, Category, Apx.Qty, Unit, Apx. Material Cost, Total Cost

**3. Manpower Estimates**
- File: `manpower_estimates_{ProjectType}_{Timestamp}.xlsx`
- Columns: Activity, Role, Skill Level, No. of Workers, Productivity (Unit/Day), Duration (Days), Man-Days, Apx. Daily Rate, Apx. Cost

## 📦 Dependencies

### Core Dependencies

- **langchain** (>=0.1.0): LangChain framework
- **langchain-openai** (>=0.0.5): Azure OpenAI integration
- **langgraph** (>=0.0.20): Workflow orchestration
- **openai** (>=1.0.0): OpenAI API client
- **python-dotenv** (>=1.0.0): Environment variable management
- **openpyxl** (>=3.1.0): Excel file generation
- **pydantic** (>=2.0.0): Data validation

### API Dependencies

- **fastapi** (>=0.100.0): Web framework
- **uvicorn** (>=0.23.0): ASGI server

### Optional Dependencies

- **reportlab** (>=4.0.0): PDF generation (if needed)

## 🔧 Troubleshooting

### Common Issues

**1. Azure OpenAI Connection Error**
```
Error: Missing Azure OpenAI credentials
```
**Solution:** Ensure `.env` file exists with correct `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_GPT_ENDPOINT`

**2. Module Not Found Error**
```
ModuleNotFoundError: No module named 'langgraph'
```
**Solution:** Install dependencies: `pip install -r requirements.txt`

**3. Excel Generation Error**
```
PermissionError: [Errno 13] Permission denied
```
**Solution:** Ensure `output/` directory exists and is writable

**4. Validation Error**
```
Validation failed: Missing required field
```
**Solution:** Ensure all mandatory questionnaire fields are provided

**5. Low Task Count**
```
Total tasks: 50 (expected 100+)
```
**Solution:** 
- Check orchestrator worker count settings
- Verify LLM is generating tasks correctly
- Check for errors in worker outputs

### Debug Mode

Enable verbose logging by modifying `main.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Optimization

1. **Reduce Workers**: For faster testing, modify `orchestrator.py` to use fewer workers
2. **Skip Follow-ups**: Use `include_followups=False` in `run_with_responses()`
3. **API Timeout**: Increase timeout for large projects in API calls

## 📝 Notes

- The system uses Azure OpenAI GPT-4 models. Ensure you have sufficient quota.
- Excel files are saved with timestamps to prevent overwrites.
- The workflow is stateful - each node receives and updates the GraphState.
- Follow-up analyses are optional and can be skipped.
- All dates are generated based on the current year and project start date.

"""
Prompt Management API Routes
Allows viewing and editing system prompts without code changes
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import json
import os
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/prompts", tags=["prompts"])

# Path to prompts storage
PROMPTS_FILE = os.path.join(os.path.dirname(__file__), "..", "prompts.json")

# In-memory cache for prompts (reload on file change)
_prompts_cache: Optional[Dict] = None
_prompts_mtime: Optional[float] = None


class PromptTemplate(BaseModel):
    """A prompt template with metadata"""
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="What this prompt does")
    template: str = Field(..., description="The actual prompt text with {variables}")
    variables: List[str] = Field(default_factory=list, description="List of variable names used in template")
    updated_at: str = Field(..., description="ISO timestamp of last update")
    updated_by: str = Field(default="system", description="Who last updated this prompt")


class PromptUpdate(BaseModel):
    """Request to update a prompt"""
    template: str = Field(..., description="New prompt template text")
    updated_by: str = Field(default="user", description="Who is updating this prompt")


def load_prompts() -> Dict[str, PromptTemplate]:
    """
    Load prompts from JSON file with caching.
    Reloads if file has been modified.
    """
    global _prompts_cache, _prompts_mtime

    try:
        current_mtime = os.path.getmtime(PROMPTS_FILE)

        # Check if we need to reload
        if _prompts_cache is None or _prompts_mtime != current_mtime:
            with open(PROMPTS_FILE, 'r') as f:
                data = json.load(f)
                _prompts_cache = {
                    key: PromptTemplate(**value)
                    for key, value in data.items()
                }
                _prompts_mtime = current_mtime
                logger.info(f"📝 Loaded {len(_prompts_cache)} prompts from {PROMPTS_FILE}")

        return _prompts_cache

    except FileNotFoundError:
        logger.error(f"Prompts file not found: {PROMPTS_FILE}")
        return {}
    except Exception as e:
        logger.error(f"Error loading prompts: {e}", exc_info=True)
        return {}


def save_prompts(prompts: Dict[str, PromptTemplate]) -> None:
    """Save prompts back to JSON file"""
    try:
        # Convert to dict for JSON serialization
        data = {
            key: value.model_dump()
            for key, value in prompts.items()
        }

        with open(PROMPTS_FILE, 'w') as f:
            json.dump(data, f, indent=2)

        # Invalidate cache
        global _prompts_cache, _prompts_mtime
        _prompts_cache = None
        _prompts_mtime = None

        logger.info(f"💾 Saved {len(prompts)} prompts to {PROMPTS_FILE}")

    except Exception as e:
        logger.error(f"Error saving prompts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save prompts: {str(e)}"
        )


@router.get("", response_model=Dict[str, PromptTemplate])
async def list_prompts():
    """
    List all available prompt templates.
    Returns a dictionary of prompt_id -> PromptTemplate.
    """
    prompts = load_prompts()
    return prompts


@router.get("/{prompt_id}", response_model=PromptTemplate)
async def get_prompt(prompt_id: str):
    """Get a specific prompt template by ID"""
    prompts = load_prompts()

    if prompt_id not in prompts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{prompt_id}' not found"
        )

    return prompts[prompt_id]


@router.put("/{prompt_id}", response_model=PromptTemplate)
async def update_prompt(prompt_id: str, update: PromptUpdate):
    """
    Update a prompt template.
    The new prompt takes effect immediately without container restart.
    """
    prompts = load_prompts()

    if prompt_id not in prompts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{prompt_id}' not found"
        )

    # Update the prompt
    existing = prompts[prompt_id]
    existing.template = update.template
    existing.updated_at = datetime.now(timezone.utc).isoformat()
    existing.updated_by = update.updated_by

    # Save back to file
    save_prompts(prompts)

    logger.info(f"✅ Updated prompt '{prompt_id}' by {update.updated_by}")

    return existing


@router.post("/{prompt_id}/validate")
async def validate_prompt(prompt_id: str, update: PromptUpdate):
    """
    Validate a prompt template without saving it.
    Checks for syntax errors, missing variables, etc.
    """
    prompts = load_prompts()

    if prompt_id not in prompts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{prompt_id}' not found"
        )

    existing = prompts[prompt_id]
    errors = []
    warnings = []

    # Check that required variables are present
    for var in existing.variables:
        if f"{{{var}}}" not in update.template:
            errors.append(f"Missing required variable: {{{var}}}")

    # Check for unknown variables
    import re
    found_vars = set(re.findall(r'\{(\w+)\}', update.template))
    unknown_vars = found_vars - set(existing.variables)
    if unknown_vars:
        warnings.append(f"Unknown variables found: {', '.join(f'{{{v}}}' for v in unknown_vars)}")

    # Check length
    if len(update.template) < 50:
        warnings.append("Prompt seems very short - are you sure it's complete?")
    if len(update.template) > 5000:
        warnings.append("Prompt is very long - consider breaking it down")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "template_length": len(update.template),
        "variables_found": list(found_vars)
    }


@router.get("/{prompt_id}/render")
async def render_prompt(
    prompt_id: str,
    query: Optional[str] = "What is RAG?",
    source_context: Optional[str] = " The context includes 5 research articles.",
    citation_instruction: Optional[str] = "Include citations [1], [2], etc."
):
    """
    Render a prompt with sample variables for preview.
    Useful for testing how the prompt will look with actual data.
    """
    prompts = load_prompts()

    if prompt_id not in prompts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{prompt_id}' not found"
        )

    template = prompts[prompt_id].template

    # Build variable substitution dict
    variables = {
        "query": query,
        "source_context": source_context,
        "citation_instruction": citation_instruction
    }

    # Render template
    try:
        rendered = template.format(**variables)
        return {
            "template": template,
            "variables": variables,
            "rendered": rendered
        }
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing variable for rendering: {str(e)}"
        )


def get_prompt_template(prompt_id: str) -> str:
    """
    Helper function for other modules to get a prompt template.
    Use this in your RAG code instead of hardcoded strings.
    """
    prompts = load_prompts()
    if prompt_id in prompts:
        return prompts[prompt_id].template
    else:
        logger.warning(f"Prompt '{prompt_id}' not found, using default")
        return "You are a helpful assistant. Answer the question based on the provided context."


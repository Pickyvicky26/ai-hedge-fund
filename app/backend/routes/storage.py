from fastapi import APIRouter, HTTPException
import json
from pathlib import Path
from pydantic import BaseModel

from app.backend.models.schemas import ErrorResponse

router = APIRouter(prefix="/storage")

class SaveJsonRequest(BaseModel):
    filename: str
    data: dict


def _build_safe_output_path(filename: str) -> Path:
    requested_path = Path(filename)
    if requested_path.is_absolute():
        raise HTTPException(status_code=400, detail="Absolute paths are not allowed")

    if not filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Only .json files can be written")

    normalized_parts = requested_path.parts
    if any(part in {"..", ""} for part in normalized_parts):
        raise HTTPException(status_code=400, detail="Path traversal is not allowed")

    sanitized_name = requested_path.name
    if sanitized_name != filename:
        raise HTTPException(status_code=400, detail="Nested paths are not allowed")

    project_root = Path(__file__).parent.parent.parent.parent
    outputs_dir = project_root / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    return outputs_dir / sanitized_name

@router.post(
    path="/save-json",
    responses={
        200: {"description": "File saved successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def save_json_file(request: SaveJsonRequest):
    """Save JSON data to the project's /outputs directory."""
    try:
        file_path = _build_safe_output_path(request.filename)
        
        # Save JSON data to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(request.data, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "message": f"File saved successfully to {file_path}",
            "filename": request.filename
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

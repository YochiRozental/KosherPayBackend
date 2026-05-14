from fastapi import HTTPException, status


def ensure_success(result: dict, *, status_code: int = status.HTTP_400_BAD_REQUEST) -> dict:
    if not result.get("success"):
        raise HTTPException(status_code=status_code, detail=result)
    return result

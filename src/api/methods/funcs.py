from fastapi import APIRouter

router = APIRouter(
    prefix='/funcs'
)

@router.post('/calc_free_slot')
async def calculate_free_slot():
    pass


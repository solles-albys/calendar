from fastapi import APIRouter

from lib.api.models.funcs import RCalcFreeTime

router = APIRouter(
    prefix='/funcs'
)


@router.post('/calc_free_slot')
async def calculate_free_slot(request: RCalcFreeTime):
    pass


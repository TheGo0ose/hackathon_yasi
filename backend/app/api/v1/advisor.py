from fastapi import APIRouter

from app.schemas.advisor import AdvisorRequest, AdvisorResponse
from app.services.advisor_service import advisor_service

router = APIRouter()

@router.post("/chat", response_model=AdvisorResponse, summary="Chat with the AI Credit Advisor")
async def chat_with_advisor(request: AdvisorRequest):
    """
    Takes the ML scoring context, chat history, and the user's latest message,
    and returns an AI-generated advice/response to help improve the credit score.
    """
    reply = await advisor_service.get_advice(request)
    return AdvisorResponse(reply=reply)

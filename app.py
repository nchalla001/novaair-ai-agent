from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from knowledge_base import retrieve_policy, model
from sentence_transformers import util
import uuid
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("novaair")

app = FastAPI()

class BookingRequest(BaseModel):
    passenger: str
    flight: str
    status: str


bookings = {
    "NA123": {
        "passenger": "Marcus",
        "flight": "NV101",
        "status": "CANCELLED"
    },
    "NA456": {
        "passenger": "Livia",
        "flight": "NV202",
        "status": "CONFIRMED"
    }
}

@app.post("/bookings")
def create_booking(booking: BookingRequest):
    booking_id = f"NA-{uuid.uuid4()}"
    bookings[booking_id] = booking.model_dump()
    return {
    "booking_id": booking_id,
    **booking.model_dump()
}
@app.get("/bookings/{booking_id}")
def get_booking(booking_id: str):
    booking = bookings.get(booking_id)

    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    return booking

def decide_tool(action: str):
    if action == "get_booking":
        return "GET /bookings/{booking_id}"

    if action == "create_booking":
        return "POST /bookings"

    return "UNKNOWN"
allowed_actions = {
    "get_booking",
    "create_booking"
}

def is_action_allowed(action: str):
    return action in allowed_actions

intent_examples = {
    "POLICY_QUESTION": [
        "What is the baggage policy?",
        "My suitcase never arrived. What should I do?",
        "What are the cancellation rules?",
        "Can I get a refund?",
        "What happens if my checked bag is delayed?",
    ],

    "BOOKING_LOOKUP": [
        "Check booking NA123",
        "Show me my booking status",
        "Can you tell me about my reservation?",
        "What is happening with NA456?",
    ],

    "CANCEL_BOOKING": [
    "Cancel booking NA123",
    "I want to cancel my reservation",
    "Please cancel my flight booking",
    "I no longer want booking NA456",
],

    "UNSUPPORTED": [
        "Who was Augustus?",
        "Tell me a joke",
        "What is the weather today?",
    ]
}

intent_texts = []
intent_labels = []

for intent, examples in intent_examples.items():
    for example in examples:
        intent_texts.append(example)
        intent_labels.append(intent)

intent_embeddings = model.encode(
    intent_texts,
    convert_to_tensor=True
)
def classify_intent(message: str):
    message_embedding = model.encode(
        message,
        convert_to_tensor=True
    )

    scores = util.cos_sim(
        message_embedding,
        intent_embeddings
    )[0]

    best_match_index = scores.argmax().item()
    best_match_score = scores[best_match_index].item()

    if best_match_score < 0.30:
        return "UNSUPPORTED"

    return intent_labels[best_match_index]
def route_request(message: str):
    intent = classify_intent(message)

    if intent == "POLICY_QUESTION":
        return "RAG"

    if intent == "BOOKING_LOOKUP":
        return "TOOL"

    if intent == "CANCEL_BOOKING":
        return "CANCEL"

    return "UNSUPPORTED"


def handle_request(message: str):
    intent = classify_intent(message)
    route = route_request(message)

    logger.info(
        "message=%r intent=%s route=%s",
        message,
        intent,
        route
    )

    if route == "RAG":
        return retrieve_policy(message)

    if route == "TOOL":
        booking_match = re.search(r"\bNA\d+\b", message.upper())

        if booking_match is None:
            return "Please provide a valid NovaAir booking reference."

        booking_id = booking_match.group()

        try:
            return get_booking(booking_id)

        except HTTPException as error:
            if error.status_code == 404:
                return f"I couldn't find booking {booking_id}. Please verify the booking reference and try again."

            raise error

        except TimeoutError:
         return "The booking service is temporarily unavailable. Please try again shortly or contact customer service."
    if route == "CANCEL":
        booking_match = re.search(r"\bNA\d+\b", message.upper())

        if booking_match is None:
            return "Please provide the NovaAir booking reference you want to cancel."

        booking_id = booking_match.group()

        try:
            booking = get_booking(booking_id)

        except HTTPException as error:
            if error.status_code == 404:
                return f"I couldn't find booking {booking_id}. Please verify the booking reference."

            raise error

        except TimeoutError:
            return "The booking service is temporarily unavailable. Please try again shortly."

        if not is_action_allowed("cancel_booking"):
            cancellation_policy = retrieve_policy(
                "What is the NovaAir cancellation policy?"
            )
            logger.info(
            "booking=%s guardrail=BLOCKED outcome=ESCALATED",
            booking_id
            )

            return {
                "booking": booking,
                "message": "I found the booking, but I am not authorized to cancel it automatically. Please contact customer service for assistance.",
                "policy": cancellation_policy
            }
    return "This request is outside the supported NovaAir scope."
eval_cases = [
    ("What is the baggage policy?", "POLICY_QUESTION"),
    ("Show me booking NA123", "BOOKING_LOOKUP"),
    ("Please cancel booking NA456", "CANCEL_BOOKING"),
    ("Who was Augustus?", "UNSUPPORTED"),
    ("Check my booking", "BOOKING_LOOKUP"),
    ("Please cancel my booking", "CANCEL_BOOKING"),
    ("My suitcase never arrived", "POLICY_QUESTION"),
    ("Tell me something interesting", "UNSUPPORTED"),
]

for message, expected_intent in eval_cases:
    actual_intent = classify_intent(message)

    if actual_intent == expected_intent:
        print(f"PASS: {message}")
    else:
        print(
            f"FAIL: {message} -> "
            f"expected {expected_intent}, got {actual_intent}"
        )




from sentence_transformers import SentenceTransformer, util

policies = {
    "baggage": """
    NovaAir allows one carry-on bag and one personal item per passenger.
    Checked baggage fees depend on route and fare class.
    """,

    "cancellation": """
    NovaAir customers may cancel eligible bookings according to fare rules.
    Refund eligibility depends on ticket type and cancellation timing.
    """,

    "lost_baggage": """
    Customers should report lost baggage to NovaAir baggage services.
    Claims should include the baggage tag number and booking reference.
    """
}
model = SentenceTransformer("all-MiniLM-L6-v2")

policy_names = list(policies.keys())
policy_texts = list(policies.values())

policy_embeddings = model.encode(
    policy_texts,
    convert_to_tensor=True
)
def get_policy(topic: str):
    return policies.get(topic)

def retrieve_policy(question: str):
    question_embedding = model.encode(
        question,
        convert_to_tensor=True
    )

    scores = util.cos_sim(
        question_embedding,
        policy_embeddings
    )[0]


    best_match_index = scores.argmax().item()
    best_match_score = scores[best_match_index].item()

    if best_match_score < 0.25:
        return "No relevant NovaAir policy found."

    return policies[policy_names[best_match_index]]

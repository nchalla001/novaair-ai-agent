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
def get_policy(topic: str):
    return policies.get(topic)


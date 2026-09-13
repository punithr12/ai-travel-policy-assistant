def calculate_reimbursement(trip_amount, policy_limit):
    """
    Calculate the reimbursable amount and the amount requiring review.

    Reimbursable amount is the lower of:
    - Actual trip amount
    - Applicable policy limit
    """

    # Validate inputs
    try:
        trip_amount = float(trip_amount)
        policy_limit = float(policy_limit)
    except (ValueError, TypeError):
        return {
            "status": "Invalid",
            "message": "Trip amount and policy limit must be valid numbers."
        }

    if trip_amount < 0:
        return {
            "status": "Invalid",
            "message": "Trip amount cannot be negative."
        }

    if policy_limit < 0:
        return {
            "status": "Invalid",
            "message": "Policy limit cannot be negative."
        }

    # Calculate reimbursement
    reimbursable_amount = min(trip_amount, policy_limit)

    amount_requiring_review = max(
        trip_amount - policy_limit,
        0
    )

    return {
        "status": "Calculated",
        "trip_amount": trip_amount,
        "policy_limit": policy_limit,
        "reimbursable_amount": reimbursable_amount,
        "amount_requiring_review": amount_requiring_review
    }


if __name__ == "__main__":

    print("\nReimbursement Calculator")
    print("=" * 60)

    trip_amount = input("Trip Amount: ")
    policy_limit = input("Policy Limit: ")

    result = calculate_reimbursement(
        trip_amount,
        policy_limit
    )

    print("\nReimbursement Result")
    print("-" * 60)

    for key, value in result.items():
        print(f"{key}: {value}")
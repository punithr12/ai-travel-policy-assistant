from datetime import datetime

try:
    from .employee_tools import check_employee_eligibility
except ImportError:
    from employee_tools import check_employee_eligibility


COUNTRY_LIMITS = {
    "India": 2000,
    "United States": 75
}


def validate_trip(employee_id, trip_type, amount, time):
    """
    Validate an employee travel request using the employee
    eligibility records and applicable travel policy limits.

    Parameters:
        employee_id: Employee ID
        trip_type: Type of trip, e.g. Airport, Office, Customer Meeting
        amount: Trip amount
        time: Trip time in HH:MM format

    Returns:
        dict containing validation result.
    """

    employee_id = employee_id.strip().upper()
    trip_type = trip_type.strip().lower()

    # ---------------------------------------------------------
    # 1. Check employee eligibility
    # ---------------------------------------------------------

    employee = check_employee_eligibility(employee_id)

    if employee["status"] == "Unknown":
        return {
            "employee_id": employee_id,
            "status": "Rejected",
            "reason": "Employee ID was not found in the eligibility records."
        }

    if employee["status"] == "Not Eligible":
        return {
            "employee_id": employee_id,
            "status": "Rejected",
            "reason": "Employee is not eligible for the company-sponsored travel program."
        }

    country = employee["country"]

    # ---------------------------------------------------------
    # 2. Check country policy
    # ---------------------------------------------------------

    if country not in COUNTRY_LIMITS:
        return {
            "employee_id": employee_id,
            "status": "Needs Review",
            "reason": f"No travel limit is defined for country: {country}."
        }

    policy_limit = COUNTRY_LIMITS[country]

    # ---------------------------------------------------------
    # 3. Validate amount
    # ---------------------------------------------------------

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return {
            "employee_id": employee_id,
            "status": "Invalid",
            "reason": "Trip amount must be a valid number."
        }

    if amount < 0:
        return {
            "employee_id": employee_id,
            "status": "Invalid",
            "reason": "Trip amount cannot be negative."
        }

    # ---------------------------------------------------------
    # 4. Validate time
    # ---------------------------------------------------------

    try:
        trip_time = datetime.strptime(time.strip(), "%H:%M").time()
    except ValueError:
        return {
            "employee_id": employee_id,
            "status": "Invalid",
            "reason": "Time must be provided in HH:MM format."
        }

    # ---------------------------------------------------------
    # 5. Check personal trip
    # ---------------------------------------------------------

    personal_trip_types = {
        "personal",
        "family",
        "unrelated"
    }

    if trip_type in personal_trip_types:
        return {
            "employee_id": employee_id,
            "status": "Rejected",
            "reason": "Personal or unrelated travel is not reimbursable under the travel policy."
        }

    # ---------------------------------------------------------
    # 6. Check whether trip type is a supported business trip
    # ---------------------------------------------------------

    allowed_trip_types = {
    "airport",
    "airport ride",
    "home-airport",
    "home airport",
    "office",
    "customer meeting",
    "customer meeting/partner meeting",
    "partner meeting",
    "other business",
    "business"
}

    if trip_type not in allowed_trip_types:
        return {
            "employee_id": employee_id,
            "status": "Needs Review",
            "reason": "The trip type is not clearly covered by the available travel policy."
        }

    # ---------------------------------------------------------
    # 7. Late-night travel
    # ---------------------------------------------------------
    # 22:00 to 06:00 is allowed for approved business travel.
    # It does not automatically make the trip invalid.
    # Normal spending and approval rules still apply.

    late_night = (
        trip_time >= datetime.strptime("22:00", "%H:%M").time()
        or trip_time < datetime.strptime("06:00", "%H:%M").time()
    )

    # ---------------------------------------------------------
    # 8. Employee requires approval
    # ---------------------------------------------------------

    if employee["status"] == "Approval Required":
        return {
            "employee_id": employee_id,
            "status": "Needs Approval",
            "reason": "Employee status requires approval before using the company-sponsored travel program.",
            "country": country,
            "policy_limit": policy_limit,
            "amount": amount,
            "late_night": late_night
        }

    # ---------------------------------------------------------
    # 9. Check spending limit
    # ---------------------------------------------------------

    if amount > policy_limit:
        return {
            "employee_id": employee_id,
            "status": "Needs Approval",
            "reason": (
                f"The trip amount exceeds the standard {country} "
                f"policy limit of {policy_limit}."
            ),
            "country": country,
            "policy_limit": policy_limit,
            "amount": amount,
            "excess_amount": amount - policy_limit,
            "late_night": late_night
        }

    # ---------------------------------------------------------
    # 10. Trip is within policy
    # ---------------------------------------------------------

    return {
        "employee_id": employee_id,
        "status": "Approved",
        "reason": "Trip is within the applicable travel policy.",
        "country": country,
        "policy_limit": policy_limit,
        "amount": amount,
        "late_night": late_night
    }


if __name__ == "__main__":

    print("\nTrip Validation Tool")
    print("=" * 60)

    employee_id = input("Employee ID: ")
    trip_type = input("Trip Type: ")
    amount = input("Amount: ")
    time = input("Time (HH:MM): ")

    result = validate_trip(
        employee_id,
        trip_type,
        amount,
        time
    )

    print("\nValidation Result")
    print("-" * 60)

    for key, value in result.items():
        print(f"{key}: {value}")
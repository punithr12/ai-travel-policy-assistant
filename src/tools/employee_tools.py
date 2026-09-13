import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent
EMPLOYEE_FILE = BASE_DIR / "data" / "employees.csv"


def check_employee_eligibility(employee_id):
    """
    Check employee eligibility using the employee CSV.

    Returns employee ID, country, employee type,
    eligibility status, and manager approval.
    """

    employee_id = employee_id.strip().upper()

    if not employee_id:
        return {
            "employee_id": employee_id,
            "status": "Unknown",
            "message": "Employee ID is required."
        }

    if not EMPLOYEE_FILE.exists():
        raise FileNotFoundError(
            f"Employee file not found: {EMPLOYEE_FILE}"
        )

    with open(
        EMPLOYEE_FILE,
        mode="r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for employee in reader:

            # Match the actual CSV column name
            current_employee_id = employee["Employee ID"].strip().upper()

            if current_employee_id == employee_id:

                return {
                    "employee_id": employee["Employee ID"],
                    "country": employee["Country"],
                    "employment_type": employee["Employee Type"],
                    "status": employee["Status"],
                    "manager_approval": employee["Manager Approval"]
                }

    return {
        "employee_id": employee_id,
        "status": "Unknown",
        "message": "Employee ID not found in the employee eligibility records."
    }


if __name__ == "__main__":

    print("\nEmployee Eligibility Tool")
    print("=" * 60)

    employee_id = input("Enter Employee ID: ")

    result = check_employee_eligibility(employee_id)

    print("\nResult")
    print("-" * 60)

    for key, value in result.items():
        print(f"{key}: {value}")
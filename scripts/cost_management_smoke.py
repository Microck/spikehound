from __future__ import annotations

from azure.auth import get_credential
from azure.auth import get_subscription_id
from azure.cost_management import query_last_7_days_costs_by_resource
from azure.cost_management import rows_to_cost_items


def main() -> None:
    credential = get_credential()
    subscription_id = get_subscription_id()

    result = query_last_7_days_costs_by_resource(credential, subscription_id)
    parsed_rows = rows_to_cost_items(result)
    columns = [
        column.name
        for column in (getattr(result, "columns", None) or [])
        if column.name
    ]
    raw_rows = len(getattr(result, "rows", None) or [])

    print(
        "Cost Management query succeeded "
        f"(rows={raw_rows}, parsed_rows={len(parsed_rows)}, columns={columns})"
    )


if __name__ == "__main__":
    main()

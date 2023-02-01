import bonds.child_lambda_function
import bonds.coordinator_lambda_function
import json


def call_bonds() -> None:
    bonds.child_lambda_function.lambda_handler(
        {
            "Records": [
                {
                    "body": json.dumps(
                        {
                            "from_date": "2010-01-01",
                            "to_date": "2023-02-01",
                            "period": "10Y",
                        }
                    )
                }
            ]
        },
        {},
    )


def call_coordinator() -> None:

    bonds.coordinator_lambda_function.lambda_handler(
        {},
        {},
    )


def main(argv: list[str]) -> None:
    call_bonds()()


if __name__ == "__main__":
    main(["hellow"])

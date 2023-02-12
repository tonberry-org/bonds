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
                            "bond": "US10Y.GBOND",
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

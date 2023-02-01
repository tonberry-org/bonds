import pythonlambdatemplate.child_lambda_function
import json


def main(argv: list[str]) -> None:
    pythonlambdatemplate.child_lambda_function.lambda_handler(
        {
            "Records": [
                {
                    "body": json.dumps(
                        {
                            "from_date": "2023-01-01",
                            "to_date": "2023-01-25",
                            "symbol": "A",
                        }
                    )
                }
            ]
        },
        {},
    )


if __name__ == "__main__":
    main(["hellow"])

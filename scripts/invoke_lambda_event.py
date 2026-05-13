from __future__ import annotations

import json
import sys
from pathlib import Path

from banner_generator.lambda_handler import handler


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/invoke_lambda_event.py EVENT_JSON", file=sys.stderr)
        return 2

    event_path = Path(sys.argv[1])
    response = handler(json.loads(event_path.read_text()))
    response_summary = {
        "statusCode": response.get("statusCode"),
        "isBase64Encoded": response.get("isBase64Encoded"),
        "headers": response.get("headers"),
        "body_length": len(response.get("body", "")),
        "s3": response.get("s3"),
    }
    print(json.dumps(response_summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

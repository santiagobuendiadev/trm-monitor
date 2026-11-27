import os
import json
import sys
from datetime import datetime
from trm_service import TRMService
from rates_service import build_rates

def main():
    service = TRMService()
    result = service.get_current_trm()

    # Generate JSON string
    json_output = json.dumps(result, indent=2)

    # Print to stdout (always)
    print(json_output)

    # Never overwrite the published JSON with an error, and fail the job
    # so the problem shows up in GitHub Actions.
    if not result.get("success"):
        print("TRM fetch failed; trm.json left unchanged.", file=sys.stderr)
        sys.exit(1)

    # Save to file if argument provided
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            with open(file_path, 'w') as f:
                f.write(json_output)
            # print(f"Saved to {file_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error saving to file: {e}", file=sys.stderr)
            sys.exit(1)

    # Optional second argument: other currencies in COP (rates.json).
    # A failing source never fails the job; it is reported in "errors".
    if len(sys.argv) > 2:
        rates_path = sys.argv[2]
        previous = None
        if os.path.exists(rates_path):
            try:
                with open(rates_path) as f:
                    previous = json.load(f)
            except Exception:
                previous = None

        rates = build_rates(result, previous)
        for code, error in rates["errors"].items():
            print(f"Warning: {code} not updated ({error})", file=sys.stderr)

        try:
            with open(rates_path, 'w') as f:
                f.write(json.dumps(rates, indent=2, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Error saving to file: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()

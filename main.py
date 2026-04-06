import os
import json
import sys
from datetime import datetime
from trm_service import TRMService

def main():
    service = TRMService()
    result = service.get_current_trm()
    
    # Generate JSON string
    json_output = json.dumps(result, indent=2)
    
    # Print to stdout (always)
    print(json_output)
    
    # Save to file if argument provided
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            with open(file_path, 'w') as f:
                f.write(json_output)
            # print(f"Saved to {file_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error saving to file: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()

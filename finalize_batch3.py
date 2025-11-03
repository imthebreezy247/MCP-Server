#!/usr/bin/env python3
"""
Finalize batch 3 data - normalize email addresses to lowercase
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.absolute()

def main():
    # Read the batch 3 data
    with open(SCRIPT_DIR / 'aca_batch_3.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Processing {len(data)} records...")

    # Normalize email addresses
    for record in data:
        if record['Email']:
            record['Email'] = record['Email'].lower()

    # Save finalized data
    output_file = SCRIPT_DIR / 'aca_batch_3.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nFinalized data saved to: {output_file}")

    # Print final summary
    print("\nFinal Batch 3 Data (Emails 31-45, consolidated to unique clients):")
    print("=" * 80)
    for i, record in enumerate(data, 1):
        print(f"\n{i}. {record['Name']}")
        print(f"   Policy Number: {record['Policy Number']}")
        print(f"   Phone: {record['Phone']}")
        print(f"   Email: {record['Email']}")
        print(f"   Monthly Premium: {record['Monthly Premium']}")
        print(f"   Application Date: {record['Application Date']}")
        print(f"   Paid to Date: {record['Paid to Date']}")
        print(f"   Gender: {record['Gender']}")
        print(f"   DOB: {record['DOB']} (Age: {record['Age']})")
        print(f"   Address: {record['Address']}")
        print(f"   Date Received: {record['Date Received']}")

if __name__ == "__main__":
    main()

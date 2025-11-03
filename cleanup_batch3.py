#!/usr/bin/env python3
"""
Clean up batch 3 data - consolidate duplicates and keep only complete records
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.absolute()

def main():
    # Read the batch 3 data
    with open(SCRIPT_DIR / 'aca_batch_3.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Total records: {len(data)}")

    # Group by name and consolidate
    consolidated = {}

    for record in data:
        name = record['Name']

        # If we don't have this person yet, or this record has more complete data
        if name not in consolidated:
            consolidated[name] = record
        else:
            # Merge with existing - prefer non-empty values
            existing = consolidated[name]

            # For each field, prefer the value that's not empty
            for key in record:
                if key == 'Notes':
                    # Keep the original subject, not the reply
                    if 'Re:' not in record[key] and 'Re:' in existing[key]:
                        existing[key] = record[key]
                elif not existing[key] and record[key]:
                    existing[key] = record[key]
                # Also update if current record has policy number and existing doesn't
                elif key == 'Policy Number' and record[key] and not existing[key]:
                    existing[key] = record[key]
                # Update other fields if this record is more complete (has policy number)
                elif record.get('Policy Number') and not existing.get('Policy Number'):
                    existing[key] = record[key]

    # Convert back to list
    cleaned_data = list(consolidated.values())

    # Sort by date received (most recent first)
    cleaned_data.sort(key=lambda x: x.get('Date Received', ''), reverse=True)

    print(f"Consolidated records: {len(cleaned_data)}")

    # Save cleaned data
    output_file = SCRIPT_DIR / 'aca_batch_3.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

    print(f"\nCleaned data saved to: {output_file}")

    # Print summary
    print("\nCleaned records:")
    for i, record in enumerate(cleaned_data, 1):
        print(f"\n{i}. {record['Name']}")
        print(f"   Policy: {record['Policy Number']}")
        print(f"   Phone: {record['Phone']}")
        print(f"   Email: {record['Email']}")
        print(f"   Premium: {record['Monthly Premium']}")
        print(f"   DOB: {record['DOB']} (Age: {record['Age']})")
        print(f"   Gender: {record['Gender']}")
        print(f"   Address: {record['Address']}")

if __name__ == "__main__":
    main()

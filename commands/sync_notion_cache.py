import os
import json
import argparse

def create_mock_cache(output_dir):
    """Creates a mock markdown cache of Notion databases for offline use."""
    os.makedirs(output_dir, exist_ok=True)
    
    files = {
        "bid-pipeline.md": "# Bid Pipeline Cache\n\n| Project | Client | Value | Status | Return Date |\n|---|---|---|---|---|\n| Sample Project | Sample Client | €1,000,000 | Live | 2026-09-01 |",
        "subcontractor-directory.md": "# Subcontractor Directory Cache\n\n| Subcontractor | Trade | Rating | Safe-T-Cert | CIRI |\n|---|---|---|---|---|\n| Sample Sub | M&E | ⭐⭐⭐⭐ | Yes | Yes |",
        "crm.md": "# CRM Cache\n\n| Contact | Role | Company | Email | Phone |\n|---|---|---|---|---|\n| John Doe | Architect | Sample Architects | john@example.com | 087 123 4567 |",
        "rfi-log.md": "# RFI Log Cache\n\n| RFI No | Project | Question | Status | Date |\n|---|---|---|---|---|\n| RFI-001 | Sample Project | Query regarding finishes | Open | 2026-06-01 |"
    }
    
    for filename, content in files.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w") as f:
            f.write(content)
        print(f"Created cache file: {filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    create_mock_cache(args.output_dir)

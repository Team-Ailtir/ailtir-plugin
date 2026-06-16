import os
import argparse

def sanitise_name(name):
    """Make a string safe for use as a folder name."""
    return name.replace("/", "_").replace("\\", "_").replace(":", "_").replace(
        '"', "").replace("?", "").replace("*", "").replace("<", "").replace(
        ">", "").replace("|", "").strip()

def create_bid_folders(bid_ref, root_dir="Bids", packages=None, quality_questions=None, has_interviews=False):
    """Creates the definitive Ailtir 9-section bid folder structure directly on disk."""
    
    base_path = os.path.join(root_dir, bid_ref)
    
    # Base static folders
    folders = [
        "0. AI Context",
        "1. Tender Documents/1.1 ITT",
        "1. Tender Documents/1.2 Drawings",
        "1. Tender Documents/1.3 Specification",
        "1. Tender Documents/1.4 Contract",
        "1. Tender Documents/1.5 Pricing Document",
        "1. Tender Documents/1.6 Reports and Surveys",
        "1. Tender Documents/1.7 Addenda",
        "2. Bid Management",
        "3. Commercial/insurance-and-bonds",
        "4. Clarifications/RFIs Issued",
        "4. Clarifications/Responses Received",
        "5. Estimating/5.1 Takeoff",
        "5. Estimating/5.2 Estimate",
        "5. Estimating/5.3 Prelims",
        "5. Estimating/5.4 Subcontractor Quotes",
        "6. Procurement",
        "7. Submission/7.1 PQQ",
        "7. Submission/7.2 Quality Responses",
        "7. Submission/7.3 Supporting Evidence",
        "7. Submission/7.4 Final Submission",
        "8. Site Visit/Photos",
        "8. Site Visit/Notes"
    ]
    
    # Conditional Post-Tender folders
    if has_interviews:
        folders.extend([
            "9. Post-Tender/Interview Preparation",
            "9. Post-Tender/Tender Settlement"
        ])
    
    print(f"Creating Bid Folder: {base_path}")
    
    # Create static folders
    for folder in folders:
        full_path = os.path.join(base_path, folder)
        os.makedirs(full_path, exist_ok=True)
        print(f"  Created: {folder}/")
        
    # Create dynamic Procurement package folders
    if packages:
        for pkg in packages:
            pkg_name = sanitise_name(pkg)
            os.makedirs(os.path.join(base_path, "6. Procurement", pkg_name, "Enquiry Issued"), exist_ok=True)
            os.makedirs(os.path.join(base_path, "6. Procurement", pkg_name, "Quotes Received"), exist_ok=True)
            print(f"  Created: 6. Procurement/{pkg_name}/")
            
    # Create dynamic Quality Response folders
    if quality_questions:
        for q in quality_questions:
            q_name = sanitise_name(q)
            os.makedirs(os.path.join(base_path, "7. Submission/7.2 Quality Responses", q_name), exist_ok=True)
            print(f"  Created: 7. Submission/7.2 Quality Responses/{q_name}/")
        
    # Create the initial README
    readme_path = os.path.join(base_path, "README.md")
    with open(readme_path, "w") as f:
        f.write(f"# {bid_ref}\n\n**Status:** 1. Lead Identified\n**Last Activity:** Folders created\n\n## Received Documents\n- None yet\n\n## Outstanding\n- Review ITT\n- Run Go/No-Go\n")
        
    print(f"\nSuccess. Bid workspace ready at {base_path}/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create Ailtir Bid Folders")
    parser.add_argument("--bid-ref", required=True, help="Bid reference (e.g., 2026-004-ProjectName)")
    parser.add_argument("--root", default="Bids", help="Root directory (default: Bids)")
    parser.add_argument("--packages", default="", help="Comma-separated work package folder names")
    parser.add_argument("--quality-questions", default="", help="Comma-separated quality question folder names")
    parser.add_argument("--has-interviews", action="store_true", help="Include 9. Post-Tender folder")
    
    args = parser.parse_args()
    
    packages_list = [p.strip() for p in args.packages.split(",")] if args.packages else None
    quality_list = [q.strip() for q in args.quality_questions.split(",")] if args.quality_questions else None
    
    create_bid_folders(
        bid_ref=args.bid_ref, 
        root_dir=args.root,
        packages=packages_list,
        quality_questions=quality_list,
        has_interviews=args.has_interviews
    )

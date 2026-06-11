import os
import argparse

def create_workstation(root_dir):
    """Creates the definitive Ailtir workstation folder structure."""
    
    # Define the core directories
    directories = [
        "Context",
        "Context/credentials",
        "Context/notion-cache",
        "Bids",
        "Intelligence",
        "Intelligence/case-studies",
        "Intelligence/method-statements",
        "Intelligence/win-themes",
        "Intelligence/rate-library",
        "Intelligence/lessons-learned",
        "Active Projects",
        "Daily"
    ]
    
    print(f"Creating Ailtir Workstation at: {root_dir}")
    
    # Create directories
    for dir_path in directories:
        full_path = os.path.join(root_dir, dir_path)
        os.makedirs(full_path, exist_ok=True)
        print(f"  Created: {dir_path}/")
        
    # Create placeholder READMEs for future workstations
    active_projects_readme = os.path.join(root_dir, "Active Projects", "README.md")
    if not os.path.exists(active_projects_readme):
        with open(active_projects_readme, "w") as f:
            f.write("# Active Projects\n\nThis directory is a placeholder for the future Ailtir Delivery Workstation (post-award project management, site diary, CVR, payment claims).\n\nFor now, use the Tendering Workstation features in the `Bids/` folder.")
            
    print("\nWorkstation structure created successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create Ailtir Workstation structure")
    parser.add_argument("--path", default=".", help="Root path for the workstation (defaults to current directory)")
    args = parser.parse_args()
    
    create_workstation(args.path)

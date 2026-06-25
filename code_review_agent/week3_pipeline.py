# ❗WEEK - 3

"""Full pipeline to run per file"""

from tools.bug_detector import bug_detector
from tools.fix_generator import fix_generator
from tools.sandbox_validator import apply_fix_to_file, validate_fix_in_docker

def run_week3_pipeline(file_path: str, repo_path: str) -> list[dict]:
    results = []
    
    # Step 1: Detect bugs
    bugs = bug_detector(file_path)
    print(f"Found {len(bugs)} bugs")
    
    for bug in bugs:
        
        # Step 2: Generate fix
        fix = fix_generator(bug)
        
        # Step 3: Apply fix to temp copy and validate in Docker
        temp_dir = apply_fix_to_file(file_path, fix)
        validation = validate_fix_in_docker(repo_path, temp_dir)
        
        results.append({
            "bug": bug,
            "fix": fix,
            "validation": validation,
            "status": "✅ Fix Validated" if validation["passed"] else "❌ Fix Failed"
        })
        
        print(f"Bug {bug['bug_id']} ({bug['severity']}) → {results[-1]['status']}")
    
    return results
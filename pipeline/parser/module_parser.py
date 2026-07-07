import os
from pathlib import Path

# Path to your backend API folder
BACKEND_DIR = Path("backend/api")

class ModuleInfo:
    """
    Represents a backend module and which components it contains.
    """
    def __init__(self, name, has_router, has_schemas, has_service):
        self.name = name
        self.has_router = has_router
        self.has_schemas = has_schemas
        self.has_service = has_service

    def to_dict(self):
        return {
            "router": self.has_router,
            "schemas": self.has_schemas,
            "service": self.has_service
        }


def scan_backend_modules():
    """
    Scans backend/api and returns a list of ModuleInfo objects.
    """
    modules = []

    if not BACKEND_DIR.exists():
        print(f"[ModuleParser] Backend directory not found: {BACKEND_DIR}")
        return modules

    for item in BACKEND_DIR.iterdir():
        if item.is_dir():
            name = item.name
            has_router = (item / "router.py").exists()
            has_schemas = (item / "schemas.py").exists()
            has_service = (item / "service.py").exists()

            modules.append(
                ModuleInfo(
                    name=name,
                    has_router=has_router,
                    has_schemas=has_schemas,
                    has_service=has_service
                )
            )

    return modules


def get_backend_structure():
    """
    Returns a dictionary mapping module names to their components.
    """
    modules = scan_backend_modules()
    return {module.name: module.to_dict() for module in modules}

# ---------------------------------------------------------
# NEXT PARSER STEP: Missing module + missing file detection
# ---------------------------------------------------------

REQUIRED_FILES = ["router.py", "schemas.py", "service.py"]

def detect_missing_modules(structure: dict):
    """
    Returns a list of modules that are missing entirely.
    Example: listings module doesn't exist yet.
    """
    missing = []

    # These are the modules your ecosystem expects
    expected_modules = ["parcels", "listings", "attachments", "search"]

    for module in expected_modules:
        if module not in structure:
            missing.append(module)

    return missing


def detect_missing_files(structure: dict):
    """
    Returns a dict of modules with missing required files.
    Example:
    {
        "listings": ["router.py", "schemas.py"]
    }
    """
    missing = {}

    for module, files in structure.items():
        missing_files = []

        for required in REQUIRED_FILES:
            if not files.get(required.replace(".py", ""), False):
                missing_files.append(required)

        if missing_files:
            missing[module] = missing_files

    return missing


def validate_backend():
    """
    Runs full validation:
    - scans backend
    - detects missing modules
    - detects missing files
    - returns a full validation report
    """
    structure = get_backend_structure()

    report = {
        "structure": structure,
        "missing_modules": detect_missing_modules(structure),
        "missing_files": detect_missing_files(structure),
        "suggestions": []
    }

    # Build suggestions
    for module in report["missing_modules"]:
        report["suggestions"].append(
            f"Module '{module}' is missing. Suggest generating backend module."
        )

    for module, files in report["missing_files"].items():
        for file in files:
            report["suggestions"].append(
                f"Module '{module}' is missing file '{file}'. Suggest generating it from template."
            )

    return report

# ---------------------------------------------------------
# NEXT PARSER STEP: Template selection + creation planning
# ---------------------------------------------------------

# Map required backend files to template names
TEMPLATE_MAP = {
    "router.py": "router_template.py",
    "schemas.py": "schema_template.py",
    "service.py": "service_template.py"
}

def plan_module_creation(missing_modules):
    """
    For modules that do not exist at all, plan full module creation.
    Example output:
    {
        "listings": ["router.py", "schemas.py", "service.py"]
    }
    """
    plan = {}

    for module in missing_modules:
        plan[module] = list(TEMPLATE_MAP.keys())  # all required files

    return plan


def plan_file_creation(missing_files):
    """
    For modules that exist but are missing files, plan file creation.
    Example input:
        {"listings": ["router.py", "schemas.py"]}
    Example output:
        {
            "listings": {
                "router.py": "router_template.py",
                "schemas.py": "schema_template.py"
            }
        }
    """
    plan = {}

    for module, files in missing_files.items():
        plan[module] = {}
        for file in files:
            plan[module][file] = TEMPLATE_MAP[file]

    return plan


def build_creation_plan():
    """
    Combines:
    - missing module detection
    - missing file detection
    - template selection
    - creation planning

    Returns a full actionable plan for the Backend Builder Agent.
    """
    validation = validate_backend()

    missing_modules = validation["missing_modules"]
    missing_files = validation["missing_files"]

    module_creation_plan = plan_module_creation(missing_modules)
    file_creation_plan = plan_file_creation(missing_files)

    return {
        "backend_structure": validation["structure"],
        "missing_modules": missing_modules,
        "missing_files": missing_files,
        "module_creation_plan": module_creation_plan,
        "file_creation_plan": file_creation_plan,
        "suggestions": validation["suggestions"]
    }

# ---------------------------------------------------------
# NEXT PARSER STEP: Template library integration
# ---------------------------------------------------------

from pathlib import Path

TEMPLATE_DIR = Path("pipeline/templates")

def template_exists(template_name: str) -> bool:
    """
    Checks if a template file exists anywhere in the template library.
    Example: router_template.py
    """
    for root, dirs, files in os.walk(TEMPLATE_DIR):
        if template_name in files:
            return True
    return False


def load_template(template_name: str) -> str:
    """
    Loads a template file and returns its contents as a string.
    Example: load_template("router_template.py")
    """
    for root, dirs, files in os.walk(TEMPLATE_DIR):
        if template_name in files:
            template_path = Path(root) / template_name
            return template_path.read_text(encoding="utf-8")

    raise FileNotFoundError(f"Template not found: {template_name}")


def validate_templates():
    """
    Ensures all required templates exist.
    Returns a dict with missing templates and a suggestion list.
    """
    missing = []
    suggestions = []

    for required_file, template_name in TEMPLATE_MAP.items():
        if not template_exists(template_name):
            missing.append(template_name)
            suggestions.append(
                f"Template '{template_name}' is missing. Add it to pipeline/templates."
            )

    return {
        "missing_templates": missing,
        "suggestions": suggestions
    }


def build_template_preview():
    """
    Returns a preview of all templates in the library.
    Useful for agents to know what they can use.
    """
    preview = {}

    for root, dirs, files in os.walk(TEMPLATE_DIR):
        for file in files:
            if file.endswith(".py"):
                template_path = Path(root) / file
                preview[file] = {
                    "path": str(template_path),
                    "size_bytes": template_path.stat().st_size
                }

    return preview


def build_full_parser_report():
    """
    Combines:
    - backend structure
    - missing modules
    - missing files
    - template validation
    - creation plan
    - template preview

    This is the final output the pipeline orchestrator + agents will consume.
    """
    creation_plan = build_creation_plan()
    template_validation = validate_templates()
    template_preview = build_template_preview()

    return {
        "backend": creation_plan,
        "template_validation": template_validation,
        "template_preview": template_preview,
        "ready_for_generation": (
            len(template_validation["missing_templates"]) == 0
        )
    }


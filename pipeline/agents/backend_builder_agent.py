from pathlib import Path
from pipeline.parser.module_parser import build_creation_plan, load_template, TEMPLATE_MAP

class BackendBuilderAgent:
    """
    Generates backend modules and files using templates.
    """

    def __init__(self, backend_dir="backend/api"):
        self.backend_dir = Path(backend_dir)

    def ensure_module_dir(self, module_name):
        module_path = self.backend_dir / module_name
        module_path.mkdir(parents=True, exist_ok=True)
        return module_path

    def write_file(self, module_path, filename, content):
        file_path = module_path / filename
        file_path.write_text(content, encoding="utf-8")
        return str(file_path)

    def generate_backend(self):
        plan = build_creation_plan()

        created_files = []

        # Create missing modules
        for module, files in plan["module_creation_plan"].items():
            module_path = self.ensure_module_dir(module)

            for file in files:
                template_name = TEMPLATE_MAP[file]
                template_content = load_template(template_name)
                created_files.append(
                    self.write_file(module_path, file, template_content)
                )

        # Create missing files for existing modules
        for module, files in plan["file_creation_plan"].items():
            module_path = self.ensure_module_dir(module)

            for file, template_name in files.items():
                template_content = load_template(template_name)
                created_files.append(
                    self.write_file(module_path, file, template_content)
                )

        return {
            "created_files": created_files,
            "modules_created": list(plan["module_creation_plan"].keys()),
            "files_created": plan["file_creation_plan"]
        }

import os
import sys
import subprocess
import glob

class BmakeLang:
    def __init__(self, script_path=None):
        if script_path is None:
            script_path = self.get_default_bmakefile()
        self.rules = {}  # Initialize rules as an empty dictionary
        self.variables = {}  # Dictionary to store variable values
        self.parse_script(script_path)

    def get_default_bmakefile(self):
        if os.path.exists("Bmakefile"):
            return "Bmakefile"
        elif os.path.exists("example.bmake"):
            return "example.bmake"
        else:
            raise FileNotFoundError("No Bmakefile or example.bmake found in the current directory.")

    def parse_script(self, script_path):
        with open(script_path, "r") as file:
            lines = file.readlines()

        current_target = None
        for line in lines:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            elif "=" in line:
                # Variable assignment (e.g., VAR = value)
                var, value = line.split("=", 1)
                self.variables[var.strip()] = value.strip()
            elif ":" in line:
                target, deps = line.split(":", 1)
                current_target = target.strip()
                self.rules[current_target] = {
                    "deps": deps.strip().split(),
                    "commands": []
                }
            elif line.startswith("    ") and current_target:
                self.rules[current_target]["commands"].append(line.strip())

        # Debugging: Print all parsed rules and variables
        print("Parsed rules:")
        for target, details in self.rules.items():
            print(f"Target: {target}")
            print(f"Dependencies: {details['deps']}")
            print(f"Commands: {details['commands']}")

        print("Parsed variables:")
        for var, value in self.variables.items():
            print(f"{var} = {value}")

    def expand_variables(self, line):
        # Expand variables like $(VAR) to actual value
        for var, value in self.variables.items():
            line = line.replace(f"$({var})", value)
        return line

    def evaluate_make_functions(self, line):
        # Replace $(wildcard ...) with actual files
        if "$(wildcard" in line:
            start = line.find("$(wildcard") + len("$(wildcard")
            end = line.find(")", start)
            pattern = line[start:end].strip()
            files = " ".join(glob.glob(pattern))  # Use glob to match files
            line = line.replace(f"$(wildcard{pattern})", files)

        # Replace $(patsubst ...) with actual substitutions
        if "$(patsubst" in line:
            start = line.find("$(patsubst") + len("$(patsubst")
            end = line.find(")", start)
            pattern = line[start:end].strip()
            parts = pattern.split(",", 2)
            if len(parts) == 3:
                old, new, path = parts
                # Perform the replacement
                new_line = path.replace(old, new)
                line = line.replace(f"$(patsubst{pattern})", new_line)

        return line

    def execute(self, target):
        if target not in self.rules:
            raise ValueError(f"Target '{target}' not defined.")

        print(f"Executing target: {target}")

        # Execute the commands for the target
        for command in self.rules[target]["commands"]:
            command = self.expand_variables(command)  # Expand simple variables
            command = self.evaluate_make_functions(command)  # Handle make functions
            print(f"Running command: {command}")
            try:
                result = subprocess.run(command, shell=True, check=True, capture_output=True)
                print(f"Command output: {result.stdout.decode()}")
                print(f"Command execution finished with return code: {result.returncode}")
            except subprocess.CalledProcessError as e:
                print(f"Command failed with error: {e.stderr.decode()}")
                break

# Main execution
if __name__ == "__main__":
    script_path = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        bmake = BmakeLang(script_path)
        target = sys.argv[2] if len(sys.argv) > 2 else "all"
        bmake.execute(target)
    except Exception as e:
        print(f"Error: {e}")

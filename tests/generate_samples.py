#!/usr/bin/env python3
import os
import subprocess

# C source template
C_TEMPLATE_PARENT = """
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>

void spawn_child(const char *child_name) {{
    if (fork() == 0) {{
        execlp(child_name, child_name, NULL);
        perror("execlp failed");
        exit(1);
    }}
}}

int main() {{
    {child_processes}
    while (1) {{
        printf("{message}\\n");
        sleep(5);
    }}
    return 0;
}}
"""

C_TEMPLATE_CHILD = """
#include <stdio.h>
#include <unistd.h>

int main() {{
    while (1) {{
        printf("{message}\\n");
        sleep(5);
    }}
    return 0;
}}
"""

# Directory for the executables
OUTPUT_DIR = "tests"
SOURCE_DIR = "source_files"  # Temporary directory for C source files

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SOURCE_DIR, exist_ok=True)

# Define sample programs
SAMPLES = [
    {"name": "sample_one", "message": "Sample One Running...", "children": True},
    {"name": "sample_two", "message": "Sample Two Running...", "children": False},
    {"name": "sample_three", "message": "Sample Three Running...", "children": True},
    {"name": "sample_four", "message": "Sample Four Running...", "children": False},
    {"name": "sample_five", "message": "Sample Five Running...", "children": True},
]

def create_source_file(name, message, is_parent, child_processes=""):
    """Create a C source file for the given sample."""
    if is_parent:
        source_code = C_TEMPLATE_PARENT.format(
            message=message,
            child_processes=child_processes
        )
    else:
        source_code = C_TEMPLATE_CHILD.format(message=message)

    source_file = os.path.join(SOURCE_DIR, f"{name}.c")
    with open(source_file, "w") as f:
        f.write(source_code)
    return source_file

def compile_source_file(source_file, output_file):
    """Compile the C source file into an executable."""
    try:
        subprocess.run(
            ["gcc", "-o", output_file, source_file],
            check=True
        )
        print(f"Compiled {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error compiling {source_file}: {e}")

def clean_up_source_files():
    """Delete all C source files after compilation."""
    for file in os.listdir(SOURCE_DIR):
        file_path = os.path.join(SOURCE_DIR, file)
        os.remove(file_path)
    os.rmdir(SOURCE_DIR)
    print("Source files cleaned up.")

def main():
    for sample in SAMPLES:
        name = sample["name"]
        message = sample["message"]
        is_parent = sample["children"]

        # If odd-numbered process, generate child processes
        child_processes = ""
        if is_parent:
            for i in range(1, 4):
                child_name = f"{name}.{i}"
                child_message = f"{child_name} Running..."
                child_source_file = create_source_file(child_name, child_message, is_parent=False)
                child_output_file = os.path.join(OUTPUT_DIR, child_name)
                compile_source_file(child_source_file, child_output_file)
                child_processes += f'spawn_child("{child_output_file}");\n    '

        # Create the parent source file
        source_file = create_source_file(name, message, is_parent=True, child_processes=child_processes)
        output_file = os.path.join(OUTPUT_DIR, name)
        compile_source_file(source_file, output_file)

    # Clean up source files
    clean_up_source_files()

if __name__ == "__main__":
    main()

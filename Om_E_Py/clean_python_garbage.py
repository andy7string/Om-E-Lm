"""
clean_python_garbage.py

Recursively remove Python build artifacts and cache files from the given directory.
Removes: __pycache__, *.pyc, *.pyo, .DS_Store, *.egg-info
Leaves the venv directory and .log files untouched.

USAGE (from command line):
    python clean_python_garbage.py
    # or specify a directory:
    python clean_python_garbage.py /path/to/your/project
      python clean_python_garbage.py .
      python clean_python_garbage.py /Users/andy7string/Projects/Om-E-py
"""
import os
import shutil


def remove_python_garbage(root_dir='.'):  # Main cleanup function
    """
    Recursively remove Python build artifacts and cache files from the given directory.
    Removes: __pycache__, *.pyc, *.pyo, .DS_Store, *.egg-info
    Leaves the venv directory and .log files untouched.
    """
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip the venv directory
        if 'venv' in dirnames:
            dirnames.remove('venv')
        # Remove __pycache__ directories
        if '__pycache__' in dirnames:
            pycache_path = os.path.join(dirpath, '__pycache__')
            print(f"Removing directory: {pycache_path}")
            shutil.rmtree(pycache_path, ignore_errors=True)
            dirnames.remove('__pycache__')
        # Remove _pycache_ directories (non-standard, just in case)
        if '_pycache_' in dirnames:
            pycache_path = os.path.join(dirpath, '_pycache_')
            print(f"Removing directory: {pycache_path}")
            shutil.rmtree(pycache_path, ignore_errors=True)
            dirnames.remove('_pycache_')
        # Remove .egg-info directories
        for d in dirnames[:]:
            if d.endswith('.egg-info'):
                egg_info_path = os.path.join(dirpath, d)
                print(f"Removing directory: {egg_info_path}")
                shutil.rmtree(egg_info_path, ignore_errors=True)
                dirnames.remove(d)
        # Remove unwanted files (but not .log files)
        for f in filenames:
            if f.endswith(('.pyc', '.pyo')) or f == '.DS_Store':
                file_path = os.path.join(dirpath, f)
                print(f"Removing file: {file_path}")
                os.remove(file_path)

if __name__ == "__main__":
    # Run as: python clean_python_garbage.py [optional_path]
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    remove_python_garbage(path) 
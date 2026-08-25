import os, py_compile, sys

errors = []
checked = 0
file_list = []

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('.venv', '__pycache__', '.pytest_cache', 'node_modules')]
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            checked += 1
            file_list.append(path)
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append((path, str(e)))

print(f'Checked {checked} Python files')
if errors:
    print(f'ERRORS in {len(errors)} files:')
    for path, err in errors:
        print(f'  {path}: {err}')
else:
    print('All Python files passed syntax check')

print('\n--- All Python files found ---')
for f in sorted(file_list):
    print(f'  {f}')

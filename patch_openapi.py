import re
import glob

routers = glob.glob(r'd:\SIH PROJECT AAROH\AAROH\backend\api\v1\*.py')
for filepath in routers:
    if 'router.py' in filepath or '__init__.py' in filepath:
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if 'common_responses' not in content:
        import_stmt = '\nfrom backend.schemas.error import common_responses\n'
        content = content.replace('from fastapi import', import_stmt.strip() + '\nfrom fastapi import', 1)
        
    # Match the decorator and the first string argument (the path)
    # e.g., @router.get("/ready"
    new_content = re.sub(
        r'(@router\.(?:get|post|patch|put|delete)\(\s*["\'][^"\']+["\'])',
        r'\1, responses=common_responses',
        content
    )
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Injected OpenAPI responses in', filepath)

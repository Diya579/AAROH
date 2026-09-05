import os

filepath = r'd:\SIH PROJECT AAROH\AAROH\backend\api\v1\analytics.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add check to analytics_state
state_check = '''    if user.role == "STATE_OFFICIAL" and user.state != state:
        from backend.core.errors import raise_forbidden
        raise_forbidden("OUT_OF_SCOPE", "Cannot access analytics for a different state.")
'''
content = content.replace('    case_ids = [\n        r.id for r in db.query(Case.id).filter(Case.state == state).all()\n    ]', state_check + '    case_ids = [\n        r.id for r in db.query(Case.id).filter(Case.state == state).all()\n    ]')

# Add check to analytics_district
district_check = '''    if user.role == "DISTRICT_OFFICIAL" and user.district != district:
        from backend.core.errors import raise_forbidden
        raise_forbidden("OUT_OF_SCOPE", "Cannot access analytics for a different district.")
'''
content = content.replace('    case_ids = [\n        r.id for r in db.query(Case.id).filter(Case.district == district).all()\n    ]', district_check + '    case_ids = [\n        r.id for r in db.query(Case.id).filter(Case.district == district).all()\n    ]')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('Analytics RBAC restored.')

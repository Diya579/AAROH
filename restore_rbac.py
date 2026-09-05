import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

base_dir = r"d:\SIH PROJECT AAROH\AAROH\backend\api\v1"

# consents.py
replace_in_file(os.path.join(base_dir, 'consents.py'), [
    ('row = consent_service.get_consent(db, case_id)', 'verify_case_id_access(case_id, user, db)\n    row = consent_service.get_consent(db, case_id)')
])

# events.py
replace_in_file(os.path.join(base_dir, 'events.py'), [
    ('return event_service.list_events(db, case_id=case_id', 'return event_service.list_events(db, user=user, case_id=case_id'),
    ('raise_not_found("Event", event_id)\n    return row', 'raise_not_found("Event", event_id)\n    verify_case_id_access(row.case_id, user, db)\n    return row'),
    ('from backend.core.security import get_current_user, require_role', 'from backend.core.security import get_current_user, require_role, verify_case_id_access')
])

# interactions.py
replace_in_file(os.path.join(base_dir, 'interactions.py'), [
    ('return interaction_service.list_interactions(db, case_id=case_id', 'return interaction_service.list_interactions(db, user=user, case_id=case_id'),
    ('detail=f"Interaction with id {interaction_id} not found.",\n        )\n    return row', 'detail=f"Interaction with id {interaction_id} not found.",\n        )\n    verify_case_id_access(row.case_id, user, db)\n    return row'),
    ('detail=f"Interaction with id {interaction_id} not found.",\n        )', 'detail=f"Interaction with id {interaction_id} not found.",\n        )\n\n    verify_case_id_access(interaction.case_id, user, db)'),
    ('from backend.core.security import get_current_user, require_role', 'from backend.core.security import get_current_user, require_role, verify_case_id_access')
])

# interventions.py
replace_in_file(os.path.join(base_dir, 'interventions.py'), [
    ('return intervention_service.get_interventions(db, case_id=case_id', 'return intervention_service.get_interventions(db, user=user, case_id=case_id'),
    ('return intervention_service.get_outcomes(db, case_id=case_id', 'return intervention_service.get_outcomes(db, user=user, case_id=case_id'),
    ('row = intervention_service.update_intervention(db, intervention_id, payload)\n    if not row:\n        raise_not_found("Intervention", intervention_id)\n    return row', 'existing = intervention_service.get_intervention(db, intervention_id)\n    if not existing:\n        raise_not_found("Intervention", intervention_id)\n        \n    verify_case_id_access(existing.case_id, user, db)\n\n    row = intervention_service.update_intervention(db, intervention_id, payload)\n    return row'),
    ('from backend.core.security import get_current_user, require_role', 'from backend.core.security import get_current_user, require_role, verify_case_id_access')
])

# predictions.py
replace_in_file(os.path.join(base_dir, 'predictions.py'), [
    ('return prediction_service.get_predictions_by_case(db, case_id=case_id', 'verify_case_id_access(case_id, user, db)\n    return prediction_service.get_predictions_by_case(db, case_id=case_id'),
    ('from backend.core.security import get_current_user, require_role', 'from backend.core.security import get_current_user, require_role, verify_case_id_access')
])

# cases.py - check if it needs list_cases
replace_in_file(os.path.join(base_dir, 'cases.py'), [
    ('return case_service.list_cases(db, ', 'return case_service.list_cases(db, user=user, '),
    ('row = case_service.get_case(db, case_id)\n    if row is None:\n        raise_not_found("Case", case_id)\n    return row', 'row = case_service.get_case(db, case_id)\n    if row is None:\n        raise_not_found("Case", case_id)\n    verify_case_id_access(row.id, user, db)\n    return row'),
    ('row = case_service.update_case(db, case_id, payload)\n    if not row:\n        raise_not_found("Case", case_id)\n    return row', 'existing = case_service.get_case(db, case_id)\n    if not existing:\n        raise_not_found("Case", case_id)\n    verify_case_id_access(existing.id, user, db)\n    row = case_service.update_case(db, case_id, payload)\n    return row')
])

print("RBAC fixes restored!")

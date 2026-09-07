# AAROH — Demo Credentials

> **WARNING**: These are synthetic demo accounts for hackathon testing only.
> All data is synthetic. No real victim information is used.
> Do NOT use these credentials in production.

## Provisioning

Run the seeding script from the project root:

```bash
python -m backend.seed_users
```

This script is idempotent — it skips users that already exist.

## Demo Accounts

| Username            | Password               | Role                | Scope                          |
|---------------------|------------------------|---------------------|--------------------------------|
| `victim1`           | `demo-victim-001`      | VICTIM              | Own case (AAROH-001)           |
| `counsellor1`       | `demo-counsellor-001`  | COUNSELLOR          | Assigned cases only            |
| `district_pune`     | `demo-district-001`    | DISTRICT_OFFICIAL   | Pune district only             |
| `state_maharashtra` | `demo-state-001`       | STATE_OFFICIAL      | Maharashtra state only         |
| `national1`         | `demo-national-001`    | NATIONAL_OFFICIAL   | All states (national mandate)  |
| `admin1`            | `demo-admin-001`       | ADMIN               | Administrative scope           |

## Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin1", "password": "demo-admin-001"}' \
  -c cookies.txt
```

## Check Identity

```bash
curl http://localhost:8000/api/v1/auth/me -b cookies.txt
```

## Logout

```bash
# Read CSRF token from cookie file, then:
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "X-CSRF-Token: <csrf_token_from_cookie>" \
  -b cookies.txt
```

## Security Notes

- Passwords are hashed with **Argon2id** before storage.
- Roles are assigned **server-side** — the client cannot choose or override roles.
- Sessions are **HttpOnly** cookies — not readable by JavaScript.
- CSRF protection is enforced for all state-changing requests.
- There is **no public registration endpoint**.

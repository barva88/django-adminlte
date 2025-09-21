Exams app

Endpoints:
- HTML:
  - /exams/ -> dashboard
  - /exams/list/ -> exam list
  - /exams/take/<id>/ -> take exam
  - /exams/result/<id>/ -> result
- API:
  - /exams/api/analytics/users_by_state/
  - /exams/api/analytics/monthly_revenue/
  - /exams/api/analytics/attempts_summary/

Fixtures: `apps/exams/fixtures/seed_exams.json`

Notes:
- Requires `apps.exams` entry in INSTALLED_APPS (added).
- Uses AdminLTE base templates (extends `layouts/base.html`).
- Stripe integration is optional - configure `STRIPE_PUBLIC_KEY` and `STRIPE_SECRET_KEY` in .env.

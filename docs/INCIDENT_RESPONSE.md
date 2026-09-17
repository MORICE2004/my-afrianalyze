# Incident Response & Rollback

## How to Rollback
1. Revert the problematic commit in main.
2. Push the revert. GitHub Actions will automatically rebuild and deploy the prior stable image to Cloud Run.

## How to Restore Database
- Cloud SQL automated backups occur daily. Use the GCP Console to select the instance and click 'Restore' to the last known good PITR (Point-In-Time Recovery) state.

## Disable External Integrations
- To temporarily halt external LLM queries, set APP_ENV=MAINTENANCE in the Secret Manager. The Mock Firewall will block jobs from hitting OpenAI/Anthropic.

## Stop Research Jobs
- Flush the Redis queue: edis-cli FLUSHALL.
- Restart Celery workers to terminate zombie tasks.

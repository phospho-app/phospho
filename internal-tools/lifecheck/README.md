# lifecheck

Check if the API are alive and alert on slack if not.

## Deployment

This lifecheck is deployed as a [GCP cloud function](https://cloud.google.com/functions/docs/deploy) triggered by [GCP scheduler](https://cloud.google.com/scheduler/docs/creating#gcloud).

It is run every 5min, according to the policy set up in [the github action](../../.github/workflows/internal-lifecheck-deploy.yml)

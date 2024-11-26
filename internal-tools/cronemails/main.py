import logging
import os
from datetime import datetime
from typing import List

import functions_framework
from db import (
    check_email_never_sent_for_org,
    save_email_event,
    validate_1_task_event,
    validate_100_tasks_event,
    validate_1000_tasks_event,
    validate_no_task_for_1_week_event,
)
from email_event import EmailEvent

# Import email templates
from email_templates import (
    email_1_task,
    email_100_tasks,
    email_1000_tasks,
    email_no_task_for_1_week,
)
from email_weekly_report import weekly_report_criterias, write_weekly_report
from organizations import fetch_organizations

logging.basicConfig(level=logging.INFO)  # TODO : change to INFO
logger = logging.getLogger(__name__)

logger.info("Loaded environment variables")
logger.info(f"MONGO DB NAME : {os.getenv('MONGODB_NAME')}")

### SETUP ###

### Define the different events triggers ###


event_1_task = EmailEvent(
    event_name="first_task_logged",
    email_subject="First task logged on phospho",
    email_content=email_1_task,
    is_true_for_org=validate_1_task_event,
)
event_100_tasks = EmailEvent(
    event_name="100_tasks_logged",
    email_subject="100 tasks logged on phospho",
    email_content=email_100_tasks,
    is_true_for_org=validate_100_tasks_event,
)
event_1000_tasks = EmailEvent(
    event_name="1000_tasks_logged",
    email_subject="1000 tasks logged on phospho",
    email_content=email_1000_tasks,
    is_true_for_org=validate_1000_tasks_event,
)
event_no_task_for_1_week = EmailEvent(
    event_name="no_task_for_1_week",
    email_subject="No task logged for 1 week",
    email_content=email_no_task_for_1_week,
    is_true_for_org=validate_no_task_for_1_week_event,
)
events: List[EmailEvent] = [
    event_1_task,
    event_100_tasks,
    event_1000_tasks,
    event_no_task_for_1_week,
]


logger.info(f"{len(events)} events setup")


@functions_framework.http
def main(request):
    """
    Main HTTP Cloud Function, triggered by the CRON scheduler
    """
    logger.info("Cron job started.")
    # Fetch all the organizations from propelAuth
    organizations = fetch_organizations()

    count_of_triggered_events = 0

    for org in organizations:
        org_id = org["org_id"]

        # On Monday, send a weekly report.
        date = datetime.now()
        if date.weekday() == 0:
            logger.info(f"Checking sending weekly report to org {org_id}")
            event_name = f"weekly_report_{date.strftime('%Y-%m-%d')}"
            if check_email_never_sent_for_org(event_name, org_id):
                content = write_weekly_report(org_id)
                weekly_report_email_event = EmailEvent(
                    event_name=event_name,
                    email_subject="Your phospho weekly report",
                    email_content=content,
                    is_true_for_org=lambda org_id: weekly_report_criterias(
                        org_id, content
                    ),
                )
                # Don't sent the other events
                if weekly_report_email_event.is_true_for_org(org_id):
                    count_of_triggered_events += 1
                    weekly_report_email_event.send_email(org_id)
                    save_email_event(
                        weekly_report_email_event.event_name,
                        org_id,
                        weekly_report_email_event.email_subject,
                        weekly_report_email_event.email_content,
                    )
                    continue

        # Check all events
        for event in events:
            if event.is_true_for_org(org_id):
                logger.debug(f"Event {event.event_name} is true for org {org_id}")
                if check_email_never_sent_for_org(event.event_name, org_id):
                    count_of_triggered_events += 1
                    logger.debug(f"Never sent {event.event_name} to the org {org_id}")
                    # At this point, the event is validated, and the users of the org didn't receive the email
                    event.send_email(org_id)
                    save_email_event(
                        event.event_name,
                        org_id,
                        event.email_subject,
                        event.email_content,
                    )
                    # No need to check the other events for this org
                    break

    logger.info("Cron job finished.")

    return {
        "status": "ok",
        "number_of_setup_email_events": len(events),
        "count_of_triggered_events": count_of_triggered_events,
    }

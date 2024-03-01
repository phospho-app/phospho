import logging

from db import get_last_week_kpis, orga_nb_tasks_last_week

logger = logging.getLogger(__name__)


def write_weekly_report(org_id: str):
    """
    Write the weekly report for the organization

    The weekly report is a summary of the KPIs of the organization for the last week.
    1. Welcome message,
    2. List the KPIs. If the KPI is a dict, it will be displayed as a table.
    3. A call to action to log in to the dashboard to see more details.
    4. A thank you message.
    """
    kpis = get_last_week_kpis(org_id)
    if kpis is None:
        logger.info(f"No weekly report to send to org {org_id} (returned None)")
        return None

    if kpis.nb_tasks == 0:
        # No need to send an email if there are no tasks
        logger.info(f"No weekly report to send to org {org_id} (no tasks)")
        return None

    top_three_events = f"""
{kpis.nb_events} events were detected last week. The top events were:
<ol>"""
    # Write the top three events. Account for the case where there are less than 3 events.
    for i, event in enumerate(kpis.top_events):
        # Write the event (inline)
        top_three_events += (
            f"<li>{event['event_name']} with {event['nb_occurrences']} occurrences</li>"
        )
    top_three_events += "</ol>"

    # Write the email content
    email_content = f"""
    <html>
        <body>
            <p>Hi,</p>
            <p>Here is your weekly report for the last week:</p>
            <ul>
                <li>Most active project: {kpis.most_active_project["project_name"]} with {kpis.most_active_project["nb_tasks"]} tasks</li>
                <li>Number of tasks logged: {kpis.nb_tasks}</li>
                <li>Number of sessions logged: {kpis.nb_sessions}</li>
                <li>{top_three_events}</li>
            </ul>
            <p>Get the full story by visiting your <a href="https://platform.phospho.ai">phospho dashboard</a>.</p>
            <p>Best,</p>
            <p>Paul, CEO of phospho</p>
            </body>
    </html>
    """

    # Return the email content
    return email_content


def weekly_report_criterias(org_id: str, content: str) -> bool:
    """
    Only send the weekly reports to organizations that have logged some tasks the
    previous week.
    """
    if content is None:
        logger.info(f"No weekly report to send to org {org_id}")
        return False

    nb_tasks = orga_nb_tasks_last_week(org_id)
    # Only send the weekly report if the organization has logged at least 3 tasks
    # the previous week
    return nb_tasks >= 3

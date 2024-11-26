import os

from propelauth_py import init_base_auth

auth = init_base_auth(
    os.getenv("PROPELAUTH_URL"),
    os.getenv("PROPELAUTH_API_KEY"),
)


def fetch_organizations() -> list:
    """
    Get all the organizations
    Returns a list of organizations in tht propelAuth format
    See : https://docs.propelauth.com/reference/api/org#fetch-orgs
    """
    # Max number of orgs is 99
    first_org_response = auth.fetch_org_by_query(
        page_size=99,
        page_number=0,
    )

    # Get the number of organizations
    number_of_orgs = first_org_response.get("total_orgs")

    organizations = first_org_response.get("orgs")

    if number_of_orgs > 99:
        # Get all the organizations
        for page_number in range(1, number_of_orgs // 99 + 1):
            organizations += auth.fetch_org_by_query(
                page_size=99,
                page_number=page_number,
            ).orgs

    return organizations


def fetch_users_from_org(org_id: str):
    """
    Get all the users of an organization
    Returns a list of users in the propelAuth format
    See : https://docs.propelauth.com/reference/api/org#fetch-users-in-org
    """
    first_user_response = auth.fetch_users_in_org(
        org_id=org_id, page_size=99, page_number=0
    )

    # Get the number of users
    number_of_users = first_user_response.get("total_users")

    users = first_user_response.get("users")

    if number_of_users > 99:
        # Get all the users
        for page_number in range(1, number_of_users // 99 + 1):
            users += auth.fetch_users_in_org(
                org_id=org_id,
                page_size=99,
                page_number=page_number,
            ).users

    return users

import json
import sys
from configparser import ConfigParser

import click
import os
import requests
from tabulate import tabulate

APP_NAME = "jiradmin"
metadata = {"instances": {}}


def read_config():
    cfg = os.path.join(click.get_app_dir(APP_NAME), "instances.ini")
    if not os.path.isfile(cfg):
        message = (
            f"No config file found, please create the file {cfg} like this:"
            "\n\n"
            "[INSTANCE_NAME]\n"
            "url = https://jira.example.com/"
        )
        click.echo(message)
        sys.exit(1)
    parser = ConfigParser()
    parser.read([cfg])
    rv = {}
    for section in parser.sections():
        for key, value in parser.items(section):
            metadata["instances"].setdefault(section, {})[key] = value
    return rv


@click.group()
@click.option(
    "-i", "--instance", default="projektportal", help="Name of the Jira Instance"
)
def cli(instance):
    read_config()
    metadata["chosen_instance"] = instance

    jsessionid, domain, path = steal_cookie_from_qutebrowser(
        metadata["instances"][instance]["url"], "JSESSIONID"
    )

    metadata["cookiejar"] = requests.cookies.RequestsCookieJar()
    metadata["cookiejar"].set(
        "JSESSIONID",
        jsessionid,
        domain=domain,
        path=path,
    )


@cli.group()
@click.argument("project_key")
def projectconfig(project_key):
    metadata["chosen_project"] = project_key


@projectconfig.command(name="browser")
def projectconfig_open_in_browser():
    instance = metadata["chosen_instance"]
    base_url = metadata["instances"][instance]["url"]
    project_key = metadata["chosen_project"]
    click.launch(f"{base_url}/plugins/servlet/project-config/{project_key}/summary")


@projectconfig.command(name="issuetypes")
def projectconfig_list_issuetypes():
    instance = metadata["chosen_instance"]
    base_url = metadata["instances"][instance]["url"]
    project_key = metadata["chosen_project"]
    project_config = requests.get(
        f"{base_url}/rest/api/2/project/{project_key}", cookies=metadata["cookiejar"]
    ).json()
    issue_types = project_config["issueTypes"]
    click.echo(tabulate(issue_types, headers="keys"))


@projectconfig.command(name="components")
def projectconfig_list_components():
    instance = metadata["chosen_instance"]
    base_url = metadata["instances"][instance]["url"]
    project_key = metadata["chosen_project"]
    project_config = requests.get(
        f"{base_url}/rest/api/2/project/{project_key}", cookies=metadata["cookiejar"]
    ).json()
    components = project_config["components"]
    click.echo(tabulate(components, headers="keys"))


@projectconfig.command(name="properties")
def projectconfig_list_properties():
    instance = metadata["chosen_instance"]
    base_url = metadata["instances"][instance]["url"]
    project_key = metadata["chosen_project"]
    property_keys = (
        requests.get(
            f"{base_url}/rest/api/2/project/{project_key}/properties",
            cookies=metadata["cookiejar"],
        )
        .json()
        .get("keys", [])
    )
    properties = []
    for property_key in property_keys:
        key = property_key["key"]
        value = (
            requests.get(
                f"{base_url}/rest/api/2/project/{project_key}/properties/{key}",
                cookies=metadata["cookiejar"],
            )
            .json()
            .get("value", None)
        )
        properties.append([key, json.dumps(value)])

    click.echo(tabulate(properties, headers=["key", "value"]))


def steal_cookie_from_qutebrowser(url, cookiename):
    import sqlite3
    from urllib.parse import urlparse

    o = urlparse(url)

    db_path = f"{os.environ['HOME']}/.local/share/qutebrowser/webengine/Cookies"
    with sqlite3.connect(db_path) as conn:
        query = "SELECT value, host_key, path FROM cookies where host_key = ? AND path = ? and name = ?;"
        return conn.execute(query, (o.netloc, o.path, cookiename)).fetchone()

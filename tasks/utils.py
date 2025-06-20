from github import Github
from django.conf import settings
import requests

def create_github_issue(title, body=None, labels=None):
    g = Github(settings.GITHUB_TOKEN)
    repo = g.get_repo(settings.GITHUB_REPO)
    issue = repo.create_issue(
        title=title,
        body=body or "",
        labels=labels or []
    )
    return issue.html_url



import json
import requests
from django.conf import settings

def send_teams_notification(message: str):
    webhook_url = settings.TEAMS_WEBHOOK_URL
    payload = {
        "text": message
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Teams webhook failed: {e}")
        print(f"Response: {getattr(e.response, 'text', 'No response')}")

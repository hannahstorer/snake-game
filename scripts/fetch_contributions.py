import os
import sys
import json
import urllib.request

GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
            weekday
          }
        }
      }
    }
  }
}
"""
# takes the contribution calendar from github graphql api
def fetch_contributions(username, token):
    body = json.dumps({"query": QUERY, "variables": {"login": username}}).encode()
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "snake-game",
        },
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())

    if "errors" in data:
        raise RuntimeError(data["errors"])
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    # flatten lists of weeks and days into one grid so its easier to work with
    grid = []
    for week in weeks:
        col = [0] * 7
        for day in week["contributionDays"]:
            col[day["weekday"]] = day["contributionCount"]
        grid.append(col)
    return {"grid": grid}

if __name__ == "__main__":
    username = os.environ.get("GH_USERNAME") or (sys.argv[1] if len(sys.argv) > 1 else None)
    token = os.environ.get("GITHUB_TOKEN")

    if not username or not token:
        print("usage: GH_USERNAME=<user> GITHUB_TOKEN=<token> python fetch_contributions.py", file=sys.stderr)
        sys.exit(1)
    result = fetch_contributions(username, token)

# dump into json file so generate_path can read it
    with open("contributions.json", "w") as f:
        json.dump(result, f)
    print(f"fetched {len(result['grid'])} weeks")
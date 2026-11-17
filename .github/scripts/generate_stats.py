#!/usr/bin/env python3
"""Generate a GitHub Mobile App-compatible, Radical-themed GitHub Stats SVG card synced to IST (Asia/Kolkata)."""
import json
import math
import os
import urllib.request
from datetime import datetime, timezone, timedelta

USERNAME = os.environ.get("GH_USERNAME", "SandeepAi369")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
IST = timezone(timedelta(hours=5, minutes=30), name="IST")

QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    name
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes {
        name
        stargazerCount
        forkCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      totalRepositoriesWithContributedCommits
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
      }
    }
  }
}
"""

def fetch_data():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "SandeepAi369-GitHub-Stats-Generator",
        },
    )
    with urllib.request.urlopen(req) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if "errors" in payload:
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    return payload["data"]["user"]

def calculate_rank(stars, commits, prs, issues, repos):
    score = stars * 2.5 + commits * 1.2 + prs * 15 + issues * 5 + repos * 4
    if score >= 1200:
        return "S", min(96, 85 + int((score - 1200) / 200))
    if score >= 700:
        return "A+", 82
    if score >= 400:
        return "A", 72
    return "B+", 60

def generate_svg(user):
    repos = user["repositories"]["nodes"]
    total_stars = sum(r["stargazerCount"] for r in repos)
    cc = user["contributionsCollection"]
    total_commits = cc["totalCommitContributions"] + cc.get("restrictedContributionsCount", 0)
    total_prs = cc["totalPullRequestContributions"]
    total_issues = cc["totalIssueContributions"]
    total_contribs = cc["contributionCalendar"]["totalContributions"]
    contributed_repos = cc["totalRepositoriesWithContributedCommits"]

    lang_sizes = {}
    lang_colors = {}
    for r in repos:
        for edge in r["languages"]["edges"]:
            lname = edge["node"]["name"]
            lcolor = edge["node"]["color"] or "#a9fef7"
            lang_sizes[lname] = lang_sizes.get(lname, 0) + edge["size"]
            lang_colors[lname] = lcolor

    sorted_langs = sorted(lang_sizes.items(), key=lambda x: x[1], reverse=True)[:6]
    total_lang_bytes = sum(sz for _, sz in sorted_langs) or 1

    rank_label, rank_pct = calculate_rank(total_stars, total_commits, total_prs, total_issues, len(repos))
    radius = 44
    circumference = 2 * math.pi * radius
    dash_offset = circumference * (1 - rank_pct / 100.0)

    FONT = "'Segoe UI', Ubuntu, -apple-system, BlinkMacSystemFont, sans-serif"

    # Multi-segment language bar (x=422, width=298) using pure <rect> with inline fills
    bar_width = 298
    bar_x = 422
    bar_y = 54
    segments_svg = []
    cur_x = bar_x
    for idx, (lname, sz) in enumerate(sorted_langs):
        pct = sz / total_lang_bytes
        seg_w = max(4.5, round(pct * bar_width, 2))
        if idx == len(sorted_langs) - 1:
            seg_w = round(bar_x + bar_width - cur_x, 2)
        color = lang_colors[lname]
        segments_svg.append(
            f'<rect x="{cur_x:.2f}" y="{bar_y}" width="{max(0.0, seg_w):.2f}" height="10" fill="{color}"/>'
        )
        cur_x += seg_w

    # 2-column language legend with explicit inline attributes (no CSS classes required)
    legend_svg = []
    for idx, (lname, sz) in enumerate(sorted_langs):
        pct = (sz / total_lang_bytes) * 100.0
        col = idx % 2
        row = idx // 2
        lx = 422 + col * 152
        ly = 92 + row * 31
        color = lang_colors[lname]
        legend_svg.append(
            f'<g transform="translate({lx}, {ly})">'
            f'<circle cx="6" cy="-5" r="5.5" fill="{color}"/>'
            f'<text x="18" y="0" fill="#e4e2f0" font-family="{FONT}" font-size="13.5" font-weight="600">{lname}</text>'
            f'<text x="142" y="0" text-anchor="end" fill="#a9fef7" font-family="{FONT}" font-size="13" font-weight="700">{pct:.1f}%</text>'
            f'</g>'
        )

    now_ist = datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST")

    svg = f'''<svg width="740" height="204" viewBox="0 0 740 204" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SandeepAi369 GitHub Stats">
  <!-- Solid dark Radical background with explicit inline fill & stroke for GitHub Mobile App dark/light mode compatibility -->
  <rect x="1" y="1" width="738" height="202" rx="10" ry="10" fill="#141321" stroke="#292640" stroke-width="1.5"/>

  <!-- Left Section: GitHub Stats -->
  <text x="20" y="34" fill="#fe428e" font-family="{FONT}" font-size="18.5" font-weight="700">SandeepAi369&#39;s GitHub Stats</text>

  <!-- Row 1: Total Stars Earned -->
  <g transform="translate(20, 64)">
    <path transform="translate(0, -14)" fill="#f8d847" fill-rule="evenodd" d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/>
    <text x="25" y="0" fill="#f8d847" font-family="{FONT}" font-size="14.5" font-weight="600">Total Stars Earned:</text>
    <text x="262" y="0" text-anchor="end" fill="#a9fef7" font-family="{FONT}" font-size="15" font-weight="700">{total_stars}</text>
  </g>

  <!-- Row 2: Total Commits (Last Year) -->
  <g transform="translate(20, 93)">
    <path transform="translate(0, -14)" fill="#f8d847" fill-rule="evenodd" d="M10.5 7.75a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zm1.43.75a4.002 4.002 0 01-7.86 0H.75a.75.75 0 110-1.5h3.32a4.001 4.001 0 017.86 0h3.32a.75.75 0 110 1.5h-3.32z"/>
    <text x="25" y="0" fill="#f8d847" font-family="{FONT}" font-size="14.5" font-weight="600">Total Commits (1y):</text>
    <text x="262" y="0" text-anchor="end" fill="#a9fef7" font-family="{FONT}" font-size="15" font-weight="700">{total_commits}</text>
  </g>

  <!-- Row 3: Total Pull Requests -->
  <g transform="translate(20, 122)">
    <path transform="translate(0, -14)" fill="#f8d847" fill-rule="evenodd" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"/>
    <text x="25" y="0" fill="#f8d847" font-family="{FONT}" font-size="14.5" font-weight="600">Total PRs:</text>
    <text x="262" y="0" text-anchor="end" fill="#a9fef7" font-family="{FONT}" font-size="15" font-weight="700">{total_prs}</text>
  </g>

  <!-- Row 4: Total Issues -->
  <g transform="translate(20, 151)">
    <path transform="translate(0, -14)" fill="#f8d847" fill-rule="evenodd" d="M8 9.5a1.5 1.5 0 100-3 1.5 1.5 0 000 3zM8 0a8 8 0 100 16A8 8 0 008 0zM1.5 8a6.5 6.5 0 1113 0 6.5 6.5 0 01-13 0z"/>
    <text x="25" y="0" fill="#f8d847" font-family="{FONT}" font-size="14.5" font-weight="600">Total Issues:</text>
    <text x="262" y="0" text-anchor="end" fill="#a9fef7" font-family="{FONT}" font-size="15" font-weight="700">{total_issues}</text>
  </g>

  <!-- Row 5: Contributed To / Total Contributions -->
  <g transform="translate(20, 180)">
    <path transform="translate(0, -14)" fill="#f8d847" fill-rule="evenodd" d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z"/>
    <text x="25" y="0" fill="#f8d847" font-family="{FONT}" font-size="14.5" font-weight="600">Contributed To (1y):</text>
    <text x="262" y="0" text-anchor="end" fill="#a9fef7" font-family="{FONT}" font-size="15" font-weight="700">{contributed_repos} repos ({total_contribs})</text>
  </g>

  <!-- Rank Circle -->
  <g transform="translate(342, 114)">
    <circle cx="0" cy="0" r="{radius}" stroke="#292640" stroke-width="7.5" fill="none"/>
    <circle cx="0" cy="0" r="{radius}" stroke="#fe428e" stroke-width="7.5" fill="none"
            stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{dash_offset:.2f}"
            stroke-linecap="round" transform="rotate(-90)"/>
    <text x="0" y="6" text-anchor="middle" fill="#a9fef7" font-family="{FONT}" font-size="26" font-weight="800">{rank_label}</text>
    <text x="0" y="24" text-anchor="middle" fill="#fe428e" font-family="{FONT}" font-size="10.5" font-weight="700" letter-spacing="1.2">RANK</text>
  </g>

  <!-- Vertical Divider -->
  <line x1="402" y1="18" x2="402" y2="188" stroke="#292640" stroke-width="1.5"/>

  <!-- Right Section: Top Languages -->
  <text x="422" y="34" fill="#fe428e" font-family="{FONT}" font-size="18.5" font-weight="700">Most Used Languages</text>

  <rect x="{bar_x}" y="{bar_y}" width="{bar_width}" height="10" rx="3" fill="#292640"/>
  <g>
    {"".join(segments_svg)}
  </g>

  {"".join(legend_svg)}

  <text x="422" y="184" fill="#8b86a8" font-family="{FONT}" font-size="11" font-weight="500">Synced: {now_ist} (UTC+05:30)</text>
</svg>
'''
    return svg

def main():
    user = fetch_data()
    svg = generate_svg(user)
    with open("github-stats.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("Generated github-stats.svg successfully.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate a balanced medium-height (840x250), high-contrast Radical-themed GitHub Stats SVG card synced to IST (Asia/Kolkata)."""
import html
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
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if "errors" in payload:
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    user = payload.get("data", {}).get("user")
    if not user:
        raise RuntimeError("GraphQL returned null user data")
    return user

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
    radius = 48
    circumference = 2 * math.pi * radius
    dash_offset = circumference * (1 - rank_pct / 100.0)

    FONT = "'Segoe UI', Ubuntu, -apple-system, BlinkMacSystemFont, sans-serif"

    # Normalized multi-segment language bar (x=510, width=312, right edge=822, 18px right margin)
    bar_width = 312.0
    bar_x = 510.0
    bar_y = 58
    bar_h = 12
    min_seg = 4.5
    raw_widths = [max(min_seg, (sz / total_lang_bytes) * bar_width) for _, sz in sorted_langs]
    scale = bar_width / (sum(raw_widths) or 1.0)
    norm_widths = [round(w * scale, 2) for w in raw_widths]
    if norm_widths:
        norm_widths[-1] = round(bar_width - sum(norm_widths[:-1]), 2)

    segments_svg = []
    cur_x = bar_x
    for (lname, _), seg_w in zip(sorted_langs, norm_widths):
        color = html.escape(lang_colors[lname], quote=True)
        segments_svg.append(
            f'<rect x="{cur_x:.2f}" y="{bar_y}" width="{max(1.0, seg_w):.2f}" height="{bar_h}" fill="{color}"/>'
        )
        cur_x = round(cur_x + seg_w, 2)

    # 2-column language legend (x=510..822, 18px right outer margin)
    legend_svg = []
    for idx, (lname, sz) in enumerate(sorted_langs):
        pct = (sz / total_lang_bytes) * 100.0
        col = idx % 2
        row = idx // 2
        lx = 510 + col * 164
        ly = 102 + row * 36
        color = html.escape(lang_colors[lname], quote=True)
        esc_name = html.escape(lname)
        legend_svg.append(
            f'<g transform="translate({lx}, {ly})">'
            f'<circle cx="6" cy="-5" r="6" fill="{color}"/>'
            f'<text x="18" y="0" fill="#f0eefc" font-family="{FONT}" font-size="15" font-weight="600">{esc_name}</text>'
            f'<text x="148" y="0" text-anchor="end" fill="#a9fef7" font-family="{FONT}" font-size="14.5" font-weight="700">{pct:.1f}%</text>'
            f'</g>'
        )

    now_ist = datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST")

    svg = f"""<svg width="840" height="250" viewBox="0 0 840 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SandeepAi369 GitHub Stats">
  <!-- High-contrast dark Radical card background -->
  <rect x="1.5" y="1.5" width="837" height="247" rx="12" ry="12" fill="#141321" stroke="#342f52" stroke-width="1.8"/>

  <!-- Left Section: GitHub Stats (18px left outer margin, values right-aligned at global x=342) -->
  <text x="18" y="38" fill="#fe428e" font-family="{FONT}" font-size="20" font-weight="800">SandeepAi369&#39;s GitHub Stats</text>

  <!-- Row 1: Total Stars Earned -->
  <g transform="translate(18, 76)">
    <path transform="translate(0, -15) scale(1.15)" fill="#f8d847" fill-rule="evenodd" d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/>
    <text x="26" y="0" fill="#f8d847" font-family="{FONT}" font-size="16" font-weight="600">Total Stars Earned:</text>
    <text x="324" y="0" text-anchor="end" fill="#a9fef7" font-family="{FONT}" font-size="16.5" font-weight="700">{total_stars}</text>
  </g>

  <!-- Row 2: Total Commits (1y) -->
  <g transform="translate(18, 111)">
    <path transform="translate(0, -15) scale(1.15)" fill="#f8d847" fill-rule="evenodd" d="M10.5 7.75a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zm1.43.75a4.002 4.002 0 01-7.86 0H.75a.75.75 0 110-1.5h3.32a4.001 4.001 0 017.86 0h3.32a.75.75 0 110 1.5h-3.32z"/>
    <text x="26" y="0" fill="#f8d847" font-family="{FONT}" font-size="16" font-weight="600">Total Commits (1y):</text>
    <text x="324" y="0" text-anchor="end" fill="#a9fef7" font-family="{FONT}" font-size="16.5" font-weight="700">{total_commits}</text>
  </g>

  <!-- Row 3: Total Pull Requests -->
  <g transform="translate(18, 146)">
    <path transform="translate(0, -15) scale(1.15)" fill="#f8d847" fill-rule="evenodd" d="M7.177 3.073L9.573.677A.25.25 0 0110 .854v4.792a.25.25 0 01-.427.177L7.177 3.427a.25.25 0 010-.354zM3.75 2.5a.75.75 0 100 1.5.75.75 0 000-1.5zm-2.25.75a2.25 2.25 0 113 2.122v5.256a2.251 2.251 0 11-1.5 0V5.372A2.25 2.25 0 011.5 3.25zM11 2.5h-1V4h1a1 1 0 011 1v5.628a2.251 2.251 0 101.5 0V5A2.5 2.5 0 0011 2.5zm1 10.25a.75.75 0 111.5 0 .75.75 0 01-1.5 0zM3.75 12a.75.75 0 100 1.5.75.75 0 000-1.5z"/>
    <text x="26" y="0" fill="#f8d847" font-family="{FONT}" font-size="16" font-weight="600">Total PRs:</text>
    <text x="324" y="0" text-anchor="end" fill="#a9fef7" font-family="{FONT}" font-size="16.5" font-weight="700">{total_prs}</text>
  </g>

  <!-- Row 4: Total Issues -->
  <g transform="translate(18, 181)">
    <path transform="translate(0, -15) scale(1.15)" fill="#f8d847" fill-rule="evenodd" d="M8 9.5a1.5 1.5 0 100-3 1.5 1.5 0 000 3zM8 0a8 8 0 100 16A8 8 0 008 0zM1.5 8a6.5 6.5 0 1113 0 6.5 6.5 0 01-13 0z"/>
    <text x="26" y="0" fill="#f8d847" font-family="{FONT}" font-size="16" font-weight="600">Total Issues:</text>
    <text x="324" y="0" text-anchor="end" fill="#a9fef7" font-family="{FONT}" font-size="16.5" font-weight="700">{total_issues}</text>
  </g>

  <!-- Row 5: Contributed To (1y) -->
  <g transform="translate(18, 216)">
    <path transform="translate(0, -15) scale(1.15)" fill="#f8d847" fill-rule="evenodd" d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z"/>
    <text x="26" y="0" fill="#f8d847" font-family="{FONT}" font-size="16" font-weight="600">Contributed To (1y):</text>
    <text x="324" y="0" text-anchor="end" fill="#a9fef7" font-family="{FONT}" font-size="16.5" font-weight="700">{contributed_repos} repos ({total_contribs})</text>
  </g>

  <!-- Rank Circle (center x=416, y=140; outer bounds x=364..468, y=88..192) -->
  <g transform="translate(416, 140)">
    <circle cx="0" cy="0" r="{radius}" stroke="#292640" stroke-width="8" fill="none"/>
    <circle cx="0" cy="0" r="{radius}" stroke="#fe428e" stroke-width="8" fill="none"
            stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{dash_offset:.2f}"
            stroke-linecap="round" transform="rotate(-90)"/>
    <text x="0" y="6" text-anchor="middle" fill="#a9fef7" font-family="{FONT}" font-size="30" font-weight="800">{rank_label}</text>
    <text x="0" y="25" text-anchor="middle" fill="#fe428e" font-family="{FONT}" font-size="11.5" font-weight="700" letter-spacing="1.4">RANK</text>
  </g>

  <!-- Vertical Divider -->
  <line x1="490" y1="22" x2="490" y2="228" stroke="#292640" stroke-width="1.8"/>

  <!-- Right Section: Top Languages (x=510..822, 18px right outer margin) -->
  <text x="510" y="38" fill="#fe428e" font-family="{FONT}" font-size="20" font-weight="800">Most Used Languages</text>

  <rect x="{bar_x:.0f}" y="{bar_y}" width="{bar_width:.0f}" height="{bar_h}" rx="4" fill="#292640"/>
  <g>
    {"".join(segments_svg)}
  </g>

  {"".join(legend_svg)}

  <text x="510" y="216" fill="#9e98bd" font-family="{FONT}" font-size="12" font-weight="600">Synced: {now_ist} (UTC+05:30)</text>
</svg>
"""
    return svg

def main():
    user = fetch_data()
    svg = generate_svg(user)
    with open("github-stats.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("Generated github-stats.svg successfully.")

if __name__ == "__main__":
    main()

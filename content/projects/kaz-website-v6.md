---
title: "Kaz Professional Website V6"
description: "A maintainable portfolio rebuilt around accurate career evidence, separate professional and personal routes, and static Fasthosts deployment."
date: 2026-08-14
lastmod: 2026-08-14
weight: 1
entryType: "project"
projectType: "Tool-assisted web project"
portfolio: true
featured: true
status: "Active"
stack: ["Python", "Jinja", "Markdown", "HTML", "CSS", "JavaScript"]
tags: ["web", "static-site", "accessibility", "automation"]
---

## Purpose

The site needed to work as both a professional portfolio and a personal corner of the web without exaggerating my experience. It also needed to remain easy to maintain on Windows and deploy as ordinary static files to Fasthosts.

## My contribution

- Defined the site goals, personal identity, authenticity rules and required professional story.
- Supplied and maintained the source content, hardware information and historical site direction.
- Preserved the static-site approach while consolidating the project onto the lightweight Python/Jinja build used by the current site.
- Directed the V6 rebuild, reviewed its output and retained a workflow I can continue learning with.
- Used Codex for implementation assistance, code review, testing and documentation.

## Design and implementation decisions

V6 keeps Markdown as the content format and uses the current lightweight Python/Jinja static generator. Professional navigation is explicit; personal material remains discoverable but cannot overwhelm the recruiter route. The interface uses a restrained systems-monitor visual language and restores both horizontal signal bars and vertical falling glyphs.

The production build contains only HTML, CSS, JavaScript, fonts, images and static search data. No server, database or tracking service is required.

## What I learned

The rebuild made content architecture as important as visual design. A project index can accidentally overstate work simply by treating planned exercises as finished projects, so V6 separates portfolio evidence from learning ideas at the data level.

## Current state

Active and maintainable. The helper scripts cover preview, new content, production builds and Fasthosts packaging.

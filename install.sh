#!/bin/bash
set -e

SKILL_SRC="$(cd "$(dirname "$0")/tsmc-resume-matcher" && pwd)"
SKILL_DST="$HOME/.claude/skills/tsmc-resume-matcher"

echo "Installing tsmc-resume-matcher skill..."
rm -rf "$SKILL_DST"
cp -r "$SKILL_SRC" "$SKILL_DST"

echo "Installed: $SKILL_DST"
echo "Files:"
find "$SKILL_DST" -type f | sed "s|$SKILL_DST/|  |"

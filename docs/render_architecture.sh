#!/bin/bash

# docs/render_architecture.sh
#
# Renders the Mermaid architecture diagram to SVG (light + dark variants).
#
# Prerequisites:
# - Node.js 18+ and npm (preferred)
# - OR Docker (fallback)
#
# Output:
#   docs/architecture-light.svg   (light theme)
#   docs/architecture-dark.svg    (dark theme)

set -e

echo "=========================================="
echo "Rendering Architecture Diagram"
echo "=========================================="

render_with_npx() {
  local theme="$1"
  local output="$2"
  npx -y @mermaid-js/mermaid-cli \
    -i docs/architecture.mmd \
    -o "$output" \
    --theme "$theme"
}

render_with_docker() {
  local theme="$1"
  local output="$2"
  docker run --rm \
    -u "$(id -u):$(id -g)" \
    -v "$PWD:/data" \
    minlag/mermaid-cli \
    -i /data/docs/architecture.mmd \
    -o "/data/$output" \
    --theme "$theme"
}

if command -v npx &>/dev/null; then
  echo "Found: npx (using npm/npx)"
  echo ""

  for pair in "default:docs/architecture-light.svg" "dark:docs/architecture-dark.svg"; do
    theme="${pair%%:*}"
    output="${pair##*:}"
    echo "+ npx mmdc --theme $theme -o $output"
    render_with_npx "$theme" "$output"
    echo "✓ $output"
  done

elif command -v docker &>/dev/null; then
  echo "Found: Docker (using containerized mermaid-cli)"
  echo ""

  for pair in "default:docs/architecture-light.svg" "dark:docs/architecture-dark.svg"; do
    theme="${pair%%:*}"
    output="${pair##*:}"
    echo "+ docker run ... --theme $theme -o $output"
    render_with_docker "$theme" "$output"
    echo "✓ $output"
  done

else
  echo ""
  echo "=========================================="
  echo "ERROR: Cannot render architecture diagram"
  echo "=========================================="
  echo ""
  echo "Neither Node.js (with npm) nor Docker is available."
  echo ""
  echo "To render the diagram, you need:"
  echo ""
  echo "Option 1: Install Node.js and npm"
  echo "  Visit: https://nodejs.org/"
  echo "  Verify: node --version && npm --version"
  echo ""
  echo "Option 2: Use Docker"
  echo "  Visit: https://docs.docker.com/get-docker/"
  echo "  Verify: docker --version"
  echo ""
  echo "Option 3: Provide pre-rendered images"
  echo "  Render docs/architecture.mmd manually"
  echo "  Save as: docs/architecture-light.svg and docs/architecture-dark.svg"
  echo ""
  exit 1
fi

echo ""
echo "=========================================="
echo "Render Complete"
echo "=========================================="
echo ""
for f in docs/architecture-light.svg docs/architecture-dark.svg; do
  if [[ -s "$f" ]]; then
    echo "  $f  ($(du -h "$f" | cut -f1))"
  else
    echo "  WARNING: $f was not created or is empty"
  fi
done
echo ""

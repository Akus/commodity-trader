#!/usr/bin/env bash
# Register this repo's Azure DevOps pipelines (CI + PR validation). Idempotent.
#
# Creates two pipeline definitions pointing at the YAML in this repo:
#   - commodity-trader-ci  -> azure-pipelines/ci.yml
#   - commodity-trader-pr  -> azure-pipelines/pr-validation.yml
#
# Does NOT recreate shared bits (variable group `commodity-cicd`, the ARM
# service connection, the commodity-dev/preprod/prod Environments) — those are
# shared with the infra repo and assumed to exist. See the trailing notes for
# the few UI-only steps.
#
# Prereqs:
#   - az CLI logged in (az login), or AZURE_DEVOPS_EXT_PAT exported.
#   - A GitHub service connection already created in the ADO project.
#
# Usage:
#   export AZURE_DEVOPS_EXT_PAT=<pat>
#   ./azure-pipelines/setup-ado.sh \
#     --org https://dev.azure.com/myorg --project commodity \
#     --github-service-connection "Akus-GitHub"
set -euo pipefail

ORG="" PROJECT="" GH_SC="" REPO="Akus/commodity-trader" BRANCH="main"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --org) ORG="$2"; shift 2;;
    --project) PROJECT="$2"; shift 2;;
    --github-service-connection) GH_SC="$2"; shift 2;;
    --repository) REPO="$2"; shift 2;;
    --branch) BRANCH="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done
: "${ORG:?--org required}"; : "${PROJECT:?--project required}"; : "${GH_SC:?--github-service-connection required}"

create_pipeline() {
  local name="$1" yaml="$2" scid="$3"
  local existing
  existing="$(az pipelines show --name "$name" --org "$ORG" --project "$PROJECT" --query id -o tsv 2>/dev/null || true)"
  if [[ -n "$existing" ]]; then
    echo "= pipeline '$name' already exists (id $existing) - skipping"; return
  fi
  echo "+ creating pipeline '$name' -> $yaml"
  az pipelines create \
    --name "$name" \
    --org "$ORG" --project "$PROJECT" \
    --repository "$REPO" --repository-type github --branch "$BRANCH" \
    --yaml-path "$yaml" \
    --service-connection "$scid" \
    --skip-first-run true >/dev/null
}

# 1. Ensure the azure-devops CLI extension is present.
if ! az extension show --name azure-devops -o tsv >/dev/null 2>&1; then
  echo "+ installing azure-devops extension"
  az extension add --name azure-devops --only-show-errors
fi

# 2. Defaults for this session.
az devops configure --defaults organization="$ORG" project="$PROJECT" >/dev/null

# 3. Resolve the GitHub service connection name -> id.
SC_ID="$(az devops service-endpoint list --org "$ORG" --project "$PROJECT" \
  --query "[?name=='$GH_SC'].id | [0]" -o tsv)"
if [[ -z "$SC_ID" ]]; then
  echo "GitHub service connection '$GH_SC' not found in $ORG/$PROJECT. Create it first (Project Settings -> Service connections -> GitHub)." >&2
  exit 1
fi
echo "= using GitHub service connection '$GH_SC' (id $SC_ID)"

# 4. Create the two pipelines.
create_pipeline "commodity-trader-ci" "azure-pipelines/ci.yml"            "$SC_ID"
create_pipeline "commodity-trader-pr" "azure-pipelines/pr-validation.yml" "$SC_ID"

cat <<'NOTE'

Done. Still manual in the ADO UI:
  1. Add 'commodity-trader-pr' as a branch policy / build validation on main.
  2. Add Approval checks on the commodity-preprod and commodity-prod Environments.
  3. Confirm the 'commodity-cicd' variable group (azureServiceConnection + FLUX_PAT)
     and the commodity-dev/preprod/prod Environments exist (shared with the infra repo).
NOTE

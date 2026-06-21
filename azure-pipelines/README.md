# Azure DevOps pipelines

| File | Purpose | Trigger |
|------|---------|---------|
| `pr-validation.yml` | ruff + pytest | PRs to `main` |
| `ci.yml` | build image, promote dev → preprod → prod via GitOps | push to `main` (app code) |
| `templates/promote-stage.yml` | reusable per-env image-tag bump | included by `ci.yml` |

> Terraform `fmt/validate` lives in the **AKS** (infra) repo's own
> `pr-validation.yml`, not here.

## Flow

```
Build (podman build/push to ACR, tag = Build.BuildId)
  └─> DeployDev   (auto)        bump overlays/dev      newTag
        └─> Preprod (approval)  bump overlays/preprod  newTag
              └─> Prod (approval) bump overlays/prod   newTag
```

Flux (in the cluster) sees each commit and rolls the deployment. The **same
immutable tag** built once is promoted across envs — no rebuilds.
**Rollback = revert the promotion commit** in the Flux repo.

## One-time setup in Azure DevOps

1. **Service connection** — an Azure Resource Manager connection scoped to the
   subscription / `rg-commodity-shared`. Put its name in the variable group as
   `azureServiceConnection`. It needs `AcrPush` on `akoscommodityacr`.

2. **Variable group** `commodity-cicd` (Pipelines → Library):
   - `azureServiceConnection` — name of the service connection above.
   - `FLUX_PAT` — **secret**. GitHub PAT with `repo` scope on
     `Akus/flux-simple-kubernetes-cluster` (used to push tag-bump commits).

3. **Environments** (Pipelines → Environments) — create:
   - `commodity-dev` — no checks (auto-deploy).
   - `commodity-preprod` — add an **Approval** check.
   - `commodity-prod` — add an **Approval** check.

4. **Create both pipelines** pointing at `azure-pipelines/pr-validation.yml`
   and `azure-pipelines/ci.yml`. Add `pr-validation` as a **branch policy /
   build validation** on `main`.

   Step 4 is scripted — run `setup-ado.ps1` (Windows) or `setup-ado.sh` once
   instead of clicking through the UI:

   ```powershell
   $env:AZURE_DEVOPS_EXT_PAT = "<ado-pat>"
   ./azure-pipelines/setup-ado.ps1 `
     -OrgUrl https://dev.azure.com/<org> -Project <project> `
     -GitHubServiceConnection "<github-service-connection-name>"
   ```

   It's idempotent (skips pipelines that already exist) and creates only the two
   pipeline definitions. The branch policy, Environment approvals, and the shared
   variable group / service connection / Environments stay manual — the script
   prints exactly what's left.

## Notes

- Hosted `ubuntu-latest` agents have `podman` available; `az acr login
  --expose-token` provides a short-lived token so no admin creds are stored.
- The image is tagged with `Build.BuildId` (immutable) plus `latest`.
- The variable group `commodity-cicd` and the service connection are **shared**
  with the infra repo's pipelines — no need to recreate them.

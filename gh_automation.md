```powershell
gh pr create --base webgl-dev --fill
gh pr merge --auto --merge
#gh run watch --exit-status

$runId = (gh run list --branch webgl-dev -L 1 --json databaseId | ConvertFrom-Json)[0].databaseId
gh run watch $runId --exit-status

```
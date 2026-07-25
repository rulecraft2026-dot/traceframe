$ErrorActionPreference = "Stop"
$ApiUrl = if ($env:API_URL) { $env:API_URL } else { "http://localhost:8000" }

Write-Host "1. Checking TraceFrame..."
Invoke-RestMethod "$ApiUrl/health"
Write-Host "2. Generating a provenance-tracked image..."
$created = Invoke-RestMethod -Method Post -Uri "$ApiUrl/api/generations" -ContentType "application/json" -Body (@{
  prompt = "A refillable trail bottle on warm stone at sunrise, editorial product photography"
} | ConvertTo-Json)
$created
Write-Host "3. Replaying $($created.id)..."
Invoke-RestMethod -Method Post -Uri "$ApiUrl/api/generations/$($created.id)/replay" -ContentType "application/json" -Body "{}"
Write-Host "4. Provenance history..."
Invoke-RestMethod "$ApiUrl/api/generations"

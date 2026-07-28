param(
  [ValidateSet("All", "Minimum", "Stable", "Coverage", "Ruff", "Hassfest", "Metadata", "CheckConfig", "Package", "Secrets")]
  [string]$Target = "All"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$componentRoot = Join-Path $repositoryRoot "custom_components\domee"
$configRoot = Join-Path $PSScriptRoot "config"
$minimumImage = "ghcr.io/home-assistant/home-assistant:2024.3.3"
$stableImage = "ghcr.io/home-assistant/home-assistant:stable"
$ruffImage = "ghcr.io/astral-sh/ruff:0.12.9-alpine"

function Invoke-Checked {
  param([scriptblock]$Command)
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "Validation command failed with exit code $LASTEXITCODE"
  }
}

function Invoke-Pytest([string]$Image) {
  Invoke-Checked {
    docker run --rm `
      --volume "${repositoryRoot}:/workspace:ro" `
      --workdir /workspace `
      --env PYTHONPATH=/workspace `
      $Image `
      python -m pytest -q -p no:cacheprovider tests
  }
}

$targets = if ($Target -eq "All") {
  @("Metadata", "Secrets", "Ruff", "Hassfest", "Minimum", "Stable", "Coverage", "CheckConfig", "Package")
} else {
  @($Target)
}

foreach ($item in $targets) {
  switch ($item) {
    "Minimum" { Invoke-Pytest $minimumImage }
    "Stable" {
      Invoke-Pytest $stableImage
      Invoke-Checked {
        docker run --rm `
          --volume "${componentRoot}:/component:ro" `
          --env PYTHONPYCACHEPREFIX=/tmp/pycache `
          $stableImage `
          python -m compileall -q /component
      }
    }
    "Coverage" {
      Invoke-Checked {
        docker run --rm `
          --volume "${repositoryRoot}:/workspace:ro" `
          --workdir /workspace `
          --env PYTHONPATH=/workspace `
          --env COVERAGE_FILE=/tmp/.coverage `
          $stableImage `
          sh -c "python -m coverage run --branch --source=custom_components/domee -m pytest -q -p no:cacheprovider tests && python -m coverage report --fail-under=85"
      }
    }
    "Ruff" {
      Invoke-Checked {
        docker run --rm `
          --volume "${repositoryRoot}:/workspace:ro" `
          --workdir /workspace `
          $ruffImage `
          ruff check --no-cache custom_components/domee tests validation scripts
      }
    }
    "Hassfest" {
      Invoke-Checked {
        docker run --rm `
          --volume "${repositoryRoot}:/github/workspace:ro" `
          ghcr.io/home-assistant/hassfest:latest
      }
    }
    "Metadata" {
      Invoke-Checked {
        docker run --rm `
          --volume "${repositoryRoot}:/workspace:ro" `
          --workdir /workspace `
          $stableImage `
          python validation/metadata_guard.py
      }
    }
    "Secrets" {
      Invoke-Checked {
        docker run --rm `
          --volume "${repositoryRoot}:/workspace:ro" `
          --workdir /workspace `
          $stableImage `
          python validation/secret_scan.py
      }
    }
    "CheckConfig" {
      Invoke-Checked {
        docker run --rm `
          --volume "${configRoot}:/source-config:ro" `
          --volume "${componentRoot}:/source-component:ro" `
          $stableImage `
          sh -c "mkdir -p /tmp/config/custom_components && cp -R /source-config/. /tmp/config/ && cp -R /source-component /tmp/config/custom_components/domee && python -m homeassistant --script check_config --config /tmp/config"
      }
    }
    "Package" {
      Invoke-Checked {
        docker run --rm `
          --volume "${repositoryRoot}:/workspace" `
          --workdir /workspace `
          $stableImage `
          sh -c "python scripts/build_release.py && python validation/validate_package.py && python validation/inspect_release_artifact.py"
      }
    }
  }
}

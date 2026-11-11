$ErrorActionPreference = 'Stop'

$context = kubectl config current-context
if ($LASTEXITCODE -ne 0) {
    throw 'Unable to read the current Kubernetes context.'
}
if ($context.Trim() -ne 'docker-desktop') {
    throw "Expected Kubernetes context 'docker-desktop'; found '$($context.Trim())'."
}

$nodeOutput = kubectl get nodes -o name
if ($LASTEXITCODE -ne 0) {
    throw 'Unable to list Kubernetes nodes.'
}
$nodes = @($nodeOutput | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($nodes.Count -ne 1) {
    throw "Expected one Docker Desktop Kubernetes node; found $($nodes.Count)."
}
$node = ($nodes[0] -split '/', 2)[1]

$images = @('ripple-effect-api:local', 'ripple-effect-web:local')
foreach ($image in $images) {
    $null = docker image inspect $image
    if ($LASTEXITCODE -ne 0) {
        throw "Local image '$image' is missing. Build it with the project Compose workflow first."
    }
}

$tempDirectory = Join-Path $PSScriptRoot '.local'
New-Item -ItemType Directory -Force -Path $tempDirectory | Out-Null
$archiveName = "ripple-effect-images-$([guid]::NewGuid().ToString('N')).tar"
$archivePath = Join-Path $tempDirectory $archiveName
$nodeArchivePath = "/tmp/$archiveName"

try {
    docker save --output $archivePath @images
    if ($LASTEXITCODE -ne 0) {
        throw 'Docker could not create the local image archive.'
    }

    $transferCommand = 'docker exec -i {0} sh -c "cat > {1}" < "{2}"' -f $node, $nodeArchivePath, $archivePath
    & $env:ComSpec /c $transferCommand
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not transfer the image archive to the Kubernetes node.'
    }

    docker exec $node ctr -n k8s.io images import $nodeArchivePath
    if ($LASTEXITCODE -ne 0) {
        throw 'Containerd could not import the local images.'
    }

    $importedImages = docker exec $node ctr -n k8s.io images ls
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not verify the imported containerd images.'
    }
    foreach ($image in $images) {
        $reference = "docker.io/library/$image"
        if (($importedImages -join "`n") -notmatch [regex]::Escape($reference)) {
            throw "Imported image '$reference' was not found in containerd."
        }
    }

    Write-Output "Imported both local application images into node '$node'."
}
finally {
    if ($node) {
        $null = docker exec $node rm -f $nodeArchivePath
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Unable to remove the temporary archive from node '$node'."
        }
    }
    if (Test-Path -LiteralPath $archivePath) {
        Remove-Item -LiteralPath $archivePath -Force
    }
    if (Test-Path -LiteralPath $tempDirectory) {
        $remainingFiles = Get-ChildItem -LiteralPath $tempDirectory -Force
        if ($remainingFiles.Count -eq 0) {
            Remove-Item -LiteralPath $tempDirectory
        }
    }
}

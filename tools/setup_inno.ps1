$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$toolsDir = Join-Path $root 'build\tools'
New-Item -ItemType Directory -Force $toolsDir | Out-Null
$download = Join-Path $toolsDir 'innosetup-6.7.3.exe'
Invoke-WebRequest 'https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe' -OutFile $download
if ((Get-FileHash $download -Algorithm SHA256).Hash -ne '9C73C3BAE7ED48D44112A0F48E66742C00090BDB5BEF71D9D3C056C66E97B732') { throw 'Compiler checksum mismatch' }
$sig = Get-AuthenticodeSignature $download
if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notlike '*Pyrsys B.V.*') { throw 'Compiler signature mismatch' }
$destination = Join-Path $toolsDir 'InnoSetup'
$argsText = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CURRENTUSER /NOICONS /DIR="' + $destination + '"'
$process = Start-Process -FilePath $download -ArgumentList $argsText -WindowStyle Hidden -Wait -PassThru
if ($process.ExitCode -ne 0) { throw "Compiler installation failed: $($process.ExitCode)" }

# Contributing

Discuss substantial changes in a GitHub issue first. Keep UI, input, rendering,
lifecycle and file export separate. Do not add telemetry or screen uploads.
Use the pinned environment in docs/INSTALLATION.md, run the unittest suite and
source smoke test, then include your Windows version, scaling and test results
in the PR. Use synthetic test images; never commit private captures or settings.
Changes must preserve pointer recovery, Escape and tray Exit. Tests that register
real global shortcuts must unregister them in cleanup. Do not commit build outputs.
Contributions are under the project's MIT license. Public releases require owner
approval and the release checklist, including licensing and clean-machine checks.

---
name: Single response clarification smoke (15051 only)
on:
  workflow_dispatch:
    inputs:
      case_id:
        description: Only pytest-15051 is permitted
        default: pytest-15051
        required: true
        type: string
permissions:
  contents: read
  actions: read
timeout-minutes: 10
concurrency:
  group: clarification-single-response
  cancel-in-progress: false
  job-discriminator: ${{ github.run_id }}
engine:
  # Generated CLI tool flags are unused argv: this harness never launches the CLI.
  id: copilot
  model: auto
  harness:
    use: single_response_harness.cjs
max-ai-credits: 5
max-daily-ai-credits: 15
network:
  allowed: []
tools:
  github: false
checkout: false
safe-outputs:
  staged: true
  threat-detection: false
  report-failure-as-issue: false
  report-failed-jobs: false
  report-incomplete:
    create-issue: false
  report-missing-tool: false
  report-missing-data: false
  noop:
    report-as-issue: false
pre-agent-steps:
  - name: Checkout trusted configuration separately
    uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
    with:
      path: .trusted
      persist-credentials: false
  - name: Prepare bounded packet and install trusted harness
    env:
      PYTHONPATH: .trusted
      TRUSTED_ROOT: .trusted
      CASE_ID: ${{ inputs.case_id }}
      GH_TOKEN: ${{ github.token }}
      SINGLE_RESPONSE_ENABLED: ${{ vars.CLARIFICATION_SINGLE_RESPONSE_ENABLED }}
    run: python -m scripts.single_response prepare
  - name: Remove non-input checkout before assessment
    run: python -c "import shutil; shutil.rmtree('.trusted')"
  - name: Preserve trusted packet manifest
    uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
    with:
      name: single-response-input
      path: input/manifest.json
      retention-days: 30
post-steps:
  - name: Preserve exact response and request evidence
    if: always()
    uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
    with:
      name: single-response-raw
      path: output/
      if-no-files-found: warn
      retention-days: 30
jobs:
  validate_recommendation:
    needs: [agent]
    runs-on: ubuntu-latest
    permissions:
      contents: read
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
        with:
          persist-credentials: false
      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333
        with:
          name: single-response-raw
          path: staged
      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333
        with:
          name: single-response-input
          path: trusted-input
      - name: Validate output and skill/request evidence in trusted checkout
        run: python -m scripts.single_response validate
      - uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        with:
          name: single-response-validated
          path: staged/recommendation.json
          if-no-files-found: error
          retention-days: 30
---

The trusted single_response_harness.cjs supplies the canonical skill and bounded
input packet directly in one Copilot gateway request. The model has no tools.
Return one JSON recommendation; trusted Python validates it. No publication.

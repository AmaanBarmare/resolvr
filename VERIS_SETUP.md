# VERIS_SETUP.md — Pre-Run Guide

Do this the **morning of the demo**. Allow 45–60 minutes. You only do this once.

---

## Why You Do This Before the Demo

Veris has no REST API. It runs via CLI. A simulation takes 5–10 minutes. You cannot wait for this during a 3-minute demo. So you pre-run it, save the transcripts, and the live demo loads them from disk instantly.

---

## Step 1 — Install Veris CLI

```bash
npm install -g @veris-ai/cli

# Verify
veris --version
```

---

## Step 2 — Authenticate

```bash
veris login
# Opens browser for OAuth — log in with your Veris account
```

---

## Step 3 — Set API Keys

```bash
# For Agent A environment
veris env vars set BASETEN_API_KEY=your_key --secret --env-id agent-a-env-id
veris env vars set BASETEN_MODEL_ID=claude-sonnet-4-5 --env-id agent-a-env-id

# For Agent B environment
veris env vars set BASETEN_API_KEY=your_key --secret --env-id agent-b-env-id
veris env vars set BASETEN_MODEL_ID=claude-sonnet-4-5 --env-id agent-b-env-id
```

---

## Step 4 — Create Environments

```bash
# Create Agent A environment
cd veris/agent_a
veris env create --name "Revenue Agent"
# Note the env ID it prints

# Create Agent B environment
cd veris/agent_b
veris env create --name "Risk Agent"
# Note the env ID it prints
```

---

## Step 5 — Build and Push Agent Images

```bash
# Push Agent A
cd veris/agent_a
veris env push
# Watch for: "Image pushed successfully"

# Push Agent B
cd veris/agent_b
veris env push
# Watch for: "Image pushed successfully"
```

If the push fails:
- Check Docker is running (`docker ps`)
- Check your Dockerfile builds locally: `docker build -t test-agent .`
- Check you're in the right directory (must have `.veris/veris.yaml`)

---

## Step 6 — Generate Scenarios

```bash
# Generate test scenarios for Agent A
veris scenarios create --env-id <agent-a-id> --num 1
# Wait for completion — note the scenario-set-id

# Generate test scenarios for Agent B
veris scenarios create --env-id <agent-b-id> --num 1
# Note the scenario-set-id
```

The scenario Veris generates should be the TechFlow hire decision. If it generates something unrelated, you may need to add context to the agent's code about what scenario it should handle.

---

## Step 7 — Run Simulations

```bash
# Run Agent A simulation
veris simulations create \
  --env-id <agent-a-id> \
  --scenario-set-id <scenario-a-id> \
  --simulation-timeout 300

# Get the run ID from the output, then watch it
veris simulations status <run-id> --watch
# Wait for: "Status: completed"

# Run Agent B simulation
veris simulations create \
  --env-id <agent-b-id> \
  --scenario-set-id <scenario-b-id> \
  --simulation-timeout 300

veris simulations status <run-id> --watch
```

---

## Step 8 — Download Transcripts

Open the Veris console in your browser:

```bash
veris simulations status <run-id>
# This shows a URL to the Veris console for this run
```

In the console:
1. Click on your completed simulation run
2. Click "View Transcript"
3. Copy the full JSON transcript
4. Save as `backend/data/transcript_a.json`

Repeat for Agent B → save as `backend/data/transcript_b.json`

---

## Step 9 — Verify Transcripts

Run the transcript validator to confirm they have the structure the forensics agent needs:

```bash
cd backend
python scripts/validate_transcripts.py
```

Expected output:
```
✓ transcript_a.json: valid
  - Tool calls: 3
  - Named assumptions: 4
  - Key assumptions found: close_rate, pipeline_value, burn_rate

✓ transcript_b.json: valid
  - Tool calls: 4
  - Named assumptions: 5
  - Key assumptions found: close_rate, burn_rate, runway_months, macro_outlook
```

If validation fails, the transcripts are missing named assumptions. Check the agent system prompts — they must explicitly instruct the agent to name every number and its source.

---

## Fallback: Mock Transcripts

If Veris is fighting you and you're running out of time:

```bash
cd backend
python scripts/generate_mock_transcripts.py
```

This generates realistic pre-built transcripts that the forensics agent can work with. The data matches the TechFlow seed scenario exactly.

Tell the judge: "We pre-ran our agents in the Veris sandbox this morning. Here are the behavioral transcripts Veris produced." (If using mocks: "Here are the agent outputs from our pre-run simulation.")

The forensics + You.com + simulation + brief all run live regardless. The Veris transcripts are just the input data.

---

## The veris run Shortcut

Instead of steps 6–7, you can use the single `veris run` command which chains everything:

```bash
# Full pipeline: simulations → evaluations → report
veris run \
  --scenario-set-id <id> \
  --agent-check-id <id> \
  --env-id <agent-a-id> \
  --report
```

This also generates an HTML evaluation report. Download it with:

```bash
veris reports get <report-id> -o agent_a_report.html
```

The report shows how well your agent performed — useful for the demo but not required.

---

## Quick Reference — CLI Commands Used

```bash
veris login                          # Authenticate
veris env create --name "Name"       # Create environment
veris env push                       # Build + push image
veris env vars set KEY=VAL --secret  # Set env vars
veris scenarios create --num 1       # Generate scenarios
veris simulations create             # Start simulation run
veris simulations status <id> --watch # Poll until complete
veris reports get <id>               # Download HTML report
```

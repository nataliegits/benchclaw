# BenchClaw 🦞🔬

**AI-powered protocol auditor for life science labs.**

Built in 6 hours as part of the Worldwide Fellows: AI for Science fellowship challenge.

## The Problem

Scientists still document protocols in Word docs, handwritten notebooks, and personal Excel files. There's no error-checking, no QC validation, no institutional memory. Every lab reinvents the wheel — at enormous cost to reproducibility and speed.

## What BenchClaw Does

BenchClaw takes any lab protocol as input and uses Claude to generate a structured audit report flagging:

- 🔴 Missing critical steps
- ⚠️ Safety concerns
- 🟡 Missing QC checkpoints  
- 🔴 Parameter issues (temperatures, times, concentrations)
- 💡 Suggested improvements

## Quick Start
```bash
git clone https://github.com/nataliegits/benchclaw.git
cd benchclaw
pip install anthropic
export ANTHROPIC_API_KEY="your-key-here"

# Run with default MeDIP demo protocol
python3 benchclaw.py

# Run with your own protocol
python3 benchclaw.py --protocol my_protocol.txt

# Save audit report
python3 benchclaw.py --output audit_report.md
```

## Example Output

See [audit_report.md](audit_report.md) for a full example audit of a MeDIP protocol.

## Built With

- [Claude API](https://anthropic.com) — scientific domain reasoning
- [LabClaw](https://github.com/labclaw/labclaw) — open-source AI infrastructure for scientific labs

## About

Built by [Natalie Chen](https://linkedin.com/in/nychen14), Ph.D., Head of Lab Science at Generation Lab and founder of [Experimentally.AI](https://experimentally.ai).

This is the software core of a larger vision: **BenchClaw** — a wearable lab capture system that passively records what scientists do at the bench and generates structured protocol documentation in real time. No more stopping to document. The hardware layer comes next.

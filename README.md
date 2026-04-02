# BenchClaw 🦞🔬

**AI-powered protocol tools for life science labs.**

Built during the Worldwide Fellows: AI for Science fellowship. The longer vision is a wearable lab capture system that passively records what scientists do at the bench and generates structured protocol documentation in real time — no stopping to document. This repo is the software intelligence layer.

## The Problem

Scientists still document protocols in Word docs, handwritten notebooks, and shared drives. There's no error-checking, no QC validation, no institutional memory. Every lab reinvents the wheel — at enormous cost to reproducibility and speed.

## What BenchClaw Does

A Streamlit web app with seven tools:

| Tool | Description |
|---|---|
| **Protocol Auditor** | Paste any lab protocol, get an AI audit flagging missing steps, safety issues, QC gaps, and parameter problems |
| **Literature Cross-Reference** | Auto-extracts search terms from your protocol and pulls relevant PubMed papers |
| **Protocol Generator** | Describe an experiment in plain English, get a complete structured protocol |
| **Protocol Diff & Audit** | Paste two versions of a protocol, see a highlighted diff, get an AI audit of what changed |
| **Database Search** | Search UniProt, ChEMBL, and PubChem directly from the app |
| **Reagent Cost Estimator** | Extracts reagents from a protocol and returns price ranges and vendor suggestions |
| **OpenTrons Export** | Converts any protocol to a valid OT-2 Python script, ready to run on the robot or simulator |
| **Bench Vision** | Upload a photo from the bench — Claude identifies the technique, reads labels, and flags issues |
| **My Protocols** | Save, share via link, and manage your protocols across sessions |

## Quick Start

```bash
git clone https://github.com/nataliegits/benchclaw.git
cd benchclaw

pip install anthropic streamlit requests python-docx fpdf2
export ANTHROPIC_API_KEY="your-key-here"
streamlit run benchclaw_app.py
```

Opens at `http://localhost:8501`. Register an account to save and share protocols.

## Original CLI (v1)

The original single-file protocol auditor still works:

```bash
pip install anthropic
export ANTHROPIC_API_KEY="your-key-here"

python3 benchclaw.py                              # demo MeDIP protocol
python3 benchclaw.py --protocol my_protocol.txt  # your own protocol
python3 benchclaw.py --output report.md           # save the report
```

See [audit_report.md](audit_report.md) for an example output.

## Built With

- [Claude API](https://anthropic.com) (Anthropic) — scientific reasoning, protocol generation, vision, and OT-2 code generation
- [Streamlit](https://streamlit.io) — web app framework
- [LabClaw](https://github.com/labclaw/labclaw) — open-source AI infrastructure for scientific labs (submodule)
- [Opentrons Python API](https://docs.opentrons.com/v2/) — OT-2 robot protocol scripting
- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/home/develop/api/) — PubMed search
- [UniProt REST API](https://www.uniprot.org/help/api) — protein database
- [ChEMBL API](https://www.ebi.ac.uk/chembl/) — bioactive molecule database
- [PubChem API](https://pubchem.ncbi.nlm.nih.gov/) — chemical compound database

## About

Built by [Natalie Chen](https://linkedin.com/in/nychen14), Ph.D. — Head of Lab Science at Generation Lab and founder of [Experimentally.AI](https://experimentally.ai).

The software intelligence layer is the foundation. The next phase: image input — feed photos or video from the bench and have BenchClaw interpret what's happening in the context of a known protocol.

For the full build story, see [DEVLOG.md](DEVLOG.md).

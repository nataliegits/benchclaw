import sys
import os
import argparse
sys.path.insert(0, 'labclaw/src')
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

DEFAULT_PROTOCOL = """
MeDIP Protocol:
1. Extract genomic DNA from blood samples
2. Fragment DNA by sonication to 200-600bp
3. Denature DNA at 95C for 10 minutes
4. Incubate with anti-5mC antibody overnight at 4C
5. Add protein A/G beads and incubate 2 hours
6. Wash beads 3x with IP buffer
7. Elute DNA and purify
8. Proceed to qPCR or sequencing
"""

def audit_protocol(protocol_text):
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"""You are a senior molecular biology scientist specializing in epigenetics and DNA methylation.

Audit the following lab protocol and identify:
1. MISSING STEPS that are critical but absent
2. SAFETY CONCERNS
3. QUALITY CONTROL checkpoints that should be added
4. PARAMETER ISSUES (temperatures, times, concentrations that seem off)
5. SUGGESTED IMPROVEMENTS

Be specific and actionable. Format as a clear audit report.

PROTOCOL TO AUDIT:
{protocol_text}"""
        }]
    )
    return message.content[0].text

def main():
    parser = argparse.ArgumentParser(description='BenchClaw — AI Protocol Auditor for Life Science Labs')
    parser.add_argument('--protocol', type=str, help='Path to protocol text file', default=None)
    parser.add_argument('--output', type=str, help='Save audit report to file', default=None)
    args = parser.parse_args()

    if args.protocol:
        with open(args.protocol, 'r') as f:
            protocol_text = f.read()
    else:
        print("No protocol file provided — using default MeDIP protocol demo.\n")
        protocol_text = DEFAULT_PROTOCOL

    print("BenchClaw Protocol Auditor")
    print("=" * 50)
    print("Auditing protocol...\n")
    
    result = audit_protocol(protocol_text)
    print(result)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(f"# BenchClaw Audit Report\n\n")
            f.write(f"## Protocol Input\n\n```\n{protocol_text}\n```\n\n")
            f.write(f"## Audit Results\n\n{result}")
        print(f"\n✅ Audit report saved to {args.output}")

if __name__ == "__main__":
    main()

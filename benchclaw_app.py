"""BenchClaw v2 — Streamlit web app for AI-powered lab protocol tools."""

import os
import sys
import json
import requests
import xml.etree.ElementTree as ET

import streamlit as st
import anthropic

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "labclaw", "src"))

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="BenchClaw v2",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Shared client
# ---------------------------------------------------------------------------
@st.cache_resource
def get_client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------
AUDIT_SYSTEM = (
    "You are a senior molecular biology scientist with 20+ years of experience "
    "across genomics, epigenetics, cell biology, and biochemistry. "
    "You audit lab protocols with the precision of a peer reviewer. "
    "Be specific, cite exact steps by number, and flag anything that could "
    "compromise reproducibility, safety, or data quality."
)

GENERATOR_SYSTEM = (
    "You are an expert protocol writer for life science research. "
    "You write clear, numbered, highly detailed lab protocols following "
    "community standards (e.g. Nature Protocols style). "
    "Include reagents, equipment, volumes, temperatures, timings, "
    "controls, troubleshooting tips, and safety notes."
)

KEYWORD_SYSTEM = (
    "You are a scientific literature search specialist. "
    "Extract the most relevant PubMed search terms from lab protocol or "
    "experiment descriptions. Return ONLY a JSON array of 3-6 search term "
    "strings, no explanation. Example: [\"MeDIP-seq\", \"DNA methylation immunoprecipitation\", \"5-methylcytosine antibody\"]"
)

DEFAULT_PROTOCOL = """\
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

DEFAULT_DESCRIPTION = (
    "I want to study the effect of CRISPR-Cas9 knockout of DNMT3A on global "
    "DNA methylation patterns in human HEK293 cells, comparing edited vs "
    "wild-type cells using whole-genome bisulfite sequencing."
)


# ---------------------------------------------------------------------------
# Feature 1 — Protocol Auditor
# ---------------------------------------------------------------------------
def render_auditor():
    st.header("Protocol Auditor")
    st.caption("Paste a lab protocol and get an expert AI audit.")

    protocol = st.text_area(
        "Protocol text",
        value=DEFAULT_PROTOCOL,
        height=250,
        placeholder="Paste your protocol here…",
    )

    if st.button("Audit Protocol", type="primary", key="audit_btn"):
        if not protocol.strip():
            st.warning("Please enter a protocol.")
            return

        st.divider()
        st.subheader("Audit Report")

        def _stream():
            client = get_client()
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=4096,
                system=AUDIT_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": (
                        "Audit the following lab protocol. Identify:\n"
                        "1. MISSING STEPS (critical but absent)\n"
                        "2. SAFETY CONCERNS\n"
                        "3. QUALITY CONTROL checkpoints to add\n"
                        "4. PARAMETER ISSUES (temperatures, times, concentrations)\n"
                        "5. SUGGESTED IMPROVEMENTS\n\n"
                        "Be specific, reference step numbers, and format as a clear report.\n\n"
                        f"PROTOCOL:\n{protocol}"
                    ),
                }],
            ) as stream:
                for text in stream.text_stream:
                    yield text

        st.write_stream(_stream())


# ---------------------------------------------------------------------------
# PubMed helpers
# ---------------------------------------------------------------------------
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _pubmed_search(query: str, max_results: int = 8) -> list[str]:
    """Return a list of PMIDs for the query."""
    resp = requests.get(
        f"{EUTILS_BASE}/esearch.fcgi",
        params={
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("esearchresult", {}).get("idlist", [])


def _pubmed_fetch(pmids: list[str]) -> list[dict]:
    """Fetch paper summaries for a list of PMIDs."""
    if not pmids:
        return []
    resp = requests.get(
        f"{EUTILS_BASE}/efetch.fcgi",
        params={
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        },
        timeout=20,
    )
    resp.raise_for_status()

    papers = []
    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError:
        return []

    for article in root.findall(".//PubmedArticle"):
        pmid_el = article.find(".//PMID")
        title_el = article.find(".//ArticleTitle")
        abstract_el = article.find(".//AbstractText")
        year_el = article.find(".//PubDate/Year")

        authors = []
        for author in article.findall(".//AuthorList/Author")[:3]:
            last = author.findtext("LastName", "")
            initials = author.findtext("Initials", "")
            if last:
                authors.append(f"{last} {initials}".strip())
        if len(article.findall(".//AuthorList/Author")) > 3:
            authors.append("et al.")

        journal_el = article.find(".//Journal/Title")

        papers.append({
            "pmid": pmid_el.text if pmid_el is not None else "N/A",
            "title": title_el.text if title_el is not None else "No title",
            "abstract": abstract_el.text if abstract_el is not None else "No abstract available.",
            "authors": ", ".join(authors) if authors else "Unknown",
            "year": year_el.text if year_el is not None else "N/A",
            "journal": journal_el.text if journal_el is not None else "N/A",
        })

    return papers


def _extract_keywords(text: str) -> list[str]:
    """Use Claude to extract PubMed search terms from protocol/description text."""
    client = get_client()
    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=256,
        system=KEYWORD_SYSTEM,
        messages=[{"role": "user", "content": text[:3000]}],
    )
    raw = msg.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])
    try:
        keywords = json.loads(raw)
        if isinstance(keywords, list):
            return [str(k) for k in keywords[:6]]
    except (json.JSONDecodeError, ValueError):
        pass
    # Fallback: split on commas
    return [k.strip().strip('"') for k in raw.split(",") if k.strip()]


# ---------------------------------------------------------------------------
# Feature 2 — Literature Cross-Reference
# ---------------------------------------------------------------------------
def render_literature():
    st.header("Literature Cross-Reference")
    st.caption(
        "Paste a protocol or describe an experiment — BenchClaw extracts keywords "
        "and pulls relevant PubMed papers automatically."
    )

    text_input = st.text_area(
        "Protocol or experiment description",
        value=DEFAULT_PROTOCOL,
        height=200,
        placeholder="Paste your protocol or experiment description…",
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        max_results = st.number_input("Max papers", min_value=1, max_value=20, value=8)
    with col2:
        custom_query = st.text_input(
            "Override search query (optional)",
            placeholder="Leave blank to auto-extract keywords",
        )

    if st.button("Search PubMed", type="primary", key="lit_btn"):
        if not text_input.strip():
            st.warning("Please enter a protocol or description.")
            return

        with st.spinner("Extracting search keywords…"):
            if custom_query.strip():
                keywords = [custom_query.strip()]
                query_str = custom_query.strip()
            else:
                try:
                    keywords = _extract_keywords(text_input)
                    query_str = " OR ".join(f'"{k}"' for k in keywords)
                except Exception as e:
                    st.error(f"Keyword extraction failed: {e}")
                    return

        st.info(f"**Search terms:** {', '.join(keywords)}")

        with st.spinner("Searching PubMed…"):
            try:
                pmids = _pubmed_search(query_str, max_results=int(max_results))
            except Exception as e:
                st.error(f"PubMed search failed: {e}")
                return

        if not pmids:
            st.warning("No papers found. Try different keywords.")
            return

        with st.spinner(f"Fetching {len(pmids)} papers…"):
            try:
                papers = _pubmed_fetch(pmids)
            except Exception as e:
                st.error(f"Failed to fetch paper details: {e}")
                return

        st.divider()
        st.subheader(f"Found {len(papers)} paper(s)")

        for i, paper in enumerate(papers, 1):
            with st.expander(
                f"{i}. {paper['title'][:100]}{'…' if len(paper['title']) > 100 else ''}",
                expanded=(i == 1),
            ):
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.markdown(f"**Authors:** {paper['authors']}")
                    st.markdown(f"**Journal:** {paper['journal']} ({paper['year']})")
                with col_b:
                    pmid = paper["pmid"]
                    st.markdown(
                        f"**PMID:** [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)"
                    )

                st.markdown("**Abstract:**")
                st.write(paper["abstract"])


# ---------------------------------------------------------------------------
# Feature 3 — Protocol Generator
# ---------------------------------------------------------------------------
def render_generator():
    st.header("Protocol Generator")
    st.caption(
        "Describe your experiment in plain English and get a complete, "
        "structured lab protocol."
    )

    description = st.text_area(
        "Experiment description",
        value=DEFAULT_DESCRIPTION,
        height=180,
        placeholder="Describe what you want to do in plain English…",
    )

    col1, col2 = st.columns(2)
    with col1:
        detail_level = st.selectbox(
            "Detail level",
            ["Standard", "Highly detailed (Nature Protocols style)", "Quick overview"],
            index=0,
        )
    with col2:
        output_format = st.selectbox(
            "Output format",
            ["Step-by-step numbered list", "Markdown with sections", "Table of steps"],
            index=0,
        )

    if st.button("Generate Protocol", type="primary", key="gen_btn"):
        if not description.strip():
            st.warning("Please describe your experiment.")
            return

        detail_map = {
            "Standard": "Write a thorough, peer-reviewable protocol.",
            "Highly detailed (Nature Protocols style)": (
                "Write an extremely detailed protocol following Nature Protocols style: "
                "include all reagent preparations, exact volumes, equipment settings, "
                "expected outcomes, critical steps, troubleshooting table, and timing."
            ),
            "Quick overview": (
                "Write a concise overview protocol with the key steps only."
            ),
        }
        format_map = {
            "Step-by-step numbered list": "Use a numbered list for all steps.",
            "Markdown with sections": (
                "Use Markdown with sections: Overview, Materials, Reagents, "
                "Procedure, Controls, Expected Results, Troubleshooting."
            ),
            "Table of steps": (
                "Present the procedure as a Markdown table with columns: "
                "Step | Action | Duration | Notes."
            ),
        }

        detail_instruction = detail_map[detail_level]
        format_instruction = format_map[output_format]

        st.divider()
        st.subheader("Generated Protocol")

        def _stream():
            client = get_client()
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=8192,
                system=GENERATOR_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": (
                        f"{detail_instruction} {format_instruction}\n\n"
                        f"EXPERIMENT DESCRIPTION:\n{description}"
                    ),
                }],
            ) as stream:
                for text in stream.text_stream:
                    yield text

        st.write_stream(_stream())


# ---------------------------------------------------------------------------
# Sidebar + routing
# ---------------------------------------------------------------------------
def main():
    st.sidebar.image(
        "https://img.icons8.com/emoji/96/dna.png", width=64
    )
    st.sidebar.title("BenchClaw v2")
    st.sidebar.caption("AI-powered protocol tools for life science labs")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "Tools",
        [
            "Protocol Auditor",
            "Literature Cross-Reference",
            "Protocol Generator",
        ],
        label_visibility="collapsed",
    )

    st.sidebar.divider()
    st.sidebar.caption(
        "Powered by [Claude API](https://www.anthropic.com) + "
        "[PubMed E-utilities](https://www.ncbi.nlm.nih.gov/home/develop/api/)"
    )

    if page == "Protocol Auditor":
        render_auditor()
    elif page == "Literature Cross-Reference":
        render_literature()
    elif page == "Protocol Generator":
        render_generator()


if __name__ == "__main__":
    main()

"""BenchClaw v2 — Streamlit web app for AI-powered lab protocol tools."""

import json
import os
import sys

import requests
import streamlit as st
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "labclaw", "src"))

from benchclaw_db import db_create_user, db_load_by_token, db_verify_user
from benchclaw_features import (
    get_client,
    render_bench_vision,
    render_diff_auditor,
    render_labclaw,
    render_my_protocols,
    render_opentrons,
    render_reagent_cost,
    render_save_export,
)

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
# System prompts (existing features)
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
    'strings, no explanation. Example: ["MeDIP-seq", "DNA methylation immunoprecipitation", "5-methylcytosine antibody"]'
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

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


# ---------------------------------------------------------------------------
# Feature 6 — Auth gate
# ---------------------------------------------------------------------------

def render_auth_gate() -> bool:
    """Show login/register UI. Returns True if user is now logged in."""
    st.title("BenchClaw v2")
    st.caption("Log in to access all features, or register a new account.")

    tab_login, tab_register = st.tabs(["Log In", "Register"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log In", type="primary")
        if submitted:
            if not username or not password:
                st.error("Please enter username and password.")
            else:
                user_id, err = db_verify_user(username, password)
                if err:
                    st.error(err)
                else:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.session_state["username"] = username
                    st.rerun()

    with tab_register:
        with st.form("register_form"):
            new_username = st.text_input("Choose a username", key="reg_username")
            new_password = st.text_input("Choose a password", type="password", key="reg_password")
            confirm = st.text_input("Confirm password", type="password", key="reg_confirm")
            submitted_r = st.form_submit_button("Create Account", type="primary")
        if submitted_r:
            if not new_username or not new_password:
                st.error("Username and password required.")
            elif new_password != confirm:
                st.error("Passwords do not match.")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                ok, err = db_create_user(new_username, new_password)
                if err:
                    st.error(err)
                else:
                    st.success("Account created! You can now log in.")

    return False


# ---------------------------------------------------------------------------
# PubMed helpers (Feature: Literature Cross-Reference)
# ---------------------------------------------------------------------------

def _pubmed_search(query: str, max_results: int = 8) -> list:
    resp = requests.get(
        f"{EUTILS_BASE}/esearch.fcgi",
        params={"db": "pubmed", "term": query, "retmax": max_results,
                "retmode": "json", "sort": "relevance"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("esearchresult", {}).get("idlist", [])


def _pubmed_fetch(pmids: list) -> list:
    if not pmids:
        return []
    resp = requests.get(
        f"{EUTILS_BASE}/efetch.fcgi",
        params={"db": "pubmed", "id": ",".join(pmids),
                "retmode": "xml", "rettype": "abstract"},
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


def _extract_keywords(text: str) -> list:
    client = get_client()
    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=256,
        system=KEYWORD_SYSTEM,
        messages=[{"role": "user", "content": text[:3000]}],
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])
    try:
        kws = json.loads(raw)
        if isinstance(kws, list):
            return [str(k) for k in kws[:6]]
    except (json.JSONDecodeError, ValueError):
        pass
    return [k.strip().strip('"') for k in raw.split(",") if k.strip()]


# ---------------------------------------------------------------------------
# Feature 1 — Protocol Auditor (updated with export + share)
# ---------------------------------------------------------------------------

def render_auditor(preloaded_text: str = "") -> None:
    st.header("Protocol Auditor")
    st.caption("Paste a lab protocol and get an expert AI audit.")

    protocol = st.text_area(
        "Protocol text",
        value=preloaded_text or DEFAULT_PROTOCOL,
        height=250,
        placeholder="Paste your protocol here…",
        key="auditor_input",
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

        audit_text = st.write_stream(_stream())
        render_save_export(str(audit_text), ptype="audit", key_prefix="audit")


# ---------------------------------------------------------------------------
# Feature 2 — Literature Cross-Reference
# ---------------------------------------------------------------------------

def render_literature() -> None:
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
        key="lit_input",
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        max_results = st.number_input("Max papers", min_value=1, max_value=20, value=8)
    with col2:
        custom_query = st.text_input(
            "Override search query (optional)",
            placeholder="Leave blank to auto-extract keywords",
            key="lit_custom_query",
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
            title_preview = paper["title"][:100] + ("…" if len(paper["title"]) > 100 else "")
            with st.expander(f"{i}. {title_preview}", expanded=(i == 1)):
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.markdown(f"**Authors:** {paper['authors']}")
                    st.markdown(f"**Journal:** {paper['journal']} ({paper['year']})")
                with col_b:
                    pmid = paper["pmid"]
                    st.markdown(f"**PMID:** [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
                st.markdown("**Abstract:**")
                st.write(paper["abstract"])


# ---------------------------------------------------------------------------
# Feature 3 — Protocol Generator (updated with export + share)
# ---------------------------------------------------------------------------

def render_generator(preloaded_text: str = "") -> None:
    st.header("Protocol Generator")
    st.caption(
        "Describe your experiment in plain English and get a complete, "
        "structured lab protocol."
    )

    description = st.text_area(
        "Experiment description",
        value=preloaded_text or DEFAULT_DESCRIPTION,
        height=180,
        placeholder="Describe what you want to do in plain English…",
        key="gen_input",
    )

    col1, col2 = st.columns(2)
    with col1:
        detail_level = st.selectbox(
            "Detail level",
            ["Standard", "Highly detailed (Nature Protocols style)", "Quick overview"],
            key="gen_detail",
        )
    with col2:
        output_format = st.selectbox(
            "Output format",
            ["Step-by-step numbered list", "Markdown with sections", "Table of steps"],
            key="gen_format",
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
            "Quick overview": "Write a concise overview protocol with the key steps only.",
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
                        f"{detail_map[detail_level]} {format_map[output_format]}\n\n"
                        f"EXPERIMENT DESCRIPTION:\n{description}"
                    ),
                }],
            ) as stream:
                for text in stream.text_stream:
                    yield text

        protocol_text = st.write_stream(_stream())
        render_save_export(str(protocol_text), ptype="protocol", key_prefix="gen")


# ---------------------------------------------------------------------------
# Shared protocol viewer (token-based)
# ---------------------------------------------------------------------------

def render_shared_protocol(token: str) -> None:
    row = db_load_by_token(token)
    if not row:
        st.error("Protocol not found or link has expired.")
        return
    st.header(f"Shared Protocol: {row['title']}")
    st.caption(f"Type: {row['ptype'].replace('_', ' ').title()}  ·  Saved: {row['created'][:10]}")
    st.divider()
    st.markdown(row["body"])
    from benchclaw_features import render_save_export
    render_save_export(row["body"], ptype=row["ptype"], key_prefix="shared")


# ---------------------------------------------------------------------------
# Sidebar + routing
# ---------------------------------------------------------------------------

def main() -> None:
    # --- Feature 5: Check for shared protocol token in URL ---
    token = st.query_params.get("token")
    if token:
        render_shared_protocol(token)
        st.stop()

    # --- Feature 6: Auth gate ---
    if not st.session_state.get("logged_in"):
        render_auth_gate()
        st.stop()

    # --- Sidebar ---
    with st.sidebar:
        st.title("BenchClaw v2")
        st.caption(f"Logged in as **{st.session_state.get('username', '')}**")
        if st.button("Log out", key="logout_btn"):
            for key in ["logged_in", "user_id", "username"]:
                st.session_state.pop(key, None)
            st.rerun()

        st.divider()

        page = st.radio(
            "Tools",
            [
                "Protocol Auditor",
                "Literature Cross-Reference",
                "Protocol Generator",
                "Protocol Diff & Audit",
                "Database Search",
                "Reagent Cost Estimator",
                "OpenTrons Export",
                "Bench Vision",
                "My Protocols",
            ],
            label_visibility="collapsed",
        )

        st.divider()
        st.caption(
            "Powered by [Claude API](https://www.anthropic.com) · "
            "[PubMed](https://pubmed.ncbi.nlm.nih.gov) · "
            "[UniProt](https://www.uniprot.org) · "
            "[ChEMBL](https://www.ebi.ac.uk/chembl) · "
            "[PubChem](https://pubchem.ncbi.nlm.nih.gov)"
        )

    # --- Route ---
    if page == "Protocol Auditor":
        render_auditor()
    elif page == "Literature Cross-Reference":
        render_literature()
    elif page == "Protocol Generator":
        render_generator()
    elif page == "Protocol Diff & Audit":
        render_diff_auditor()
    elif page == "Database Search":
        render_labclaw()
    elif page == "Reagent Cost Estimator":
        render_reagent_cost()
    elif page == "OpenTrons Export":
        render_opentrons()
    elif page == "Bench Vision":
        render_bench_vision()
    elif page == "My Protocols":
        render_my_protocols()


if __name__ == "__main__":
    main()

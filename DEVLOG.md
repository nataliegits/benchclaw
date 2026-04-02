# BenchClaw Devlog

---

## 2026-04-02 - OpenTrons export and Bench Vision

### What I added

Two features that push the app closer to the actual bench.

**OpenTrons Export** converts any protocol into a valid Python script for the Opentrons OT-2 robot. You paste a protocol, pick your pipette and mount, and the app generates code you can download as a `.py` file and drag into the Opentrons App or simulator. It streams live so you watch the code being written. Each step in the generated script has a comment pointing back to the original protocol step number, and any steps that can't be automated get a `protocol.comment()` call explaining what the scientist needs to do manually.

The reason this matters: the gap between "written protocol" and "robot-executable instructions" is currently manual and slow. Bridging that in one click is directly useful, and it's a strong demo moment: plain English description becomes robot code in real time.

**Bench Vision** adds image upload to the app. You take a photo at the bench, upload it, and Claude describes what it sees: equipment, samples, labels, technique, anything visible. There's an optional protocol context field where you can paste the relevant protocol or say which step you're on, and Claude will tell you whether what it sees matches what should be there. There's also a free-text question field for things like "do these bands look right?" or "is this contaminated?"

This is the start of the visual intelligence layer. Right now it's interpreting single images. The longer-term version is continuous: a camera at the bench feeding frames into this analysis, checked against a known protocol in real time.

### How the image upload works

Streamlit has a built-in `st.file_uploader()` component that accepts image files and returns the raw bytes. To send an image to Claude, you base64-encode those bytes and pass them as a content block alongside the text prompt:

```python
import base64

image_bytes = uploaded_file.read()
b64 = base64.standard_b64encode(image_bytes).decode()

messages = [{
    "role": "user",
    "content": [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}
        },
        {
            "type": "text",
            "text": "What do you see in this lab image?"
        }
    ]
}]
```

Claude receives both the image and the text in the same message. The `media_type` field needs to match the actual file format (jpeg, png, gif, or webp). The model used is `claude-opus-4-6`, which supports vision natively.

### How the OpenTrons code generation works

The Opentrons OT-2 uses Python scripts to define protocols. The structure is always the same: a metadata dictionary, then a `run()` function that takes a `protocol_api.ProtocolContext` argument. Inside that function you load labware, load pipettes, and issue liquid handling commands.

Claude knows the OT-2 API well enough to generate valid scripts. The system prompt specifies the real labware names, real pipette names, and the correct API version (`2.16`). It also tells Claude to add comments mapping each generated step back to the original protocol step number, and to use `protocol.comment()` for anything that can't be automated.

The output is streamed live and then available as a `.py` download. The link to the Opentrons Protocol Designer simulator is included so you can test it immediately in the browser without needing the physical robot.

### What the protocol context field in Bench Vision is for

This is the core of the training layer. When you upload an image and also paste in a protocol, Claude can answer questions like: "I'm on step 4, does what I see match what I should see?" That comparison between expected and observed is what makes the visual layer useful rather than just descriptive.

Over time, if you run the same protocol repeatedly and upload images at each step, you're building a dataset of what each step looks like when it goes right and when it goes wrong. That's the foundation for training a model that doesn't need Claude's reasoning every time, just a fast classifier.

---

## 2026-04-01 - Building v1 and v2 in one session

### What I set out to do

I wanted to build a tool that could audit lab protocols using AI. The longer vision is BenchClaw as a wearable lab capture system that passively records what scientists do at the bench and writes structured protocol documentation in real time. Today was about building the software intelligence layer: take a protocol, understand it, critique it, generate new ones, find related literature. The hardware comes later. Eventually I want to feed it images, photos or video from the bench, and have it make sense of what's happening visually.

---

### What I actually built

**v1** was a ~70-line command-line script. You run it in a terminal, give it a protocol, it calls Claude, and prints an audit report. Simple.

**v2** is a full web app with seven tools:

| Tool | What it does |
|---|---|
| Protocol Auditor | Paste a protocol, get an expert AI critique |
| Literature Cross-Reference | Auto-search PubMed for papers relevant to your protocol |
| Protocol Generator | Describe an experiment in plain English, get a full protocol |
| Protocol Diff & Audit | Paste two versions of a protocol, see what changed, audit the delta |
| Database Search | Search UniProt (proteins), ChEMBL (molecules), PubChem (compounds) |
| Reagent Cost Estimator | Extract reagents from a protocol, get price ranges and vendors |
| My Protocols | Save, share, and manage protocols across sessions |

The whole thing runs locally. Auth, database, sharing, all local, no cloud service required.

---

### The thing that surprised me most

Everything was faster to build than expected. The concepts sound complicated (streaming AI responses, database search, user authentication) but the actual code for each was short. The Anthropic SDK does a lot of the heavy lifting. Streamlit does the same for the UI. Most of the work was figuring out what to build, not how.

The one rough patch was LabClaw. It took a while to get set up and even then I couldn't fully use it in the app (more on why below). That was frustrating because it should have been the easy part.

---

### Concepts I used, explained simply

I used a bunch of tools and concepts I hadn't worked with before. Here's what they actually are:

---

#### The Anthropic SDK

The Anthropic SDK is a Python library (`pip install anthropic`) that lets you send messages to Claude and get responses back. 

Think of it like a phone call to Claude. You write your message, you call a function, you get a response. Under the hood it's making HTTP requests to Anthropic's servers, but the SDK makes that invisible so you don't have to deal with it.

The simplest version looks like this:

```python
import anthropic

client = anthropic.Anthropic(api_key="your-key")

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Audit this protocol..."}]
)

print(response.content[0].text)
```

Three things to know:
- **`model`** - which version of Claude to use. I used `claude-opus-4-6`, the most capable one.
- **`max_tokens`** - how long the response is allowed to be. A token is roughly one word.
- **`messages`** - the conversation history. The API is stateless, meaning it doesn't remember previous conversations, so you send the whole history every time.

There's also a `system` parameter that sets Claude's persona and instructions before the conversation starts. That's how you tell it "you are a senior molecular biologist" and it shapes every response after that.

---

#### Streaming

When you call an API normally, you wait for the entire response before you see anything. If Claude is writing a 500-word protocol audit, you stare at a blank screen for 10 seconds and then the whole thing appears at once.

Streaming changes that. Instead of waiting for the whole response, you receive it word by word as it's being written, exactly like watching someone type in real time. The user sees output immediately, and long responses don't feel like they're hanging.

In code, instead of `client.messages.create()`, you use `client.messages.stream()` with a context manager:

```python
with client.messages.stream(model="claude-opus-4-6", ...) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

In Streamlit specifically, there's a function called `st.write_stream()` that handles all of this. You give it a generator that yields text chunks, and Streamlit renders them live on the page.

Streaming is almost always the right choice for AI responses. It makes the app feel faster even when it isn't, and it prevents timeouts on long responses.

---

#### Streamlit

Streamlit is a Python library that turns a Python script into a web app. No HTML, no CSS, no JavaScript required.

Normally building a web app means writing frontend code (what the user sees) separately from backend code (the logic). Streamlit collapses that into one Python file. You write `st.text_area("Paste your protocol")` and it becomes a text input on a webpage. `st.button("Audit")` becomes a clickable button. `st.write(result)` renders the output.

Every time a user interacts with the page, clicks a button, types in a box, Streamlit reruns your entire Python script from top to bottom. That's a weird mental model at first (it's not how normal web apps work) but it means the UI always reflects the current state of your code.

`st.session_state` is how you persist information across those reruns. It's a dictionary that survives the rerun cycle. That's how auth works: after login, I store `st.session_state["logged_in"] = True`, so when the script reruns it knows the user is still logged in.

---

#### REST APIs

REST APIs are how most databases and services expose their data over the internet. You send a request to a URL with some parameters, you get structured data (usually JSON) back.

Example, searching PubMed for papers about MeDIP-seq:

```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
    ?db=pubmed&term="MeDIP-seq"&retmax=5&retmode=json
```

That returns a list of PubMed IDs. You then make a second call to fetch the actual paper details. No special library needed, just `requests.get(url, params={...})` in Python.

NCBI (PubMed), UniProt, ChEMBL, and PubChem all have free REST APIs that don't require API keys for basic use. That's how the Database Search and Literature Cross-Reference features work: direct HTTP calls, no intermediary.

---

#### SQLite

SQLite is a database that lives in a single file on your computer. No server to set up, no credentials, no configuration. You just open the file and start storing data.

It's used in BenchClaw for two things: storing user accounts (username, salted password hash) and storing saved protocols with share tokens. The database file is called `benchclaw.db` and gets created automatically when the app starts.

The reason to use a database rather than a text file or JSON file is that it handles concurrent access safely (multiple reruns of the Streamlit script all hitting the same data without corrupting it) and lets you query by specific fields like a token or user ID.

---

#### Why I couldn't use LabClaw's brain module directly

LabClaw has a `brain` module that wraps all the scientific database tools (including PubMed search, protein lookup, etc.). I wanted to use it directly in the app. It didn't work.

The reason: LabClaw's code uses a Python feature called `StrEnum`, a type of enum that's also a string. `StrEnum` was added to Python's standard library in **Python 3.11**. The Python version running the app is **3.9**. When the app tried to import `labclaw.brain`, Python hit that line and crashed immediately.

The fix was to call the underlying databases directly via their REST APIs, which is exactly what LabClaw's wrappers do internally anyway. Same data, one less layer. It works fine, but it means the app isn't using LabClaw the way it was designed to be used. That's something to fix properly once I'm on Python 3.11+.

---

### Architecture decisions

**Why three files instead of one?**

The app started as one file (`benchclaw_app.py`). Once I added six more features, it would have grown to ~900 lines in one place. I split it into:

- `benchclaw_app.py` - routing, auth gate, the original three features
- `benchclaw_features.py` - all six new features and export helpers
- `benchclaw_db.py` - all database operations (user accounts, protocol saving)

The principle: separate things by what changes together. Auth logic and database schema change for different reasons than UI features. Keeping them separate makes each file easier to read and modify.

**Why no external auth library?**

User authentication libraries add dependencies and opinions about how auth should work. For a local tool, the stdlib is enough: `hashlib` for hashing, `secrets` for generating random salts and tokens, `sqlite3` for storing it all. The passwords are salted before hashing, which means even if someone got the database file, they couldn't reverse-engineer the passwords.

**Why are shared protocol links accessible without login?**

Intentional. If I generate a protocol and want to send it to a colleague, they shouldn't have to create an account to read it. The share link is a random 16-character URL-safe token (`secrets.token_urlsafe(12)`). Knowing the token is enough to view the protocol. It's the same model GitHub uses for secret gists.

---

### What's next

The intelligence layer for images. The end goal is: I take a photo or video at the bench, feed it to the app, and BenchClaw understands what's happening. What reagent is in that tube, what step I'm on, what the gel looks like, whether the cell morphology looks right.

Claude already supports image input (vision). The groundwork is the protocol and database layer I built today. Once the app understands what a correct protocol looks like, it has a baseline to compare visual observations against. That's the connection between today's work and the hardware vision.

The next concrete step is building an image upload interface and prompting Claude to interpret bench photos in the context of a specific protocol.

import base64
import json
import time
import asyncio
from pathlib import Path

import requests
from groq import Groq
from fastmcp import Client

from config import HEADERS, GROQ_KEY, STT_MODEL, LLM_MODEL, TTS_MODEL, SPEAKER, LANG, MAX_TOKENS
from logger import log

client = Groq(api_key=GROQ_KEY)
mcp = Client("http://127.0.0.1:8001/mcp")
sarvam = requests.Session()      # connection khula rehta hai -> har baar naya nahi banta
connected = False
HISTORY = Path(__file__).with_name("logs") / "history.json"   # project folder me hi bane

# tool ka naam khud ek keyword hai (search_loan -> loan), saath me kuch aam shabd.
# KRAM ZAROORI HAI: upar wala pehle check hota hai, isliye khaas tool pehle rakho.
# "total" aur "upfront" legal me hai -> "total kitna lagega" wala sawal charges wale page pe jaye
TOOLS = {
    "search_loan":  "loan emi eligibility cibil salary income downpayment payment interest subsidy tenure".split(),
    "search_legal": "stamp duty registry registration gst patta khatedari rera brokerage "
                    "charge charges document documents total upfront".split(),
    "search_properties": "property flat villa plot bhk price cost area sqft floor "
                         "parking furnished locality possession".split(),
}

# Serper tabhi chalegi jab sawal me in me se koi shabd ho.
# Iska side effect: "gold rate today" jaisa sawal bhi Serper pe chala jayega (kyunki "rate" hai)
DOMAIN_WORDS = set(
    "property flat villa plot bhk house home buy sell rent price cost rate "
    "area sqft sqyd yard floor parking furnished locality possession "
    "loan emi eligibility salary income downpayment payment interest subsidy tenure bank "
    "registry registration stamp duty gst patta khatedari rera "
    "brokerage broker builder dealer maintenance deposit booking token circle "
    "charge charges document documents total upfront".split())

PROMPT = ("You are a real estate voice assistant for a property dealer in Jaipur. "
          "Answer ONLY from the context below, never from your own knowledge. "
          "One or two short sentences, under 20 words."
          "Say amounts exactly as written in the context, in lakh or crore. "
          "If the answer is not in the context, reply exactly: "
          "Sorry, I do not have that information.")
SORRY_HEARD = "Sorry, I could not hear you clearly. Please try again."
SORRY_FOUND = "Sorry, I could not find that information."
OFF_TOPIC = "I can only answer questions about properties, home loans and registration."

# in teeno ki awaaz badalti nahi -> ek baar bana ke memory me rakh lo
FIXED_REPLIES = (SORRY_HEARD, SORRY_FOUND, OFF_TOPIC)
SAVED_AUDIO = {}


def since(t):
    return round(time.time() - t, 2)


def pick_tool(question):
    """Sawal me jo shabd mila, wahi tool chalao."""
    q = question.lower()
    words = q.replace("?", " ").split()
    for tool, extra in TOOLS.items():
        if tool.replace("search_", "").rstrip("s") in q or any(w in words for w in extra):
            return tool
    return "search_knowledge"


def is_domain(question):
    """Sawal property se juda hai ya nahi. rstrip se charges/documents bhi match ho jate hain."""
    return bool({w.rstrip("s") for w in question.lower().replace("?", " ").split()} & DOMAIN_WORDS)


def save_record(record):
    """Chat history logs/history.json me jod do."""
    HISTORY.parent.mkdir(exist_ok=True)

    try:
        old = json.loads(HISTORY.read_text(encoding="utf-8"))
    except Exception:          # file nahi hai, khali hai, ya aadhi likhi hai
        old = []

    HISTORY.write_text(json.dumps(old + [record], indent=2, ensure_ascii=False),
                       encoding="utf-8")


async def ask_tool(tool, question):
    """MCP se EK HI BAAR judo, phir wahi connection chalta rehta hai."""
    global connected
    if not connected:
        t = time.time()
        await mcp.__aenter__()
        connected = True
        log.info(f"MCP connected in {since(t)}s")

    return str((await mcp.call_tool(tool, {"query": question})).data)


async def answer(question, sec):
    """Local me dhoondo, jawab na bane to web try karo. Property ka sawal na ho to mana kar do."""
    ai, tokens = "", (0, 0, 0)

    for tool in (pick_tool(question), "search_web_tool"):
        t = time.time()
        context = await ask_tool(tool, question)
        sec["search_sec"] += since(t)

        if "NOT_FOUND" not in context:              # ye word tools.py bhejti hai
            t = time.time()
            ai, tokens = await asyncio.to_thread(ask_llm, question, context)
            sec["llm_sec"] += since(t)

            if "do not have" not in ai.lower():
                return tool, ai, tokens             # jawab mil gaya

        if not is_domain(question):                 # property ka sawal hi nahi -> web mat jao
            return "off_topic", OFF_TOPIC, tokens

    return "search_web_tool", ai or SORRY_FOUND, tokens


def ask_llm(question, context):
    """Context se chhota jawab banao. Khali aaya to sorry bol do."""
    res = client.chat.completions.create(
        model=LLM_MODEL, max_completion_tokens=MAX_TOKENS, temperature=0.2,
        messages=[{"role": "system", "content": PROMPT},
                  {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}])
    answer = (res.choices[0].message.content or "").strip() or SORRY_FOUND
    u = res.usage
    return answer, (u.prompt_tokens, u.completion_tokens, u.total_tokens) if u else (0, 0, 0)


def speech_to_text(file):
    """Awaaz se text (Sarvam STT)."""
    with open(file, "rb") as f:
        res = sarvam.post("https://api.sarvam.ai/speech-to-text", headers=HEADERS, timeout=60,
                          files={"file": ("audio.webm", f, "audio/webm")},
                          data={"model": STT_MODEL, "language_code": LANG})
    if res.status_code != 200:
        raise Exception(f"STT Error: {res.text}")
    return res.json().get("transcript", "")


def text_to_speech(text, file):
    """Text se awaaz (Sarvam TTS). Fixed jawab ki awaaz ek hi baar banti hai."""
    audio = SAVED_AUDIO.get(text)

    if audio is None:
        res = sarvam.post("https://api.sarvam.ai/text-to-speech", headers=HEADERS, timeout=30,
                          json={"text": text, "language_code": LANG, "speaker": SPEAKER,
                                "model": TTS_MODEL, "output_audio_codec": "mp3"})
        if res.status_code != 200:
            raise Exception(f"TTS Error: {res.text}")

        audio = base64.b64decode(res.json()["audios"][0])

        if text in FIXED_REPLIES:      # ye teen jawab hamesha same hote hain
            SAVED_AUDIO[text] = audio

    with open(file, "wb") as f:
        f.write(audio)


async def run(in_file, out_file):
    """Pura pipeline: awaaz -> tool -> LLM -> awaaz."""
    t0 = t = time.time()

    # bahut chhoti recording me awaaz hoti hi nahi -> Sarvam ko bhejne ka fayda nahi
    if Path(in_file).stat().st_size < 1000:
        user = ""
    else:
        user = await asyncio.to_thread(speech_to_text, in_file)

    sec = {"stt_sec": since(t), "search_sec": 0, "llm_sec": 0}

    if user.strip():
        tool, ai, tokens = await answer(user, sec)
    else:
        tool, ai, tokens = "none", SORRY_HEARD, (0, 0, 0)   # awaaz samajh nahi aayi

    t = time.time()
    await asyncio.to_thread(text_to_speech, ai, out_file)
    sec["tts_sec"] = since(t)
    sec["total_sec"] = since(t0)
    sec = {k: round(v, 2) for k, v in sec.items()}      # jodne se aaye lambe decimal saaf

    log.info(f"STT={sec['stt_sec']}s | SEARCH={sec['search_sec']}s | LLM={sec['llm_sec']}s "
             f"| TTS={sec['tts_sec']}s | TOTAL={sec['total_sec']}s | tool={tool}")
    log.info(f"TOKENS: in={tokens[0]} out={tokens[1]} total={tokens[2]}")
    log.info(f"USER: {user} | AI: {ai}")

    meta = {"tool": tool, **sec, "tokens_in": tokens[0],
            "tokens_out": tokens[1], "total_tokens": tokens[2]}
    save_record({"time": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "question": user, "answer": ai, **meta})

    return user, ai, meta

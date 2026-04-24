# backend.py — AI Error Detective Core Engine
import os
import re
import base64
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not found!\n"
        "Create a .env file and add:\n"
        "GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx"
    )

# ── LLM Setup ──
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    temperature=0.3,
    model="llama-3.3-70b-versatile"
)
parser = StrOutputParser()
client = Groq(api_key=GROQ_API_KEY)


# ─────────────────────────────────────────────
# PROMPTS (unchanged)
# ─────────────────────────────────────────────

ERROR_ANALYSIS_PROMPT = """
You are an expert SAP Developer and Debugger specializing in:
- SAP BTP (Business Technology Platform)
- CAP (Cloud Application Programming Model)
- ABAP Cloud and ABAP on-premise
- SAP Fiori and UI5
- SAP S/4HANA Cloud

A developer has submitted the following error. Analyze it and respond in EXACT format:

---
## 🔴 SEVERITY
[Write ONLY one of: CRITICAL / HIGH / MEDIUM / LOW]
[One sentence explaining why]

## 📋 ERROR SUMMARY
[2-3 sentences explaining what this error means in simple language]

## 🔍 ROOT CAUSE ANALYSIS
[Detailed explanation of WHY this error is happening]
[Mention exact SAP components, modules, or configurations involved]

## 🛠️ STEP-BY-STEP FIX
[Numbered steps to fix — include transaction codes, config paths, code changes]

## 💻 CORRECTED CODE
[Provide corrected code block if needed, else write "No code change required"]

## ⚡ QUICK TIPS
[3 bullet points to prevent this error in future]

## 📚 SAP REFERENCES
[Relevant SAP Notes, transaction codes, or documentation]
---

ERROR DETAILS:
Platform/Type: {error_type}
Error Message:
{error_text}

Base response strictly on the error. Do not hallucinate.
"""

CHAT_PROMPT = """
You are an expert SAP debugging assistant specializing in BTP, CAP, ABAP Cloud, Fiori.

You analyzed this error:
{error_text}

Previous Analysis:
{previous_analysis}

Answer the follow-up question clearly based on the error context.
If unrelated to error, politely redirect.

Developer Question: {question}
"""

QUICK_FIX_PROMPT = """
You are an SAP expert. Give ONLY a 3-line quick fix for this error.
Be direct. No long explanation. Just the fix steps.

Error: {error_text}
Platform: {error_type}
"""


# ─────────────────────────────────────────────
# CORE FUNCTIONS
# ─────────────────────────────────────────────

def analyze_error(error_text: str, error_type: str) -> dict:
    if not error_text.strip():
        raise ValueError("Error text cannot be empty")

    prompt = PromptTemplate(
        input_variables=["error_text", "error_type"],
        template=ERROR_ANALYSIS_PROMPT
    )
    chain    = prompt | llm | parser
    response = chain.invoke({
        "error_text": error_text[:5000],
        "error_type": error_type
    })
    severity = extract_severity(response)

    return {
        "analysis":   response,
        "severity":   severity,
        "error_text": error_text,
        "error_type": error_type,
    }


def extract_severity(analysis_text: str) -> str:
    text_upper = analysis_text.upper()
    for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if level in text_upper:
            return level
    return "UNKNOWN"


def get_quick_fix(error_text: str, error_type: str) -> str:
    prompt = PromptTemplate(
        input_variables=["error_text", "error_type"],
        template=QUICK_FIX_PROMPT
    )
    chain = prompt | llm | parser
    return chain.invoke({
        "error_text": error_text[:2000],
        "error_type": error_type
    })


def chat_about_error(
    error_text: str,
    previous_analysis: str,
    question: str
) -> str:
    if not question.strip():
        return "Please ask a question about the error."

    prompt = PromptTemplate(
        input_variables=["error_text", "previous_analysis", "question"],
        template=CHAT_PROMPT
    )
    chain = prompt | llm | parser
    return chain.invoke({
        "error_text":        error_text[:2000],
        "previous_analysis": previous_analysis[:3000],
        "question":          question
    })


def extract_text_from_image(image_file) -> str:
    """
    Extract text from SAP error screenshot using
    Groq Vision LLM — no tesseract needed.
    """
    try:
        from PIL import Image

        # Read image
        image_file.seek(0)
        img_bytes = image_file.read()
        img_b64   = base64.b64encode(img_bytes).decode("utf-8")

        # Get format
        image_file.seek(0)
        img  = Image.open(image_file)
        fmt  = (img.format or "PNG").lower()
        mime = f"image/{fmt}"

        # Call Groq vision
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{img_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": (
                                "This is a screenshot of an SAP error message. "
                                "Extract ALL visible text exactly as shown. "
                                "Include error codes, stack traces, "
                                "program names, line numbers, "
                                "and all technical details."
                            )
                        }
                    ]
                }
            ],
            max_tokens=1000,
        )

        extracted = response.choices[0].message.content.strip()
        return extracted if extracted else "No text found in image."

    except Exception as e:
        return (
            f"Could not read image: {str(e)}\n"
            "Please copy-paste the error text in the Analyze Error tab."
        )


def get_severity_color(severity: str) -> str:
    return {
        "CRITICAL": "#FF0000",
        "HIGH":     "#FF6B00",
        "MEDIUM":   "#FFB800",
        "LOW":      "#00B050",
        "UNKNOWN":  "#808080",
    }.get(severity, "#808080")


def get_severity_emoji(severity: str) -> str:
    return {
        "CRITICAL": "🔴",
        "HIGH":     "🟠",
        "MEDIUM":   "🟡",
        "LOW":      "🟢",
        "UNKNOWN":  "⚪",
    }.get(severity, "⚪")


def format_download_report(result: dict, chat_history: list) -> str:
    lines = [
        "=" * 60,
        "AI ERROR DETECTIVE — RESOLUTION REPORT",
        "=" * 60,
        f"Platform : {result.get('error_type', 'N/A')}",
        f"Severity : {result.get('severity',   'N/A')}",
        "=" * 60,
        "",
        "ERROR SUBMITTED:",
        "-" * 40,
        result.get("error_text", ""),
        "",
        "AI ANALYSIS:",
        "-" * 40,
        result.get("analysis", ""),
        "",
    ]

    if chat_history:
        lines += ["FOLLOW-UP Q&A:", "-" * 40]
        for msg in chat_history:
            role = "Developer" if msg["role"] == "user" else "AI Detective"
            lines += [f"{role}: {msg['content']}", ""]

    lines += [
        "=" * 60,
        "Generated by AI Error Detective",
        "Built with Groq LLaMA 3.3 + LangChain + Streamlit",
        "=" * 60,
    ]
    return "\n".join(lines)
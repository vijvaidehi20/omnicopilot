"""
AI service — standardized Groq LLM integration.
"""
import os
import json
import re
import traceback
from typing import Optional

from openai import OpenAI
from dotenv import load_dotenv

from database import get_db
from models import User
from sqlalchemy.orm import Session
from datetime import datetime
from tools.definitions import get_tools_prompt_section
from tools.registry import execute_tool

load_dotenv()

# DEBUG ENV VARIABLES
print("GROQ_API_KEY:", os.getenv("GROQ_API_KEY"))
print("GROQ_MODEL:", os.getenv("GROQ_MODEL"))

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

import pytz
IST = pytz.timezone("Asia/Kolkata")

# Pre-cache the static part of the tools section
_TOOLS_SECTION = get_tools_prompt_section()

def _build_system_prompt():
    """Build system prompt dynamically so the LLM always knows the EXACT current IST time."""
    now_ist = datetime.now(IST)
    current_datetime = now_ist.strftime("%A, %B %d, %Y at %I:%M %p IST")
    
    return f"""You are OmniCopilot, an AI assistant.
The current date and time is {current_datetime}.

You can either respond normally or decide to call a tool.

Available tools:
{_TOOLS_SECTION}

CRITICAL INSTRUCTIONS FOR TOOL USAGE:

1. SEND vs DRAFT:
   - If user says "send", "send invite", "send email" → use send_email tool (sends immediately)
   - If user says "draft", "create draft" → use draft_email tool (saves as draft only)

2. EDITING EVENTS:
   - If user asks to edit an EXISTING event (e.g., "add attendee", "change time"), use the `update_event` tool.
   - For `update_event`'s `event_id` property, you MUST use the exact alphanumeric `event_id` text extracted from the [CONTEXT] blocks. NEVER guess or use the human-readable 'title' field for the `event_id`.
   - Do NOT use create_event to modify an existing event. Always use update_event.

3. GOOGLE DOCS (STRICT RULES):
   - If the user intent includes "google doc", "save to docs", "create document", or "generate report and save": YOU MUST CALL the `create_document` tool.
   - You MUST generate fully formatted clean paragraphs (minimum 800 words if a report is requested) for the `content` argument.
   - DO NOT print the content in the chat if a document is requested. Return the tool call ONLY.
   - FALLBACK RULE: If the user says "create a report" (without mentioning Google Docs / saving), you MUST ask: "Do you want this saved to Google Docs?"
   - BUT IF the user already mentioned docs (e.g. "create a google doc on AI impact"), DO NOT ASK. Execute the tool directly.

4. DETAILED REPORTS:
   - If the user asks for a "report", "detailed overview", or "structured summary":
     - Minimum length: 800 words.
     - Structure: Clear Title, Introduction, multiple detailed Key Sections with headings, and a comprehensive Conclusion.
     - Language: Professional and academic.

5. CONTEXT AWARENESS:
   - Use the [CONTEXT] blocks in the conversation history for event ids, details, or attendees when sending email invites or using `update_event`.
   
6. FILE Q&A:
   - If the user says "summarize this file", "what is this document about" or asks anything about an uploaded file, use the `analyze_file` tool to query the file's contents safely.

7. REMINDERS (IST TIMEZONE — CRITICAL):
   - The current IST time is {current_datetime}. Use THIS as your reference.
   - If user says "in X minutes", calculate: current time + X minutes. Output that as the scheduled_time in ISO 8601 format.
   - Example: if current time is 07:12 PM IST and user says "in 5 minutes", scheduled_time = "2026-04-19T19:17:00".
   - ALWAYS use 24-hour format for the ISO string but the timezone is Asia/Kolkata.
   - Use `create_reminder` tool.

8. OTHER TOOLS:
   - read_emails: to check inbox.
   - drive tools: to check files or documents.

TOOL FORMAT:
If you decide to use a tool, you MUST output ONLY the raw JSON object. Do NOT include conversational text.
{{
  "tool": "tool_name",
  "arguments": {{ ... }}
}}

Otherwise, respond normally but keep responses concise UNLESS generating a report.
"""


def _extract_tool_call(text: str) -> Optional[dict]:
    """Try to parse the JSON tool call format from the model's response."""
    # 1. Heuristic check
    if '"tool"' not in text or '"arguments"' not in text:
        return None

    print("RAW LLM:", text)
    
    # 2. Try markdown fences first
    json_text = ""
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        json_text = fence_match.group(1)
    else:
        # Fallback to finding the main JSON block
        block_match = re.search(r"(\{.*\})", text, re.DOTALL)
        json_text = block_match.group(1) if block_match else text.strip()

    try:
        # Clean potential markdown or double-braces hallucinations
        json_text = json_text.strip()
        if json_text.startswith("{{") and json_text.endswith("}}"):
            json_text = json_text[1:-1]
            
        # strict=False allows literal newlines in strings
        parsed = json.loads(json_text, strict=False)
        if isinstance(parsed, dict) and "tool" in parsed and "arguments" in parsed:
            return {
                "name": parsed["tool"],
                "parameters": parsed["arguments"]
            }
    except json.JSONDecodeError:
        print(f"[DEBUG] JSON parse failed for: {json_text[:200]}...")
        pass

    return None


def generate_response(messages: list[dict], user: User, db: Session) -> dict:
    """
    Standardized chat function mapping to new AI API.
    """
    model = os.getenv("GROQ_MODEL") or "llama-3.1-8b-instant"
    
    try:
        openai_history = [{"role": "system", "content": _build_system_prompt()}]

        for msg in messages:
            role = "assistant" if msg["role"] == "assistant" else "user"
            openai_history.append({"role": role, "content": msg["content"]})
            
        print(f"[DEBUG] Sending request to Groq model: {model}...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=openai_history,
                temperature=0.7,
                timeout=30.0 # Add timeout to prevent hanging
            )
        except Exception as api_err:
            print(f"[ERROR] Groq API call failed!")
            traceback.print_exc()
            raise Exception(f"Groq API Error: {str(api_err)}")
            
        response_text = response.choices[0].message.content or ""
        
        tool_call = _extract_tool_call(response_text)

        if tool_call:
            tool_name = tool_call.get("name", "")
            tool_params = tool_call.get("parameters", {})
            print(f"TOOL DETECTED: {tool_name}")
            
            # Execute tool with user context
            tool_result = execute_tool(tool_name, tool_params, user, db)

            if tool_result.get("status") == "auth_error":
                return {
                    "response": "Please click the 'Connect Google' button to authorize OmniCopilot to access your Calendar and Gmail.",
                    "tool_used": tool_name,
                    "tool_result": tool_result,
                }

            # Backend response generation
            if tool_result.get("status") == "error":
                error_msg = tool_result.get("result", {}).get("message", "Unknown error")
                final_response = f"Failed to execute {tool_name}: {error_msg}"
            else:
                if tool_name == "create_event":
                    res = tool_result.get("result", {})
                    title = res.get("title", "Meeting")
                    event_id = res.get("event_id", "")
                    start_time = res.get("start_time", "")
                    meet_link = res.get("meet_link", "")
                    attendees = res.get("attendees", [])
                    
                    # Minimal text — the MeetingCard handles the display
                    final_response = f"✅ Meeting **{title}** created."
                    
                    # Inject last_event context for follow-up actions
                    attendees_str = ", ".join(attendees) if attendees else "none"
                    context_msg = (
                        f"[CONTEXT] Last created event: event_id={event_id}, "
                        f"title={title}, time={start_time}, meet_link={meet_link}, "
                        f"attendees=[{attendees_str}]"
                    )
                    # Append context to the conversation so LLM can reference it
                    openai_history.append({"role": "assistant", "content": context_msg})
                    
                    # Store context in tool_result for the frontend
                    tool_result["_event_context"] = context_msg
                
                elif tool_name == "update_event":
                    res = tool_result.get("result", {})
                    title = res.get("title", "Meeting")
                    event_id = res.get("event_id", "")
                    start_time = res.get("start_time", "")
                    meet_link = res.get("meet_link", "")
                    attendees = res.get("attendees", [])
                    
                    final_response = f"✅ Event **{title}** updated."
                    
                    # Update the context with new state
                    attendees_str = ", ".join(attendees) if attendees else "none"
                    context_msg = (
                        f"[CONTEXT] Last updated event: event_id={event_id}, "
                        f"title={title}, time={start_time}, meet_link={meet_link}, "
                        f"attendees=[{attendees_str}]"
                    )
                    tool_result["_event_context"] = context_msg

                elif tool_name == "send_email":
                    res = tool_result.get("result", {})
                    to = res.get("to", "")
                    final_response = f"✅ Email sent to **{to}**."

                elif tool_name == "read_emails":
                    emails = tool_result.get("result", {}).get("emails", [])
                    if not emails:
                        final_response = "You have no new emails in your inbox."
                    else:
                        final_response = f"Here are your **{len(emails)} latest emails**:\n"
                        for e in emails:
                            final_response += f"\n• **{e['subject']}** — {e['from']}"
                            
                elif tool_name == "draft_email":
                    res = tool_result.get("result", {})
                    to = res.get("to", "")
                    final_response = f"✅ Draft saved for **{to}**."

                elif tool_name == "create_document":
                    res = tool_result.get("result", {})
                    title = res.get("title", "Document")
                    doc_link = res.get("doc_link", "#")
                    final_response = f"✅ Document created: **{title}**\n📄 [Open Document]({doc_link})"
                    
                elif tool_name == "create_reminder":
                    res = tool_result.get("result", {})
                    msg = res.get("message", "Reminder")
                    display_time = res.get("display_time", "soon")
                    final_response = f"Got it. I’ll remind you to {msg} at {display_time}."

                elif tool_name in ["summarize_document", "analyze_file"]:
                    # Keep the 2nd LLM pass only for this specific intelligence tool
                    print(f"[DEBUG] Generating AI response based on document for {tool_name}...")
                    
                    if tool_name == "analyze_file":
                        user_question = tool_params.get("question", "Summarize this file")
                        doc_content = tool_result.get('result', {}).get('content', '')
                        filename = tool_result.get('result', {}).get('filename', 'Unknown File')
                        tool_context = (
                            f"The user uploaded file '{filename}' with content:\n"
                            f"```\n{doc_content[:10000]}\n```\n"
                            f"Based strictly on this file, answer the user's prompt: '{user_question}'"
                        )
                    else:
                        tool_context = (
                            f"The document content was extracted successfully:\n"
                            f"```\n{tool_result.get('result', {}).get('content', '')[:10000]}\n```\n"
                            "Please provide a comprehensive summary of this document."
                        )
                        filename = tool_result.get('result', {}).get('filename', 'Unknown File')

                    openai_history.append({"role": "assistant", "content": response_text})
                    openai_history.append({"role": "user", "content": tool_context})
                    
                    summary_resp = client.chat.completions.create(
                        model=model,
                        messages=openai_history,
                        temperature=0.7
                    )
                    summary_text = summary_resp.choices[0].message.content or "Response could not be generated."
                    
                    # Return formatted as requested
                    final_response = f"**{filename}** Analysis:\n\n{summary_text}"
                
                else:
                    final_response = f"Tool '{tool_name}' executed successfully."

            if tool_name in ["summarize_document", "analyze_file", "create_reminder"]:
                return {
                    "type": "text",
                    "response": final_response,
                    "tool_used": None,
                    "tool_result": None,
                }
            
            return {
                "type": "tool",
                "response": final_response,
                "tool_used": tool_name,
                "tool_result": tool_result,
            }

        return {
            "type": "text",
            "response": response_text,
            "tool_used": None,
            "tool_result": None,
        }
    except Exception as e:
        traceback.print_exc()
        print("FULL GROQ ERROR:", str(e))
        return {
            "type": "text",
            "response": f"AI error: {str(e)}",
            "tool_used": None,
            "tool_result": None
        }

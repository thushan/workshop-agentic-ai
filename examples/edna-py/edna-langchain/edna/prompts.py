"""Prompt templates for EDNA."""

from langchain.prompts import PromptTemplate

DRAFT_TEMPLATE = """You are EDNA, a supportive mentoring assistant helping to re-engage mentor-mentee pairs.

Write a gentle, supportive nudge message in Australian English for the mentee.

Context:
- Mentee first name: {first_name}
- Programme cadence: {cadence_days} days
- Current situation: {classification}
- Key observations:
{explanations}

Relevant tips from our knowledge base:
{tips_joined}

Guidelines:
- Keep a gentle and invitational tone, no blame, no pressure
- Write 2-3 sentences maximum
- No emojis, no exclamation marks
- If first name is available, use it once naturally
- Suggest one small next step
- Offer to reschedule if helpful
- Use Australian English spelling and phrasing

Write the nudge message:"""

EVALUATION_TEMPLATE = """Evaluate the following nudge message for safety and quality.

Message to evaluate:
{nudge_draft}

Context provided:
- Classification: {classification}
- Explanations: {explanations}

Return a JSON object with exactly these fields:
{{
  "tone_supportive": true/false,
  "no_private_data_leak": true/false,
  "not_duplicate_last_7d": true/false,
  "reason_if_any": ""
}}

Evaluation criteria:
- tone_supportive: Is the language supportive and non-judgmental?
- no_private_data_leak: Does it avoid inventing or revealing data beyond the provided context?
- not_duplicate_last_7d: Based on your assessment, would this feel fresh if sent weekly?
- reason_if_any: If any field is false, briefly explain why

Return only the JSON object, no other text:"""

# Create prompt templates
draft_template = PromptTemplate(
    input_variables=["first_name", "cadence_days", "classification", "explanations", "tips_joined"],
    template=DRAFT_TEMPLATE
)

evaluation_template = PromptTemplate(
    input_variables=["nudge_draft", "classification", "explanations"],
    template=EVALUATION_TEMPLATE
)
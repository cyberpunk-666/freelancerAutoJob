API_KEY="YOUR_API_KEY"

# Adjust safety settings in generationConfig below.
# See https://ai.google.dev/gemini-api/docs/safety-settings
curl \
  -X POST https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key=${API_KEY} \
  -H 'Content-Type: application/json' \
  -d @<(echo '{
  "contents": [
    {
      "role": "user",
      "parts": [
        {
          "text": "Budget: $30-250 USD\n\n        Please convert the budget to CAD"
        }
      ]
    },
    {
      "role": "model",
      "parts": [
        {
          "text": "```json\n{\n\"max_budget_cad\":396.75,\n\"min_budget_cad\":39.67,\n\"rate_type\":\"fixed\"\n} \n```"
        }
      ]
    },
    {
      "role": "user",
      "parts": [
        {
          "text": "INSERT_INPUT_HERE"
        }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 1,
    "topK": 64,
    "topP": 0.95,
    "maxOutputTokens": 8192,
    "responseMimeType": "application/json",
    "responseSchema": {
      "type": "object",
      "properties": {
        "min_budget_cad": {
          "type": "number",
          "format": "float"
        },
        "max_budget_cad": {
          "type": "number",
          "format": "float"
        },
        "rate_type": {
          "type": "string",
          "enum": [
            "hourly",
            "fixed"
          ]
        }
      },
      "required": [
        "min_budget_cad",
        "max_budget_cad",
        "rate_type"
      ]
    }
  }
}')
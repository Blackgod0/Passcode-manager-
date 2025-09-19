# app.py
import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
import requests

from analysis_utils import score_password, make_local_suggestions, generate_strong_password

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_ENDPOINT = os.getenv("GEMINI_ENDPOINT")  # Example: "https://api.gemini.example/v1/generate"

app = Flask(__name__)
CORS(app)  # Allow cross origin (adjust in production)


@app.route("/api/analyze", methods=["POST"])
def analyze_password():
    """
    Analyze password strength locally and optionally query Gemini AI.
    Expects JSON: { "password": "<plaintext password>" }
    SECURITY: Raw password is never sent to Gemini API.
    """
    data = request.get_json(silent=True)
    if not data or "password" not in data:
        return jsonify({"error": "Missing 'password' in request body."}), 400

    password = data["password"]

    # Basic input validation
    if not isinstance(password, str):
        return jsonify({"error": "Invalid password type."}), 400
    if len(password) > 1000:
        return jsonify({"error": "Password too long."}), 400

    # Local deterministic analysis
    analysis = score_password(password)
    local_suggestions = make_local_suggestions(analysis)

    # Features sent to AI (never the raw password)
    features = {
        "length": analysis["length"],
        "entropy": analysis["entropy"],
        "classes": analysis["classes"],
        "problems": analysis["problems"],
        "score": analysis["score"],
    }

    ai_response = None

    # Try Gemini API if configured
    if GEMINI_API_KEY and GEMINI_ENDPOINT:
        try:
            prompt = (
                "You are an expert password security assistant. "
                "Do NOT request or accept the raw password. "
                "Given these anonymized password features, provide:\n"
                "1) A short classification (very weak / weak / moderate / strong)\n"
                "2) A clear, non-technical explanation of *why* (2-4 sentences)\n"
                "3) Specific, actionable suggestions to improve the password (3-6 items)\n"
                "4) Provide 3 alternative strong passwords (randomly generated).\n\n"
                f"Features: {json.dumps(features)}\n\n"
                "Respond as JSON with keys: classification, explanation, suggestions, alternatives\n"
            )

            url = f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            body = {
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ]
            }

            r = requests.post(url, headers=headers, json=body, timeout=10)
            r.raise_for_status()
            data = r.json()

            # Try extracting AI response safely
            ai_text = None
            try:
                ai_text = data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError):
                app.logger.warning("Unexpected Gemini response format: %s", data)

            if ai_text:
                try:
                    ai_response = json.loads(ai_text)
                except Exception:
                    ai_response = {"explanation": ai_text}

        except Exception as e:
            app.logger.warning("Gemini call failed: %s", str(e))
            ai_response = None

    # If AI not available → use local fallback
    if not ai_response:
        class_map = {
            0: "very weak",
            1: "weak",
            2: "moderate",
            3: "strong",
            4: "very strong",
        }
        classification = class_map.get(analysis["score"], "unknown")
        explanation = (
            f"Estimated entropy: {analysis['entropy']} bits. "
            f"Includes classes: {', '.join([k for k,v in analysis['classes'].items() if v]) or 'none'}. "
            f"Issues found: {', '.join(analysis['problems']) or 'none'}."
        )
        alternatives = [generate_strong_password(16) for _ in range(3)]
        ai_response = {
            "classification": classification,
            "explanation": explanation,
            "suggestions": local_suggestions,
            "alternatives": alternatives,
        }

    # Final response
    return jsonify({
        "analysis": analysis,
        "ai": ai_response,
    }), 200


@app.route("/api/generate", methods=["GET"])
def api_generate():
    """
    Endpoint to generate a strong password locally (no AI).
    Query: ?length=16
    """
    try:
        length = int(request.args.get("length", 16))
    except ValueError:
        length = 16
    length = max(8, min(64, length))
    pwd = generate_strong_password(length)
    return jsonify({"password": pwd})


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    app.run(host=host, port=port)

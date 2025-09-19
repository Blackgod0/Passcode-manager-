# analysis_utils.py
import math
import re
from collections import Counter

COMMON_PASSWORDS = {
    # Short list for demo; expand in production
    "password", "123456", "12345678", "qwerty", "abc123", "111111", "iloveyou", "admin",
}

def char_classes(password: str):
    classes = {
        "lower": bool(re.search(r"[a-z]", password)),
        "upper": bool(re.search(r"[A-Z]", password)),
        "digits": bool(re.search(r"[0-9]", password)),
        "symbols": bool(re.search(r"[^\w\s]", password)),
    }
    return classes

def estimate_entropy(password: str) -> float:
    """
    Very small entropy heuristic:
    - entropy per char determined by number of character classes present
    - multiply by length
    This is a heuristic; for production use a stronger estimator.
    """
    classes = char_classes(password)
    pool = 0
    if classes["lower"]:
        pool += 26
    if classes["upper"]:
        pool += 26
    if classes["digits"]:
        pool += 10
    if classes["symbols"]:
        pool += 32  # rough count
    if pool == 0:
        return 0.0
    entropy_per_char = math.log2(pool)
    return round(entropy_per_char * max(1, len(password)), 2)

def contains_common_patterns(password: str):
    lower = password.lower()
    problems = []
    if lower in COMMON_PASSWORDS:
        problems.append("common_password")
    if re.search(r"(.)\1{2,}", password):
        problems.append("repeat_chars")
    if re.search(r"(1234|2345|3456|4567|5678|6789|7890)", password):
        problems.append("sequence_digits")
    if re.search(r"(qwerty|asdf|zxcv)", lower):
        problems.append("keyboard_sequence")
    return problems

def score_password(password: str):
    """
    Score 0..4
    0 = very weak
    4 = very strong
    """
    if not password:
        return 0
    ent = estimate_entropy(password)
    classes = char_classes(password)
    class_count = sum(classes.values())
    problems = contains_common_patterns(password)
    score = 0
    # baseline scoring heuristics
    if len(password) >= 8 and class_count >= 2:
        score += 1
    if len(password) >= 10 and class_count >= 3:
        score += 1
    if ent >= 50:
        score += 1
    if ent >= 80 and class_count >= 3 and not problems:
        score += 1
    # clamp
    score = max(0, min(4, score))
    return {
        "score": score,
        "entropy": ent,
        "class_count": class_count,
        "classes": classes,
        "problems": problems,
        "length": len(password),
    }

def make_local_suggestions(analysis):
    suggestions = []
    length = analysis["length"]
    if length < 12:
        suggestions.append("Use at least 12 characters; longer is better (passphrases are great).")
    if not analysis["classes"]["upper"]:
        suggestions.append("Add uppercase letters (A-Z).")
    if not analysis["classes"]["lower"]:
        suggestions.append("Add lowercase letters (a-z).")
    if not analysis["classes"]["digits"]:
        suggestions.append("Add digits (0-9).")
    if not analysis["classes"]["symbols"]:
        suggestions.append("Add symbols (e.g., !@#$%^&*).")
    if analysis["problems"]:
        if "common_password" in analysis["problems"]:
            suggestions.append("Avoid common passwords and obvious patterns.")
        if "repeat_chars" in analysis["problems"]:
            suggestions.append("Avoid repeated characters (e.g., 'aaaa').")
        if "keyboard_sequence" in analysis["problems"]:
            suggestions.append("Avoid keyboard sequences like 'qwerty'.")
        if "sequence_digits" in analysis["problems"]:
            suggestions.append("Avoid simple numeric sequences like '123456'.")
    if not suggestions:
        suggestions.append("Looks good. Use a password manager to store complex unique passwords.")
    return suggestions

def generate_strong_password(length=16):
    import secrets, string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|:;,.<>/?"
    # ensure each class present
    while True:
        pwd = ''.join(secrets.choice(alphabet) for _ in range(length))
        a = char_classes(pwd)
        if all(a.values()):
            return pwd

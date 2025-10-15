# utils.py
def calc_bmi(weight_kg: float, height_cm: float) -> float:
    if not weight_kg or not height_cm:
        return 0.0
    h_m = height_cm / 100.0
    return round(weight_kg / (h_m * h_m), 2)

def weight_class_from_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "underweight"
    if 18.5 <= bmi < 25:
        return "normal"
    if 25 <= bmi < 30:
        return "overweight"
    return "obese"

def age_band(age: int) -> str:
    if age < 18: return "u18"
    if age <= 25: return "18-25"
    if age <= 35: return "26-35"
    if age <= 45: return "36-45"
    if age <= 55: return "46-55"
    if age <= 65: return "56-65"
    return "65plus"

def signature(profile: dict) -> str:
    """
    Build a signature that groups 'similar' cases.
    You can tune fields used here to control reuse sensitivity.
    """
    parts = [
        f"age:{profile.get('age_band')}",
        f"gender:{profile.get('gender')}",
        f"wclass:{profile.get('weight_class')}",
        f"act:{profile.get('activity')}",
        f"stress:{profile.get('stress')}",
        f"work:{profile.get('work_type')}",
        f"bp:{profile.get('bp')}",
        f"sugar:{profile.get('sugar')}",
        f"thy:{profile.get('thyroid')}",
        f"pcod:{profile.get('pcod')}",
        f"chol:{profile.get('cholesterol')}",
        f"heart:{profile.get('heart')}",
        f"kidney:{profile.get('kidney')}",
        f"preg:{profile.get('pregnancy')}",
        f"diet:{profile.get('diet_pref')}",
        f"allergy:{profile.get('allergies') or 'none'}",
        f"goal:{profile.get('goal')}",
    ]
    return "|".join(parts)

# -*- coding: utf-8 -*-
import random
from copy import deepcopy

###############################################################################
# Helper: sample without repeating too often
###############################################################################

def _pick_week(items, k=7):
    """
    Return a list of k picks from items with minimal repetition.
    If items < k, we shuffle and then allow repeats only after exhausting items.
    """
    items = list(items)
    if not items:
        return ["Simple veg meal"] * k

    picks = []
    pool = items[:]
    random.shuffle(pool)
    for i in range(k):
        if not pool:
            pool = items[:]
            random.shuffle(pool)
        picks.append(pool.pop())
    return picks


###############################################################################
# Helper: simple "avoid + swap" filter for condition & allergy handling
###############################################################################

def _apply_avoids_and_swaps(text, avoids, swaps):
    """
    If any avoid token appears in text (case-insensitive), try a gentle swap.
    'swaps' is a dict like {"white rice":"brown rice", "fried":"grilled"}.
    If no matching swap, annotate as '(modified)' to signal a safer version.
    """
    lowered = text.lower()
    modified = text
    changed = False

    for bad in avoids:
        if bad and bad.lower() in lowered:
            # try to find a specific swap
            replaced_once = False
            for src, dst in (swaps or {}).items():
                if src.lower() in modified.lower():
                    modified = _safe_replace_case_insensitive(modified, src, dst)
                    replaced_once = True
                    changed = True
            if not replaced_once:
                # generic softening
                if "(modified" not in modified.lower():
                    modified += " (modified)"
                changed = True

    # Small cleanups for double-modification
    if changed:
        modified = modified.replace("  ", " ").strip()
    return modified


def _safe_replace_case_insensitive(text, src, dst):
    """
    Replace src with dst, case-insensitively, preserving overall readability.
    """
    idx = text.lower().find(src.lower())
    if idx == -1:
        return text
    return text[:idx] + dst + text[idx + len(src):]


###############################################################################
# Main: generate_plan(profile) -> (plan_dict, updated_profile)
###############################################################################

def generate_plan(profile):
    """
    Build a 7-day diet plan with structured meals + exercise list + notes.
    Returns (plan_dict, updated_profile)

    Required fields used from profile (with fallbacks):
      - weight (kg), height (cm) -> BMI
      - goal: "weight_loss" | "weight_gain" | "fitness" | "strength" (default fitness)
      - stress: "low" | "medium" | "high"
      - diet_pref: "veg" | "non-veg" | "vegan" | "both"
      - allergies: list[str]
      - conditions: derived from:
            bp, sugar, thyroid, pcod, cholesterol, heart, kidney, pregnancy
    """
    # -------- Derive BMI and store back ----------
    try:
        weight = float(profile.get("weight") or 0)
        height_cm = float(profile.get("height") or 0)
        bmi = round(weight / ((height_cm / 100.0) ** 2), 2) if height_cm else 0.0
    except Exception:
        bmi = 0.0

    if bmi < 18.5:
        weight_class = "Underweight"
    elif bmi < 25:
        weight_class = "Normal"
    elif bmi < 30:
        weight_class = "Overweight"
    else:
        weight_class = "Obese"

    profile = dict(profile or {})
    profile["bmi"] = bmi
    profile["weight_class"] = weight_class

    # -------- Read user prefs -----------
    goal = (profile.get("goal") or "fitness").lower()
    stress = (profile.get("stress") or "low").lower()

    # Any casing from HTML form (Veg / Vegan / Both) -> lower canonical
    diet_pref = (profile.get("diet_pref") or "both").strip().lower()
    # normalize values
    if diet_pref == "non-veg":
        diet_pref = "nonveg"
    if diet_pref not in ("veg", "nonveg", "vegan", "both"):
        diet_pref = "both"

    # allergies list
    allergies = set(
        a.strip().lower()
        for a in (profile.get("allergies") or [])
        if isinstance(a, str) and a.strip()
    )

    # -------- Build condition flags --------
    cond = {
        "diabetes": (profile.get("sugar") in ["prediabetic", "diabetic", "yes"]),
        "bp_or_heart": (profile.get("bp") in ["high", "yes"]) or
                       (profile.get("heart") == "yes") or
                       (profile.get("cholesterol") == "high"),
        "thyroid": (profile.get("thyroid") in ["hypo", "hyper", "yes"]),
        "kidney": (profile.get("kidney") == "yes"),
        "pcod": (profile.get("pcod") == "yes"),
        "pregnancy": (profile.get("pregnancy") == "yes"),
    }

    ###########################################################################
    # MEAL LIBRARIES (Large & varied)
    ###########################################################################

    LIB = {
        "veg": {
            "breakfast": [
                "Vegetable oats (no sugar)",
                "Besan chilla + mint chutney",
                "Moong dal chilla + curd",
                "Idli + sambar",
                "Upma with mixed veggies",
                "Poha with peas & carrot (no potato)",
                "Rava uttapam + tomato chutney",
                "Daliya (broken wheat) porridge + nuts",
                "Multigrain toast + peanut butter",
                "Sprouts salad + lemon",
                "Ragi dosa + chutney",
                "Vegetable paratha (low oil) + curd",
            ],
            "lunch": [
                "2 chapati + tur dal + mixed veg sabzi + salad",
                "Brown rice + rajma (small portion) + cucumber salad",
                "Vegetable khichdi (low GI) + salad",
                "Chapati + lauki (bottle gourd) sabzi + salad",
                "Vegetable pulao (low oil) + curd",
                "2 chapati + paneer curry (low oil) + salad",
                "Brown rice + sambar + spinach stir-fry",
                "Millet roti + chana masala + salad",
                "Curd rice (low salt) + beetroot poriyal",
                "Palak chole + half bowl rice + salad",
                "Quinoa pulao + moong dal tadka (light)",
            ],
            "snack": [
                "Fruit bowl (apple/guava/orange) + chia",
                "Buttermilk (unsalted)",
                "Roasted chana",
                "Green tea + murmura",
                "Cucumber + carrot sticks + hummus",
                "Handful of almonds/walnuts",
                "Sprouts chaat (lemon, no potato)",
                "Greek curd + mixed seeds",
            ],
            "dinner": [
                "1 chapati + mix veg curry (low oil)",
                "Moong dal khichdi + salad",
                "Clear veg soup + sautéed veggies",
                "1 roti + palak paneer (low salt)",
                "Vegetable upma + cucumber salad",
                "Soup + multigrain toast",
                "1 chapati + bottle gourd curry",
                "Vegetable stew + small millet dosa",
                "Dal + sautéed beans + salad",
                "Lentil soup + 1 chapati",
            ],
        },
        "nonveg": {
            "breakfast": [
                "2 boiled eggs + multigrain toast",
                "Oats + milk + nuts",
                "Chicken sandwich (multigrain, low mayo)",
                "Egg bhurji + chapati",
                "Scrambled eggs + spinach",
                "Egg white omelette + veggies",
                "Oats pancake + egg white",
            ],
            "lunch": [
                "Grilled chicken + brown rice + salad",
                "Fish curry + 2 chapati + cucumber raita",
                "Egg curry + 2 chapati + salad",
                "Chicken pulao (small portion, low oil) + salad",
                "Boiled eggs + veg salad + chapati",
                "Grilled fish + sautéed veggies + small rice",
                "Chicken curry + millet roti + salad",
            ],
            "snack": [
                "Boiled egg whites + lemon",
                "Chicken soup (clear)",
                "Tuna salad (no mayo)",
                "Greek yogurt + walnuts",
                "Protein shake (no sugar)",
            ],
            "dinner": [
                "Grilled fish + clear soup",
                "Chicken stew + multigrain bread",
                "Egg curry + vegetable soup",
                "Grilled chicken + sautéed veggies",
                "Fish tikka + salad",
            ],
        },
        "vegan": {
            "breakfast": [
                "Soy milk smoothie + berries + oats",
                "Vegan oats porridge + nuts",
                "Chia pudding (unsweetened) + fruit",
                "Almond butter toast",
                "Vegan poha (no ghee)",
                "Tofu scramble + veggies",
                "Ragi porridge + banana (if allowed)",
            ],
            "lunch": [
                "Quinoa + masoor dal + veggies",
                "Vegan pulao + cabbage salad",
                "Chapati + tofu curry",
                "Vegan khichdi (oil, no ghee)",
                "Vegetable stew + salad",
                "Brown rice + beans curry",
                "Chickpea curry + millet roti",
            ],
            "snack": [
                "Soy yogurt + fruit",
                "Roasted seeds trail mix",
                "Vegan smoothie (almond milk)",
                "Roasted chana",
                "Carrot + cucumber sticks + hummus",
            ],
            "dinner": [
                "Veg clear soup + salad",
                "Quinoa + sautéed veggies",
                "Chapati + veg curry (oil, no ghee)",
                "Lentil stew + salad",
                "Tofu curry + small brown rice",
                "Millet roti + mixed veg curry",
            ],
        },
    }

    ###########################################################################
    # CONDITION RULES (avoids + smart swaps + condition notes)
    ###########################################################################

    # Merged flags to a normalized condition set for easier processing
    active_conditions = set()
    if cond["diabetes"]: active_conditions.add("diabetes")
    if cond["bp_or_heart"]: active_conditions.add("bp_or_heart")
    if cond["thyroid"]: active_conditions.add("thyroid")
    if cond["kidney"]: active_conditions.add("kidney")
    if cond["pcod"]: active_conditions.add("pcod")
    if cond["pregnancy"]: active_conditions.add("pregnancy")

    condition_rules = {
        "diabetes": {
            "avoid": ["sugar", "white rice", "sweet", "jaggery", "honey", "dessert", "potato"],
            "swaps": {
                "white rice": "brown rice",
                "sugar": "no added sugar",
                "sweet": "low-GI fruit",
                "honey": "no sweetener",
                "jaggery": "no sweetener",
                "poha": "poha (no potato)",
            },
            "tip": "For diabetes: choose low-GI carbs, add fiber/protein to each meal, space meals evenly, and monitor glucose response.",
        },
        "bp_or_heart": {
            "avoid": ["salt", "pickles", "papad", "fried", "butter", "processed", "sausage"],
            "swaps": {
                "salt": "low salt",
                "fried": "grilled",
                "butter": "olive oil (very little)",
                "pickle": "salad",
            },
            "tip": "For BP/heart/cholesterol: restrict salt and fried foods, prefer grilled/steamed, include leafy greens and pulses.",
        },
        "thyroid": {
            "avoid": ["soy", "cabbage", "cauliflower", "broccoli", "millet (excess)"],
            "swaps": {
                "soy": "paneer/tofu (if allowed) or lentils (if vegan avoid soy)",
                "cabbage": "zucchini",
                "cauliflower": "bottle gourd",
            },
            "tip": "For thyroid: take meds on empty stomach; limit goitrogens (soy, raw cabbage/cauliflower); ensure adequate protein, iodine, selenium.",
        },
        "kidney": {
            "avoid": ["excess protein", "banana", "orange", "tomato (excess)", "spinach (excess)", "salt"],
            "swaps": {
                "banana": "apple/pear",
                "orange": "apple/guava",
                "salt": "low salt",
            },
            "tip": "For kidney: moderate protein and potassium as advised; keep dishes simple and lightly spiced; follow nephrologist guidance.",
        },
        "pcod": {
            "avoid": ["sugary", "dessert", "refined flour", "maida", "soft drink", "juice (packed)"],
            "swaps": {
                "dessert": "fruit + curd",
                "maida": "whole-wheat",
                "juice": "whole fruit",
            },
            "tip": "For PCOD/PCOS: emphasize protein + fiber, low-GI carbs, add strength training, aim for consistent sleep.",
        },
        "pregnancy": {
            "avoid": ["raw papaya", "excess caffeine", "street food", "unpasteurized"],
            "swaps": {
                "coffee": "decaf/limit",
            },
            "tip": "For pregnancy: small frequent meals; include iron, calcium, folate; hydrate well; avoid unpasteurized foods.",
        },
    }

    ###########################################################################
    # GOAL / BMI NOTES
    ###########################################################################

    notes = []

    # BMI-based notes
    if weight_class == "Underweight":
        notes.append("You are underweight: include calorie-dense healthy foods—nuts, milkshakes/smoothies, paneer/tofu/eggs.")
    elif weight_class == "Overweight":
        notes.append("You are overweight: prefer low-GI, high-fiber foods; control portions; limit sugary drinks and fried items.")
    elif weight_class == "Obese":
        notes.append("You are in the obese range: target a modest caloric deficit, prioritize protein + vegetables, and increase daily steps.")
    else:
        notes.append("Balanced plate guidance: ½ vegetables, ¼ protein, ¼ complex carbs.")

    # Goal-based notes
    if goal == "weight_loss":
        notes.append("Goal: Weight loss—aim for a 200–400 kcal daily deficit; 8–10k steps/day; prioritize lean protein and fiber.")
    elif goal == "weight_gain":
        notes.append("Goal: Weight gain—300–500 kcal surplus; 1.6–2.2 g/kg/day protein; strength train 3–5x/week.")
    elif goal in ("strength", "muscle", "strength_gain", "muscle_building"):
        notes.append("Goal: Strength/Muscle—progressive overload 3–5x/week; target 1.6–2.2 g/kg/day protein; time protein post-workout.")
    else:
        notes.append("Goal: General fitness—mix cardio, strength, and mobility work across the week.")

    # Condition notes
    for key in active_conditions:
        tip = condition_rules.get(key, {}).get("tip")
        if tip:
            notes.append(tip)

    # Stress note
    if stress == "high":
        notes.append("High stress reported: add 10–15 minutes of daily mindfulness (box breathing, body scan) and reduce late-night screen time.")

    ###########################################################################
    # EXERCISE PLAN (goal + conditions + stress)
    ###########################################################################

    # Base by goal
    base_exercise = []
    if goal == "weight_loss":
        base_exercise += [
            "Brisk walking 30–45 mins (5 days/week)",
            "Cycling or swimming 25–40 mins (3 days/week)",
            "HIIT 12–18 mins (2 days/week, if medically cleared)",
        ]
    elif goal == "weight_gain":
        base_exercise += [
            "Strength training 4–5 days/week (full-body split, progressive overload)",
            "Post-workout protein within 60 mins",
        ]
    elif goal in ("strength", "muscle", "strength_gain", "muscle_building"):
        base_exercise += [
            "Strength training 4–5 days/week (progressive overload; compound lifts)",
            "Mobility & core 2–3 days/week",
        ]
    else:
        base_exercise += [
            "Walk 8–10k steps/day",
            "Yoga or Pilates 3 sessions/week",
            "Bodyweight basics (push-ups, squats, planks) 2–3 sessions/week",
        ]

    # Stress relaxation
    if stress == "high":
        base_exercise.append("Mindfulness/meditation 10–15 mins daily (e.g., box breathing)")

    # Condition constraints/edits
    if cond["bp_or_heart"]:
        base_exercise.append("Avoid heavy straining; prefer steady-state cardio (walk, cycle), yoga, or swimming")
    if cond["diabetes"]:
        base_exercise.append("Post-meal 15–20 min walk helps glycemic control")
    if cond["thyroid"]:
        base_exercise.append("Combine moderate cardio with flexibility and light strength work")
    if cond["kidney"]:
        base_exercise.append("Gentle walking; avoid overexertion; follow nephrologist guidance")
    if cond["pcod"]:
        base_exercise.append("Mix of strength + cardio 4–5 days/week; prioritize sleep consistency")
    if cond["pregnancy"]:
        base_exercise.append("Light walking; prenatal yoga (only with clinician approval)")

    exercise_plan = list(dict.fromkeys(base_exercise))  # de-duplicate, keep order

    ###########################################################################
    # Build 7-Day Diet Plan (structured: breakfast/lunch/snack/dinner)
    ###########################################################################

    def pick_meal_banks(preference):
        if preference == "veg":
            return deepcopy(LIB["veg"])
        elif preference == "nonveg":
            return deepcopy(LIB["nonveg"])
        elif preference == "vegan":
            return deepcopy(LIB["vegan"])
        else:
            # BOTH: merge veg + nonveg + vegan (without duplicates)
            both = {"breakfast": [], "lunch": [], "snack": [], "dinner": []}
            seen = set()
            for pref_key in ("veg", "nonveg", "vegan"):
                for slot in ("breakfast", "lunch", "snack", "dinner"):
                    for item in LIB[pref_key][slot]:
                        if item not in seen:
                            seen.add(item)
                            both[slot].append(item)
            return both

    meals_bank = pick_meal_banks(diet_pref)

    # Allergy filter (removes items containing allergen tokens)
    if allergies:
        def safe_filter(items):
            out = []
            for item in items:
                text = item.lower()
                if any(a in text for a in allergies):
                    continue
                out.append(item)
            return out

        for slot in ("breakfast", "lunch", "snack", "dinner"):
            meals_bank[slot] = safe_filter(meals_bank[slot])

        # Safety fallback to avoid empty banks
        if not meals_bank["breakfast"]:
            meals_bank["breakfast"] = ["Fruit + oats porridge (no allergen)"]
        if not meals_bank["lunch"]:
            meals_bank["lunch"] = ["Brown rice + lentil curry + salad (no allergen)"]
        if not meals_bank["snack"]:
            meals_bank["snack"] = ["Roasted chana (no allergen)"]
        if not meals_bank["dinner"]:
            meals_bank["dinner"] = ["Veg clear soup + chapati (no allergen)"]

    # Per-condition avoids + swaps aggregated
    combined_avoids = set()
    combined_swaps = {}
    for key in active_conditions:
        rules = condition_rules.get(key) or {}
        for bad in rules.get("avoid", []):
            combined_avoids.add(bad.lower())
        for src, dst in (rules.get("swaps") or {}).items():
            combined_swaps[src] = dst

    # Extra goal-based swaps (gentle)
    if goal == "weight_loss":
        combined_swaps.setdefault("fried", "grilled")
        combined_swaps.setdefault("biryani", "small portion pulao (low oil)")
        combined_swaps.setdefault("paratha", "roti (low oil)")
    elif goal == "weight_gain":
        # allow a bit more energy density
        combined_swaps.setdefault("low oil", "moderate oil")
        combined_swaps.setdefault("no added sugar", "honey (small)")
    # fitness/strength keep defaults

    # Build weekly picks
    week_breakfasts = _pick_week(meals_bank["breakfast"], 7)
    week_lunches = _pick_week(meals_bank["lunch"], 7)
    week_snacks = _pick_week(meals_bank["snack"], 7)
    week_dinners = _pick_week(meals_bank["dinner"], 7)

    # Apply avoids/swaps per item
    def adapt(item):
        return _apply_avoids_and_swaps(item, combined_avoids, combined_swaps)

    diet_plan = {}
    for i in range(7):
        b = adapt(week_breakfasts[i])
        l = adapt(week_lunches[i])
        s = adapt(week_snacks[i])
        d = adapt(week_dinners[i])

        # Portion guidance by BMI/goal (light annotation)
        portion_note = ""
        if goal == "weight_loss" or weight_class in ("Overweight", "Obese"):
            portion_note = " (controlled portion)"
        elif goal == "weight_gain" or weight_class == "Underweight":
            portion_note = " (generous portion)"

        diet_plan[f"Day {i+1}"] = {
            "breakfast": b + portion_note,
            "lunch": l + portion_note,
            "snack": s,
            "dinner": d + portion_note,
        }

    # Lifestyle tips (generic + condition + BMI)
    lifestyle = [
        "Hydration: 2–3 liters water/day (adjust for kidney/doctor advice).",
        "Sleep: target 7–8 hours/night; consistent schedule.",
        "NEAT: stand/move briefly each hour; aim for 8–10k steps/day (tailor to condition).",
        "Cook at home when possible; keep oils minimal; prioritize whole foods.",
    ]
    # condition-specific add-ons already in notes; add a couple more practicals:
    if cond["diabetes"]:
        lifestyle.append("Pair carbs with protein/healthy fats to blunt glucose spikes (e.g., curd/nuts with fruit).")
    if cond["bp_or_heart"]:
        lifestyle.append("Rinse canned foods; prefer fresh; watch packaged snacks for hidden sodium.")
    if cond["thyroid"]:
        lifestyle.append("Keep a consistent routine for thyroid meds; avoid coffee/iron supplements within 4 hours of dose.")
    if cond["kidney"]:
        lifestyle.append("Track daily fluids and potassium/phosphorus per clinician plan; prefer simple soups and boiled veggies.")
    if cond["pcod"]:
        lifestyle.append("Aim for 25–35 g fiber/day; include flaxseed/chia; maintain strength training schedule.")
    if cond["pregnancy"]:
        lifestyle.append("Include folate, iron, calcium sources; avoid unpasteurized dairy and high-mercury fish.")

    # Compose final plan object
    plan = {
        "diet_plan": diet_plan,        # dict: Day -> {breakfast,lunch,snack,dinner}
        "exercise_plan": exercise_plan,  # list of strings
        "notes": notes + lifestyle,    # combined recommendations
    }

    return plan, profile


###############################################################################
# If you want to quick-test locally:
###############################################################################
if __name__ == "__main__":
    sample_profile = {
        "name": "Test",
        "age": 32,
        "gender": "female",
        "weight": 78,
        "height": 164,
        "sleep": 6.5,
        "activity": "low",
        "stress": "high",
        "work_type": "sedentary",
        "goal": "weight_loss",
        "diet_pref": "Both",
        "allergies": ["lactose"],
        "bp": "high",
        "sugar": "prediabetic",
        "thyroid": "hypo",
        "pcod": "yes",
        "cholesterol": "high",
        "heart": "no",
        "kidney": "no",
        "pregnancy": "no",
    }
    plan, prof = generate_plan(sample_profile)
    from pprint import pprint
    pprint(prof)
    pprint(plan["diet_plan"])
    print("\n--- EXERCISE ---")
    for ex in plan["exercise_plan"]:
        print("-", ex)
    print("\n--- NOTES (first 8) ---")
    for n in plan["notes"][:8]:
        print("-", n)

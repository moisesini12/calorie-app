# core.py
def scale_macros(food, grams):
    factor = grams / 100.0
    return {
        "calories": float(food["calories"]) * factor,
        "protein": float(food["protein"]) * factor,
        "carbs": float(food["carbs"]) * factor,
        "fat": float(food["fat"]) * factor,
    }

def calculate_goals(sex: str, age: float, weight: float, height: float, activity: float, deficit_pct: float):
    """
    Devuelve:
    maintenance_kcal, deficit_kcal, protein_g, carbs_g, fat_g
    (misma lógica que tu Tkinter)
    """
    sex = sex.upper().strip()
    if sex == "F":
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5

    maintenance = bmr * activity
    deficit_calories = maintenance * (1 - deficit_pct / 100)

    protein_target = weight * 2.0
    fat_target = weight * 0.8
    remaining_calories = max(maintenance - (protein_target * 4 + fat_target * 9), 0)
    carbs_target = remaining_calories / 4

    return round(maintenance), round(deficit_calories), round(protein_target), round(carbs_target), round(fat_target)


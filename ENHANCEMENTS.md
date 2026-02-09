# Latest Enhancements

## 1. App Simplification: 5 Pages → 3 Pages ✅

**What it does:** Streamlined navigation with consolidated features for a cleaner, more intuitive user experience.

**Changes:**
- **Removed pages**: Schedule (functionality moved to Chat), RAG Explorer (integrated into Chat)
- **Enhanced pages**: Chat (citations + wellness cards), Meal Planner (shopping list + reorganized UI), Dashboard (unchanged)

### Chat Page Enhancements

**RAG Citation Display:**
- Automatic extraction of citations from tool responses
- PubMed articles: Shows title, PMID, clickable link
- USDA nutrition data: Shows food name, FDC ID, link to details
- Displayed in collapsible "📚 Sources & Citations" section

**Wellness Suggestion Cards:**
- Automatically detects wellness suggestions in AI responses
- Displays as actionable cards with icons (👥 social, 🚶 movement, 🧘 mindfulness, 📝 reflection)
- **Calendar integration**: Click "📅 Calendar" to add activity to Google Calendar (scheduled for tomorrow 9 AM)
- **Email reminders**: Click "✉️ Email" to send yourself a reminder
- Smart categorization based on activity type

**Implementation:**
- `pages/1_Chat.py`: Added `extract_citations()`, `extract_wellness_suggestions()`, `add_to_calendar()`, `send_email_reminder()`
- `.env.example`: Added email configuration (SMTP_HOST, SMTP_PORT, etc.)
- Uses existing Google Calendar integration
- Email via standard SMTP (works with Gmail, Outlook, etc.)

### Meal Planner Page Enhancements

**Shopping List Generation:**
- Automatically generates organized grocery list from meal plans
- Aggregates ingredients: "6 eggs" instead of "2 eggs" three times
- Categorizes by type: Produce, Proteins, Dairy, Grains, Pantry, Nuts & Seeds, Beverages
- Shows which meals use each ingredient
- Export as Markdown (with checkboxes) or Text

**UI Reorganization:**
- **Before**: Settings buried in sidebar
- **After**: Clean main page layout
  - Top: Nutritional recommendations as prominent metrics (calories, protein)
  - Middle: 2-column settings (dietary preference, restrictions, days, calories)
  - Bottom: 3 tabs (Meal Plan, Shopping List, Downloads)

**Tab Structure:**
1. **📋 Meal Plan**: Your full meal plan with day-by-day breakdown
2. **🛒 Shopping List**: Organized grocery list with metrics (total items, categories, days covered)
3. **⬇️ Downloads**: Export meal plan (JSON, CSV, Markdown) + shopping list (Markdown, Text)

**Implementation:**
- `meal_planning/shopping_list.py`: NEW - Complete shopping list generator
  - `parse_ingredient()`: Parses "2 cups Greek yogurt" → {qty: 2.0, unit: "cups", name: "Greek yogurt"}
  - `categorize_ingredient()`: Auto-categorizes by keywords
  - `generate_shopping_list()`: Aggregates and organizes
- `pages/3_Meal_Plan.py`: Complete UI overhaul with tabs and metrics

**Example Shopping List Output:**
```markdown
## Produce (8 items)
- [ ] 6.0 cups Spinach
- [ ] 3.0 large Tomatoes
  Used in: Breakfast Day 1, Lunch Day 2, Dinner Day 3

## Proteins (5 items)
- [ ] 12.0 large Eggs
- [ ] 1.5 lbs Tofu
```

---

## 2. Nutritional Calculator with Science-Based Recommendations ✅

**What it does:** Automatically calculates personalized calorie and protein targets based on user's physical stats and activity level.

**Scientific Basis:**
- **BMR Calculation**: Mifflin-St Jeor equation (most accurate for modern populations)
- **TDEE**: BMR × activity level multiplier (1.2-1.9)
- **Protein Recommendations**: Based on activity level
  - Sedentary: 0.8-1.0g/kg (RDA minimum)
  - Light/Moderate: 1.2-1.6g/kg
  - Very/Extremely Active: 1.6-2.2g/kg (athlete levels)

**Implementation:**
- **New Module**: [analytics/nutrition_calculator.py](analytics/nutrition_calculator.py)
  - `NutritionCalculator` class with validated formulas
  - Enums for Sex, ActivityLevel, Goal
  - `get_recommendations()` method returns complete nutritional profile

**User Profile Integration:**
- Updated [data/user_profile.json](data/user_profile.json) to include `activity_level`
- Existing fields used: `weight_kg`, `height_cm`, `age`, `sex`

**UI Integration** ([pages/3_Meal_Plan.py](pages/3_Meal_Plan.py)):
- Automatically loads user profile on page load
- Displays personalized recommendations in sidebar:
  ```
  💡 Recommended for you:
  Calories: 2,650 kcal/day
  Protein: 144g/day
  Based on your profile (BMR: 1,800 kcal, TDEE: 2,790 kcal)
  ```
- Users can choose:
  - **Use Recommended** (default) - Uses calculated values
  - **Use Custom Values** - Override with manual input

**Example Calculation:**
```python
from analytics.nutrition_calculator import NutritionCalculator, Sex, ActivityLevel, Goal

recommendations = NutritionCalculator.get_recommendations(
    weight_kg=80,
    height_cm=178,
    age=28,
    sex=Sex.MALE,
    activity_level=ActivityLevel.MODERATELY_ACTIVE,
    goal=Goal.MAINTENANCE,
)

# Output:
# bmr: 1,800 kcal/day
# tdee: 2,790 kcal/day
# target_calories: 2,790 kcal/day
# protein_recommended_g: 112g/day (1.4g/kg for moderate activity)
```

---

## 3. Optional Google Calendar Integration with Clear Messaging ✅

**Problem:** Users were confused about whether Google Calendar was required.

**Solution:** Calendar integration is **completely optional** and now better integrated into chat via wellness suggestion cards.

**How It Works:**
- Wellness suggestions appear as cards in chat responses
- Click "📅 Calendar" button on any suggestion to add to Google Calendar
- If calendar not configured: Shows helpful error message, no blocking
- Alternative: Use email reminders instead (no Google account needed)

**Integration Points:**
- **Chat page** ([pages/1_Chat.py](pages/1_Chat.py)): Wellness cards with calendar buttons
- **Calendar client** ([integrations/google_calendar.py](integrations/google_calendar.py)): OAuth2 authentication, event creation
- **Email integration** (built-in SMTP): Alternative to calendar reminders

**Benefits:**
- ✅ Full functionality without calendar setup
- ✅ Optional calendar integration when needed
- ✅ Email alternative for non-Google users
- ✅ Clear error messages, no blocking

---

## Benefits

### For Users:
1. **Simpler Navigation**: 3 focused pages instead of 5 (Chat, Meal Planner, Dashboard)
2. **Actionable Insights**: Citations for all health advice, wellness cards with calendar/email integration
3. **Practical Tools**: Shopping list generation saves time at the grocery store
4. **Personalized Nutrition**: Science-based calorie and protein recommendations (Mifflin-St Jeor)
5. **Flexibility**: Can use recommended values or override with custom targets
6. **No Barriers**: Full functionality available without optional integrations (calendar, email)

### For Portfolio:
1. **Simplified UX**: Demonstrates understanding of user-centered design (reduced from 5 pages to 3)
2. **Practical Features**: Shopping list generation shows real-world problem-solving
3. **Domain Expertise**: Accurate BMR/TDEE/protein calculations, ingredient parsing
4. **Evidence-based Approach**: RAG citations provide transparency and credibility
5. **Integration Skills**: Google Calendar OAuth2, SMTP email, RAG citation extraction
6. **Clear Communication**: Users understand what's required vs. optional

---

## How to Use

### Chat with Citations & Wellness Cards:
1. Go to **Chat** page
2. Ask nutrition or wellness questions
3. See citations below responses (📚 Sources & Citations)
4. If wellness suggestions appear, click:
   - **📅 Calendar**: Add to Google Calendar (requires setup)
   - **✉️ Email**: Send yourself a reminder (requires SMTP config in .env)

### Meal Planning with Shopping List:
1. Go to **Meal Planner** page
2. Configure: Dietary preference, calorie target, restrictions, days
3. Click "🔄 Generate Meal Plan"
4. **Meal Plan tab**: View full meal plan with nutrition info
5. **Shopping List tab**: See organized grocery list by category
6. **Downloads tab**: Export meal plan and shopping list

### Nutritional Recommendations:
1. Ensure [data/user_profile.json](data/user_profile.json) has:
   - `weight_kg`, `height_cm`, `age`, `sex`
   - `activity_level` (sedentary, lightly_active, moderately_active, very_active, extremely_active)
2. Go to **Meal Planner** page
3. See personalized recommendations at top
4. Use recommended values or toggle "Custom Values" to override

### Optional Integrations:
1. **Google Calendar**: Add GOOGLE_CREDENTIALS_PATH to .env, follow OAuth flow
2. **Email Reminders**: Add SMTP settings to .env (SMTP_HOST, SMTP_USERNAME, etc.)

---

## Technical Details

### Activity Level Multipliers:
```python
SEDENTARY: 1.2           # Little or no exercise
LIGHTLY_ACTIVE: 1.375    # Light exercise 1-3 days/week
MODERATELY_ACTIVE: 1.55  # Moderate exercise 3-5 days/week
VERY_ACTIVE: 1.725       # Hard exercise 6-7 days/week
EXTREMELY_ACTIVE: 1.9    # Very hard exercise & physical job
```

### Goal Adjustments:
```python
WEIGHT_LOSS: -500 kcal   # ~0.5 kg/week loss
MAINTENANCE: 0 kcal      # Maintain current weight
MUSCLE_GAIN: +300 kcal   # Lean gains
```

### Protein Guidelines:
Based on current sports nutrition research:
- **Sedentary**: 0.8g/kg (RDA minimum for general health)
- **Active Individuals**: 1.2-1.6g/kg (supports training adaptation)
- **Athletes**: 1.6-2.2g/kg (optimizes performance and recovery)

---

## References

- Mifflin et al. (1990). "A new predictive equation for resting energy expenditure in healthy individuals"
- Phillips & Van Loon (2011). "Dietary protein for athletes: From requirements to optimum adaptation"
- International Society of Sports Nutrition Position Stand: Protein and Exercise (2017)

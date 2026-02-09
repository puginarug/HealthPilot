# Data Guide

## Overview

HealthPilot uses wearable health data exported from Google Fit or similar devices. This guide explains data formats, how to get your own data, and how the analytics pipeline processes it.

## Data Files

All data lives in `data/sample/`:

### 1. daily_activity.csv

Daily activity metrics from your wearable device.

**Columns**:
- `date` (YYYY-MM-DD): Calendar date
- `steps` (int): Total daily steps
- `calories_burned` (int): Total calories (BMR + activity)
- `distance_km` (float): Total distance walked/run
- `active_minutes` (int): Minutes of moderate+ intensity activity

**Example**:
```csv
date,steps,calories_burned,distance_km,active_minutes
2025-11-01,8432,2150,6.2,45
2025-11-02,9821,2280,7.5,58
```

**Analytics Used**:
- Rolling averages (7-day, 30-day)
- Trend detection (increasing/declining)
- Weekday vs weekend patterns
- Anomaly detection

### 2. heart_rate.csv

Heart rate measurements at 5-minute intervals.

**Columns**:
- `timestamp` (ISO 8601): Measurement time
- `bpm` (int): Beats per minute

**Example**:
```csv
timestamp,bpm
2025-11-01T08:00:00,72
2025-11-01T08:05:00,74
```

**Analytics Used**:
- Resting HR calculation (measurements <70 bpm)
- Heart rate zones (resting, light, moderate, vigorous)
- Circadian rhythm analysis (average by hour of day)
- Max HR tracking

### 3. sleep.csv

Nightly sleep sessions.

**Columns**:
- `date` (YYYY-MM-DD): Night the sleep started
- `sleep_start` (HH:MM): Bedtime
- `sleep_end` (HH:MM): Wake time
- `duration_hours` (float): Total sleep duration
- `deep_sleep_pct` (float): % in deep sleep stage
- `light_sleep_pct` (float): % in light sleep stage
- `rem_pct` (float): % in REM sleep stage

**Example**:
```csv
date,sleep_start,sleep_end,duration_hours,deep_sleep_pct,light_sleep_pct,rem_pct
2025-11-01,23:15,07:02,7.78,20.2,52.3,27.5
```

**Analytics Used**:
- Average sleep duration
- Bedtime consistency (std dev)
- Social jet lag (weekend vs weekday shift)
- Sleep stage balance

## Exporting from Google Fit

### Step-by-Step

1. **Go to Google Takeout**:
   https://takeout.google.com/

2. **Select Fit data only**:
   - Deselect all products
   - Check only "Fit"

3. **Choose export format**:
   - File type: ZIP
   - Delivery method: Email link

4. **Download and extract**:
   - Google will email you a download link
   - Extract the ZIP file

5. **Locate relevant files**:
   Google Fit exports include multiple JSON files:
   - `Daily activity metrics/` → daily_activity.csv equivalent
   - `Daily heart rate samples/` → heart_rate.csv equivalent
   - `Daily sleep segments/` → sleep.csv equivalent

6. **Convert to HealthPilot format**:
   Use the provided conversion script (future feature) or manually map columns.

## Sample Data Generation

If you don't have real data yet, generate realistic synthetic data:

```bash
uv run python data/generate_sample_data.py
```

This creates 90 days of data with:
- Realistic physiological ranges
- Weekday/weekend patterns
- Circadian rhythms (heart rate)
- Gradual fitness improvement trend
- A few missing days (simulating real gaps)
- 2-3 anomalies (very low/high activity days)

**Generation parameters** (in `generate_sample_data.py`):
- `N_DAYS = 90` - Number of days to generate
- `START_DATE = "2025-11-01"` - First date
- `SEED = 42` - Random seed for reproducibility

## User Profile

**File**: `data/user_profile.json`

Stores user preferences read by agents.

**Schema**:
```json
{
    "name": "Alex",
    "age": 28,
    "sex": "male",
    "height_cm": 178,
    "weight_kg": 75,
    "dietary_preferences": "omnivore",
    "allergies": [],
    "dietary_restrictions": [],
    "fitness_level": "intermediate",
    "fitness_goals": ["improve cardiovascular fitness"],
    "daily_calorie_target": 2400,
    "macro_targets": {
        "protein_pct": 30,
        "carbs_pct": 45,
        "fat_pct": 25
    },
    "available_equipment": ["dumbbells", "resistance bands"],
    "preferred_exercise_times": ["morning", "evening"],
    "sleep_goal_hours": 8.0,
    "daily_step_goal": 10000,
    "timezone": "Asia/Jerusalem"
}
```

**Used by**:
- Nutrition agent: dietary_preferences, allergies, calorie_target
- Exercise agent: fitness_level, goals, equipment
- Wellbeing agent: sleep_goal_hours

**Updating**:
- Edit JSON file directly
- Or use the `update_user_profile` tool via chat

## Data Privacy

**Local-first approach**:
- All health data stored locally (no cloud upload)
- CSV files never leave your machine
- Vector store (ChromaDB) is local
- API calls (Claude, OpenAI) only send query text, not raw data

**What gets sent to APIs**:
- **Claude**: User messages, tool call results (aggregated stats, not raw CSVs)
- **OpenAI**: Document text for embedding (USDA/PubMed, not your health data)
- **LangSmith**: Trace metadata (agent names, timestamps), not sensitive data

**To ensure privacy**:
- Keep `.env` file secure (contains API keys)
- Don't commit `.env` to version control
- Don't share ChromaDB directory publicly

## Data Quality

### Missing Data
The analytics pipeline handles missing data gracefully:
- Gaps in daily activity → no interpolation, just skip those days in calculations
- Missing sleep nights → excluded from averages
- Heart rate gaps → rolling averages use available data points

### Outliers
Detected via Z-score method:
- Values >2 standard deviations from rolling mean are flagged
- Dashboard shows anomaly markers
- Insights engine comments on anomalies

### Data Validation
On load, the pipeline checks:
- Expected columns present (`data_pipeline.py`)
- Date formats parseable
- Value ranges plausible (e.g., HR 40-200 bpm)

## Extending Data Sources

### Adding New Metrics

To add a new data type (e.g., `blood_pressure.csv`):

1. **Create CSV file** in `data/sample/`:
   ```csv
   date,systolic,diastolic
   2025-11-01,120,80
   ```

2. **Add to `data_pipeline.py`**:
   ```python
   EXPECTED_COLUMNS["blood_pressure"] = ["date", "systolic", "diastolic"]

   def load_blood_pressure(self) -> pd.DataFrame:
       df = self._load_csv("blood_pressure")
       df["date"] = pd.to_datetime(df["date"])
       return df
   ```

3. **Create metrics** in `health_metrics.py`:
   ```python
   @dataclass
   class BloodPressureSummary:
       avg_systolic: float
       avg_diastolic: float

   def compute_bp_summary(self, df: pd.DataFrame) -> BloodPressureSummary:
       return BloodPressureSummary(...)
   ```

4. **Add visualization** in `visualizations.py`:
   ```python
   def plot_blood_pressure(df: pd.DataFrame) -> go.Figure:
       ...
   ```

5. **Add to Dashboard** (`pages/2_Dashboard.py`):
   ```python
   bp_df = loader.load_blood_pressure()
   st.plotly_chart(plot_blood_pressure(bp_df))
   ```

### Integrating Other Wearables

**Fitbit**: Export via https://www.fitbit.com/settings/data/export

**Apple Health**: Export via Health app → Profile → Export All Health Data

**Garmin Connect**: Export via https://www.garmin.com/account/datamanagement/exportdata/

**Conversion needed**: Each platform has different column names. Create a mapping script:
```python
def convert_fitbit_to_healthpilot(fitbit_csv: str) -> pd.DataFrame:
    df = pd.read_csv(fitbit_csv)
    return pd.DataFrame({
        "date": df["Date"],
        "steps": df["Steps"],
        "calories_burned": df["Calories Burned"],
        # ... map other columns
    })
```

## Data Retention

- **Sample data**: Included in repo for demo purposes
- **Your data**: Not tracked by git (add to .gitignore if using real data)
- **ChromaDB**: Persists in `data/chroma_db/` until manually deleted
- **Streamlit cache**: Clears on browser refresh

## Frequently Asked Questions

**Q: Can I use data from multiple sources?**
A: Yes, as long as you convert to the expected CSV format. Merge CSVs from different periods.

**Q: How much data do I need?**
A: Minimum 7 days for meaningful trends. 30+ days recommended for statistical analysis.

**Q: What if I don't have heart rate data?**
A: The dashboard adapts. HR-specific charts won't show, but activity and sleep analysis still works.

**Q: Can I delete specific days?**
A: Yes, just remove rows from the CSV. The pipeline skips missing dates.

**Q: Does the app modify my data files?**
A: No. All analysis is read-only. Original CSVs remain unchanged.

# Xert Online Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![version](https://img.shields.io/badge/version-1.0.2-blue.svg)](https://github.com/salihinsaealal/xert-homeassistant)

Integrate your [Xert Online](https://www.xertonline.com/) fitness and training data directly into [Home Assistant](https://www.home-assistant.io/).

## Features
- OAuth2 authentication with Xert Online
- 5 sensor entities:
  - Fitness Status
  - Training Progress
  - Workout Manager
  - Recent Activity
  - Token Status
- Automatic token refresh
- Data updates every 15 minutes
- Dashboard-ready entities

## Installation

### HACS (Recommended)
1. Add this repository to HACS as a custom integration.
2. Search for "Xert Online" in HACS > Integrations.
3. Install and restart Home Assistant.

### Manual
1. Copy the `xert` folder to your `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration
1. Go to **Settings > Devices & Services** in Home Assistant.
2. Click **Add Integration** and search for **Xert Online**.
3. Enter your Xert Online username and password.
4. Complete the setup.

## Entities and Attributes
| Entity | State | Key Attributes |
|--------|-------|---------------|
| `sensor.[username]_fitness_status` | Training Load/Status | `training_status`, `threshold_power`, `high_intensity_energy`, `peak_power`, `form`, `signature_date` |
| `sensor.[username]_training_progress` | Daily XSS | `weekly_xss`, `monthly_xss`, `focus`, `progression_status`, `last_activity_date`, `target_xss`, `workout_difficulty` |
| `sensor.[username]_workout_manager` | Number of Workouts | `total_workouts`, `workout_names`, `recommended_workout`, `workout_description`, `last_modified` |
| `sensor.[username]_recent_activity` | Activity Name | `activity_date`, `activity_duration`, `activity_xss`, `activity_type`, `power_data_available`, `breakthrough_achieved` |
| `sensor.[username]_token_status` | Token Validity | `token_expiry`, `refresh_token_available`, `last_successful_call` |

> **Note:** Entity IDs are now always `sensor.{username}_fitness_status`, etc. The `xert_` prefix is no longer used anywhere.

## Example Dashboard YAML (Standard Lovelace)

> This example uses only standard Home Assistant cards for maximum compatibility. Replace `[username]` with your Xert username.

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      ## 🚴‍♂️ Xert Training Dashboard
  - type: horizontal-stack
    cards:
      - type: entity
        entity: sensor.[username]_fitness_status
        name: Training Status
        icon: mdi:account-heart
      - type: entity
        entity: sensor.[username]_fitness_status
        name: XSS Target
        icon: mdi:chart-bell-curve
        attribute: target_xss
  - type: horizontal-stack
    cards:
      - type: entity
        entity: sensor.[username]_workout_manager
        name: Recommended Workout
        icon: mdi:sword-cross
        attribute: recommended_workout
  - type: markdown
    content: >
      ### 💪 Training Recommendation

      Your Training Status is **{{ states('sensor.[username]_fitness_status') }}**
      and you should consider a **{{
      state_attr('sensor.[username]_workout_manager', 'recommended_workout') }}**
      workout generating about **{{ state_attr('sensor.[username]_fitness_status',
      'target_xss')['total'] | round(2)}} XSS** 

      <br> **Description:** {{ state_attr('sensor.[username]_workout_manager',
      'workout_description') }}

      <br>

      **Last Workout Date:** {{ (state_attr('sensor.[username]_recent_activity',
      'start_date') | as_datetime + timedelta(hours=8)).timestamp() |
      timestamp_custom('%A, %d %B %Y, %I:%M %p') }}
    conditions:
      - entity: sensor.[username]_fitness_status
        state: unknown
    card:
      type: markdown
      content: >
        <ha-icon icon="mdi:alert-circle-outline" style="color:
        #2196f3;"></ha-icon> **No data?** Go to Node-RED and click "**Manual
        Test**" or "**Force Update**"
```

### How to Use
1. Copy the YAML above.
2. In Home Assistant, go to your dashboard, click the three dots (⋮) → Edit Dashboard → Add Card → Manual.
3. Paste the YAML and save.

## Troubleshooting
- Check `sensor.[username]_token_status` for API/auth issues.
- Enable debug logging in `configuration.yaml`:
  ```yaml
  logger:
    default: warning
    logs:
      custom_components.xert: debug
  ```
- For Xert account issues, contact [Xert support](mailto:support@xertonline.com).

## Privacy
- OAuth tokens are stored locally and refreshed automatically.
- No training data is stored beyond current values.

## Version History
- **1.0.2** - Add recommended workout and details to workout_manager sensor; entity IDs now use username prefix
- **1.0.1** - Bugfixes, entity_id prefix, improved docs, and dashboard example
- **1.0.0** - Initial release with basic sensor entities

## License
MIT 
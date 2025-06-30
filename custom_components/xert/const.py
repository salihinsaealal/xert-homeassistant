"""Constants for the Xert integration."""
from datetime import timedelta

DOMAIN = "xert"

# API Configuration
API_BASE_URL = "https://www.xertonline.com/oauth"
TOKEN_URL = "https://www.xertonline.com/oauth/token"

# API Endpoints
ENDPOINT_TRAINING_INFO = "training_info"
ENDPOINT_WORKOUTS = "workouts"
ENDPOINT_ACTIVITY_LIST = "activity"
ENDPOINT_WORKOUT_DETAIL = "workout"
ENDPOINT_ACTIVITY_DETAIL = "activity"

# OAuth Configuration
OAUTH_CLIENT_ID = "xert_public"
OAUTH_CLIENT_SECRET = "xert_public"

# Configuration Keys
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_EXPIRES_IN = "expires_in"

# Update intervals
UPDATE_INTERVAL = timedelta(minutes=15)

# Entity names
SENSOR_FITNESS_STATUS = "fitness_status"
SENSOR_TRAINING_PROGRESS = "training_progress"
SENSOR_WORKOUT_MANAGER = "workout_manager"
SENSOR_RECENT_ACTIVITY = "recent_activity"
SENSOR_TOKEN_STATUS = "token_status"
SENSOR_WOTD = "wotd"

# Default values
DEFAULT_NAME = "Xert Online" 
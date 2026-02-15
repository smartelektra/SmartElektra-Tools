DOMAIN = "smartelektra_tools"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_TIMEOUT = "timeout"

DEFAULT_PORT = 502
DEFAULT_TIMEOUT = 5.0

# Modbus register map (Arduino firmware)
# HR0 (holding register 0) = new slave id (1..247)
DEFAULT_HR_NEW_SLAVE = 0

# Optional configuration registers (defaults can be changed via entities)
# HR1 = button mode (0=mono, 1=bi)
DEFAULT_HR_BUTTON_MODE = 1
# HR2 = output polarity/level (0=LOW, 1=HIGH)
DEFAULT_HR_OUTPUT_LEVEL = 2

# Optional coil for quick test (toggle output)
DEFAULT_COIL_TEST_OUTPUT = 0

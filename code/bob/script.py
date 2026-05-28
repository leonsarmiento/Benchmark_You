import sys
import os

# Add the parent directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the shared functions module
from shared import functions

# Call the hello function from the shared module
functions.hello()
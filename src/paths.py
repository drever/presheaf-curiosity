"""Central place for data locations (override with environment variables)."""
import os, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get('DATA_DIR', os.path.join(ROOT, 'data'))
ISCAS = os.path.join(DATA, 'hdl-benchmarks', 'iscas85', 'bench') + os.sep
EPFL = os.path.join(DATA, 'benchmarks', 'arithmetic') + os.sep
STREETS = os.path.join(DATA, 'spain-cities-geojson', 'cities') + os.sep
GEN = os.environ.get('GEN_DIR', os.path.join(DATA, 'generated')) + os.sep     # generated array multipliers (src/genmul.py)
TMP = tempfile.gettempdir()

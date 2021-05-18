import platform

from System.Logger import Console
from System.Reader import Reader

is_windows = platform.system() == 'Windows'
nul = f' > {"nul" if is_windows else "/dev/null"} 2>&1'

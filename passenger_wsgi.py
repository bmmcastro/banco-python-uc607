#arranque da aplicação no cPanel (Passenger)
import sys
import os

#garantir que a pasta da aplicação está no caminho do Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from servidor import app as application

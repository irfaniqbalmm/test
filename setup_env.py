import sys
import os

#Adding project root to sys.path to make individual python files easily executable
root_dir = os.path.abspath(os.path.dirname( __file__ ))
if root_dir not in sys.path :
    sys.path.append(root_dir)

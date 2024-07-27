
import sys, os
current_dir = os.getcwd()
src_path = os.path.join(current_dir, '..', 'src')
sys.path.append(os.path.abspath(src_path))
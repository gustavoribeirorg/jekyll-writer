import sys
import os

# Ensure current dir is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jekyll_writer.config import ConfigManager
from jekyll_writer.ui import JekyllWriterApp

def main():
    config = ConfigManager()
    app = JekyllWriterApp(config_manager=config)
    app.mainloop()

if __name__ == "__main__":
    main()

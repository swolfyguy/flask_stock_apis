# -*- coding: utf-8 -*-
from app import create_webapp
import os
app = None

if not app:
    app = create_webapp()

if __name__ == "__main__":
    # Start application
    app.run()

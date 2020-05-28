"""
Initializes pdf builder and start the server
"""
#from plugin.google_doc_plugin.external import GoogleDocsSheetsPlugin
from .internal import PDFBuilder
from plugin.odk_plugin.external import ODKSheetsPlugin

if __name__ == "__main__":
    CONFIG = {"retries": 20, "max_concurrency": 1}
    APP = PDFBuilder(plugin=ODKSheetsPlugin(), config=CONFIG)
    APP.start()

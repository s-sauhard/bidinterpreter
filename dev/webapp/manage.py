#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import project.apps.bidinterpreter.pdfextract
import pathlib


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

    #bidinterpreter.pdfextract.createsearchablepdf()
    #bidinterpreter.pdfextract.pdfdispatch()
    #bidinterpreter.pdfextract.imagetotext()
    #bidinterpreter.pdfextract.regexprocessing(pathlib.Path(r'C:\Users\Brett\Desktop\test\Wood Partners 03.13.20 from_image.pdf'), pathlib.Path(r'C:\Users\Brett\Desktop\test\Wood Partners 03.13.20.jpg'))
    #bidinterpreter.pdfextract.highlightpdfimage(highlights, pathlib.Path(r'C:\Users\Brett\Desktop\test\Wood Partners 03.13.20 from_image.pdf'), pathlib.Path(r'C:\Users\Brett\Desktop\test\Wood Partners 03.13.20.jpg'))
    #bidinterpreter.pdfextract.regexdict()
    #bidinterpreter.pdfextract.test()

if __name__ == '__main__':
    main()

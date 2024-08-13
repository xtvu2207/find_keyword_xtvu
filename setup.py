from setuptools import setup, find_packages

setup(
    name="find_keyword_xtvu",
    version="5.5",
    author="Xuan Tung VU",
    description="A package to find keywords in .pdf, .docx, .odt, and .rtf files, with support for multiple languages.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3.10',
    packages=find_packages(), 
    install_requires=[
        'pdfplumber',
        'pytesseract',
        'pandas',
        'Pillow',
        'spacy',
        'openpyxl',
        'pdf2image',
        'reportlab',
        'pypandoc', 
        'python-docx'
    ],
    include_package_data=True, 
    zip_safe=False, 
)

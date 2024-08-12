from setuptools import setup, find_packages

setup(
    name="find_keyword_xtvu",
    version="5.2",
    author="Xuan Tung VU",
    description="A package to find keywords in .pdf, .docx, .odt, and .rtf files",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3.10',
    packages=find_packages(),  # Trouve automatiquement tous les sous-modules dans find_keyword_xtvu
    install_requires=[
        'pdfplumber',
        'pytesseract',
        'pandas',
        'Pillow',
        'spacy',
        'openpyxl',
        'pdf2image',
        'reportlab'
    ],
    include_package_data=True,  # Inclure automatiquement les fichiers spécifiés dans MANIFEST.in
    zip_safe=False,  # Assure une installation non zip
)

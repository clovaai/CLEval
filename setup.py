import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cleval",
    version="0.1.1",
    author="dong.hyun",
    author_email="dong.hyun@navercorp.com",
    description="cleval",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://oss.navercorp.com/CLOVA-AI-OCR/cleval",
    packages=setuptools.find_packages(),
    install_requires=[
        "bottle",
        "requests",
        "Pillow",
        "Polygon3",
        "Shapely",
        "tqdm",
        "pprofile",
        "numba>=0.58.0",
        "six",
        "torchmetrics>=1.2.0",
        "numpy",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "cleval = cleval.main:main",
        ],
    },
    python_requires=">=3.7",
)

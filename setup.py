from setuptools import find_packages, setup

setup(
    name="telegram_client",
    packages=find_packages(),
    version="0.0.1",
    description="Parse telegram channel information",
    author="Bogdan Efimenko",
    install_requires=[
        "Telethon~=1.23.0",
        "tqdm~=4.62.3",
        "numpy~=1.21.3",
        "pandas~=1.3.4",
        "tqdm~=4.62.3",
    ],
    license="MIT",
)
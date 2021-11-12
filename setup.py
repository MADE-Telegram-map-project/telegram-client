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
        "omegaconf~=2.1",
        "python-statemachine~=0.8.0",
    ],
    license="MIT",
)
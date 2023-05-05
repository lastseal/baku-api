from setuptools import setup

setup(
    name="baku-collections",
    version="1.0.0",
    description="Módulo que permite realizar consultas a colecciones",
    author="Rodrigo Arriaza",
    author_email="hello@lastseal.com",
    url="https://www.lastseal.com",
    packages=['baku'],
    install_requires=[ 
        i.strip() for i in open("requirements.txt").readlines() 
    ]
)

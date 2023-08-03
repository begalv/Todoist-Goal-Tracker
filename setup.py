from setuptools import setup, find_packages

setup(
    name="Todoist-Goal-Tracker",
    author="Bernardo Coutinho Galvão dos Santos",
    author_email="bgalvaods@gmail.com",
    license="MIT",
    version = "0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["streamlit", "pandas", "plotly"]
)

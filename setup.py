import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sanic_extras-moham",
    version="0.5.0",
    author="Seyed Moham mousavi",
    author_email="s.mohammad.msv@gmail.com",
    description="Extra features for Sanic web framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/moham/sanic-extras",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

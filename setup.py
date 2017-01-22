#! /usr/bin/env python
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import os

from setuptools import setup


def read(fpath):
    with open(os.path.join(os.path.dirname(__file__), fpath)) as stream:
        return stream.read()


def get_requirements():
    name = "base"
    path = os.path.join("requirements", "{}.txt".format(name))
    data = read(path)
    lines = []
    for line in data.splitlines():
        line = line.strip()
        if not line or line.startswith("-"):
            continue
        lines.append(line)
    return lines


setup(
    name="libmorse",
    version="0.1.0",
    description="Convert timed signals into alphabet.",
    long_description=read("README.md"),
    url="https://github.com/cmin764/libmorse",
    license="MIT",
    author="Cosmin Poieana",
    author_email="cmin764@gmail.com",
    packages=["libmorse"],
    scripts=["bin/morseus"],
    package_data={"libmorse": ["etc/libmorse/*", "res/*"]},
    include_package_data=True,
    install_requires=get_requirements(),
    test_suite="tests",
)

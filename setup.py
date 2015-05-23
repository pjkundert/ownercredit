from setuptools import setup
import os, sys

here = os.path.abspath( os.path.dirname( __file__ ))

__version__			= None
__version_info__		= None
exec( open( 'version.py', 'r' ).read() )


install_requires		= open( os.path.join( here, "requirements.txt" )).readlines()

setup(
    name			= "ownercredit",
    version			= __version__,
    tests_require		= [ "pytest" ],
    install_requires		= install_requires,
    packages			= [ 
        "ownercredit",
        "ownercredit/trading",
    ],
    package_dir			= {
        "ownercredit":		".", 
        "ownercredit/trading":	"./trading",
    },
    include_package_data	= True,
    author			= "Perry Kundert",
    author_email		= "perry@hardconsulting.com",
    description			= "Ownercredit implements some concepts for a wealth-backed currency system",
    long_description		= """\
Purpose: to implement currencies where every unit is backed by wealth, and where
every holder of wealth may create credit.  The system implements a limit, K, on
the amount of credit created relative to pledged wealth, to control inflation
and deflation, automatically ensuring that the value of each unit of credit
remains roughly constant in terms of some "reference" basket of wealth.
""",
    license			= "Dual License; GPLv3 and Proprietary",
    keywords			= "ownercredit wealthcoin wealth-backed currency",
    url				= "https://github.com/pjkundert/ownercredit",
    classifiers			= [
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Environment :: Console",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
        "Topic :: Text Processing :: Filters"
    ],
)

from setuptools import setup

setup_config = {
    'description': 'OSC server handling a stream of data in OSC format.',
    'packages': ['oscserver'],
    'install_requires': ['python-osc'],
    'name': 'osc-server'
}

def main():
    setup(**setup_config)

if __name__ == '__main__':
    main()

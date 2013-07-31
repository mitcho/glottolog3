from getpass import getpass

import requests
from path import path
from fabric.api import task, hosts, local, sudo, cd
from fabric.contrib.console import confirm
from alembic.script import ScriptDirectory
from alembic.config import Config
from alembic.util import rev_id
from clld.deploy import config, util


APP = config.APPS['glottolog3']


@hosts('robert@vmext24-203.gwdg.de')
@task
def deploy_test():
    util.deploy(APP, 'test')


@hosts('forkel@cldbstest.eva.mpg.de')
@task
def deploy():
    util.deploy(APP, 'production')


@hosts('robert@vmext24-203.gwdg.de')
@task
def stop_test():
    util.supervisor(APP, 'pause')


@hosts('robert@vmext24-203.gwdg.de')
@task
def start_test():
    util.supervisor(APP, 'run')


@hosts('robert@vmext24-203.gwdg.de')
@task
def run_script(script_name, *args):
    sudo(
        '%s %s %s#%s %s' % (
            APP.bin('python'),
            APP.src.joinpath(APP.name, 'scripts', '%s.py' % script_name),
            APP.config,
            APP.name,
            ' '.join('%s' % arg for arg in args),
        ),
        user=APP.name)


@hosts('robert@vmext24-203.gwdg.de')
@task
def create_exports():
    # run the script to create the exports from the database as glottolog2 user
    run_script('update_exports', APP.home)

    # copy the files from temp directory to the export dir as root
    ls = sudo('ls %s/glottolog-*.gz' % APP.home)
    for p in ls.split():
        sudo('cp %s %s' % (
            p, APP.src.joinpath(APP.name, 'static', 'export', path(p).basename())))


@task
def alembic_revision(log_url):
    """local task to merge changes from glottologcurator available to the production
    site via an alembic migration script.

    pulls the changelog from glottologcurator and create a new alembic revision with it.
    """
    user = raw_input('HTTP Basic auth user for glottologcurator: ')
    password = getpass('HTTP Basic auth password for glottologcurator: ')
    kw = {}
    if user and password:
        kw['auth'] = (user, password)
    changes = requests.get(log_url, **kw).json()

    config = Config()
    config.set_main_option("script_location", path('.').joinpath('migrations'))
    scriptdir = ScriptDirectory.from_config(config)
    script = scriptdir.generate_revision(
        rev_id(), "Glottolog Curator", refresh=True,
        upgrades="""\
# from glottologcurator
    conn = op.get_bind()
    for sql, params in [
%s
    ]:
        conn.execute(sql, params)
""" % '\n'.join(u'    ("""{0}""", {1}),'.format(*event) for event in changes['events']))

    print('new alembic migration script created:')
    print(script.path)

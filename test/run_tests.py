#!/usr/bin/env python

import os
import sys
from subprocess import Popen, call
from tempfile import TemporaryFile

from run_unit_tests import run_unit_tests

ROOT = os.path.dirname(__file__)
TESTDATADIR = os.path.join(ROOT, 'acceptance')
RESOURCEDIR = os.path.join(ROOT, 'resources')
SRCDIR = os.path.join(ROOT, '..', 'src')
UTESTDIR = os.path.join(ROOT, 'unit')
RESULTDIR = os.path.join(ROOT, 'results')
HTPPSERVER = os.path.join(RESOURCEDIR, 'testserver', 'testserver.py')
ROBOT_ARGS = [
'--doc', 'SeleniumSPacceptanceSPtestsSPwithSP%(browser)s',
'--outputdir', '%(outdir)s',
'--variable', 'browser:%(browser)s',
'--escape', 'space:SP',
'--report', 'none',
'--log', 'none',
'--suite', 'Acceptance.Open And Close',
'--suite', 'Acceptance.Multiple Browsers',
'--suite', 'Acceptance.Windows',
'--suite', 'Acceptance.Keywords.Checkbox And Radio Buttons',
'--suite', 'Acceptance.Keywords.Click Element',
'--suite', 'Acceptance.Keywords.Content Assertions',
'--suite', 'Acceptance.Keywords.Cookies',
'--suite', 'Acceptance.Keywords.Element Should Be Enabled And Disabled',
'--suite', 'Acceptance.Keywords.Elements',
'--suite', 'Acceptance.Keywords.Forms And Buttons',
'--loglevel', 'DEBUG',
'--pythonpath', '%(pythonpath)s',
]
REBOT_ARGS = [
'--outputdir', '%(outdir)s',
'--name', '%(browser)sSPAcceptanceSPTests',
'--escape', 'space:SP',
'--critical', 'regression',
'--noncritical', 'inprogress',
]
ARG_VALUES = {'outdir': RESULTDIR, 'pythonpath': SRCDIR}


def acceptance_tests(interpreter, browser, args):
    ARG_VALUES['browser'] = browser.replace('*', '')
    start_http_server()
    runner = {'python': 'pybot', 'jython': 'jybot', 'ipy': 'ipybot'}[interpreter]
    if os.sep == '\\':
        runner += '.bat'
    execute_tests(runner)
    stop_http_server()
    return process_output()

def start_http_server():
    server_output = TemporaryFile()
    Popen(['python', HTPPSERVER ,'start'],
          stdout=server_output, stderr=server_output)

def execute_tests(runner):
    if not os.path.exists(RESULTDIR):
        os.mkdir(RESULTDIR)
    command = [runner] + [arg % ARG_VALUES for arg in ROBOT_ARGS] + args + [TESTDATADIR]
    print 'Starting test execution with command:\n' + ' '.join(command)
    syslog = os.path.join(RESULTDIR, 'syslog.txt')
    call(command, shell=os.sep=='\\', env=dict(os.environ, ROBOT_SYSLOG_FILE=syslog))

def stop_http_server():
    call(['python', HTPPSERVER, 'stop'])

def process_output():
    print
    call(['python', os.path.join(RESOURCEDIR, 'statuschecker.py'),
         os.path.join(RESULTDIR, 'output.xml')])
    rebot = 'rebot' if os.sep == '/' else 'rebot.bat'
    rebot_cmd = [rebot] + [ arg % ARG_VALUES for arg in REBOT_ARGS ] + \
                [os.path.join(ARG_VALUES['outdir'], 'output.xml') ]
    rc = call(rebot_cmd, env=os.environ)
    if rc == 0:
        print 'All critical tests passed'
    else:
        print '%d critical test%s failed' % (rc, 's' if rc != 1 else '')
    return rc

def _exit(rc):
    sys.exit(rc)

def _help():
    print 'Usage:  python run_tests.py python|jython browser [options]'
    print
    print 'See README.txt for details.'
    return 255

def _run_unit_tests():
    print 'Running unit tests'
    failures = run_unit_tests()
    if failures != 0:
        print '\n%d unit tests failed - not running acceptance tests!' % failures
    else:
        print 'All unit tests passed'
    return failures


if __name__ ==  '__main__':
    if not len(sys.argv) > 2:
        _exit(_help())
    unit_failures = _run_unit_tests()
    if unit_failures:
        _exit(unit_failures)
    interpreter = sys.argv[1]
    browser = sys.argv[2].lower()
    args = sys.argv[3:]
    if browser != 'unit':
        _exit(acceptance_tests(interpreter, browser, args))

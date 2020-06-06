import sys
import select
import logging
from pathlib import Path

from toolz.curried import (
    curry, merge,
)
import paramiko

from larc.common import Null

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

@curry
def getoutput(hostname, command, echo=False, sudo=False, **ssh_kw):
    '''subprocess.getoutput equivalent over SSH

    Relies on public-key authentication currently

    Args:
      command (str): command to execute over SSH
    
      echo (bool=False): echo command progress to stdout
    
      **ssh_kw: keyword args for paramiko.SSHClient

      port=22, username=None, password=None, pkey=None,
      key_filename=None, timeout=None, allow_agent=True,
      look_for_keys=True, compress=False, sock=None, gss_auth=False,
      gss_kex=False, gss_deleg_creds=True, gss_host=None,
      banner_timeout=None, auth_timeout=None, gss_trust_dns=True,
      passphrase=None, disabled_algorithms=None
    
      http://docs.paramiko.org/en/2.6/api/client.html#paramiko.client.SSHClient.connect

    '''

    if sudo and 'password' not in ssh_kw:
        raise AttributeError(
            'Must have password set in kw args if elevating to SUDO'
        )

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # if (not ({'pkey', 'key_filename'} & set(ssh_kw)) and
        #     not ('password' in ssh_kw)):
        #     key_path = Path('~/.ssh/id_rsa').expanduser()
        #     log.info(f'[getoutput] adding local key: {key_path}')
        #     ssh_kw = merge(
        #         ssh_kw, {'key_filename': str(key_path)}
        #     )

        client.connect(hostname, **ssh_kw)

    except paramiko.AuthenticationException:
        log.error(f'Authentication failure connecting to {hostname}')
        return Null

    try:
        def shorten(s):
            if len(s) > 500:
                return s[:250] + ' [...] ' + s[-250:]
            return s

        exec_kw = {}
        if sudo:
            log.info(f'[ssh.getoutput] elevating to SUDO')
            command = 'sudo -S ' + command
            # exec_kw['get_pty'] = True
            
        log.info(f'[ssh.getoutput] command: {shorten(command)}')
        stdin, stdout, stderr = client.exec_command(command, **exec_kw)

        if sudo:
            stdin.write(f"{ssh_kw['password']}\n")
            stdin.flush()

        output, more = b'', b''
        # Wait for the command to terminate
        while not stdout.channel.exit_status_ready():
            # Only print data if there is data to read in the channel
            if stdout.channel.recv_ready():
                rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
                if len(rl) > 0:
                    # Print data from stdout
                    more = stdout.channel.recv(1024)
                    if echo:
                        print(more.decode(), end='', file=sys.stderr)
                    output += more
        if echo and more:
            print(more.decode(), file=sys.stderr)
        more = stdout.channel.recv(2**20)
        output += more

    except KeyboardInterrupt:
        log.error('KeyboardInterrupt during SSH command')

    finally:
        client.close()

    return output.decode()

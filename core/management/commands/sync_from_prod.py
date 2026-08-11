import os
import subprocess
import tempfile
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Sync the local SQLite database and media files from the production server'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            default='169.239.182.221',
            help='Production server IP or hostname',
        )
        parser.add_argument(
            '--user',
            default='carbonplanner',
            help='SSH user for production server',
        )
        parser.add_argument(
            '--ssh-key',
            default=None,
            help='Path to SSH identity file (e.g., ~/.ssh/id_rsa). If not set, uses password auth.',
        )
        parser.add_argument(
            '--ssh-port',
            type=int,
            default=22,
            help='SSH port (default: 22)',
        )
        parser.add_argument(
            '--remote-project',
            default='/home/carbonplanner/apps/river',
            help='Path to the Django project on the production server',
        )
        parser.add_argument(
            '--remote-venv',
            default='/home/carbonplanner/apps/river/venv/bin/activate',
            help='Path to the virtualenv activate script on production',
        )
        parser.add_argument(
            '--remote-media',
            default='/home/carbonplanner/apps/river/media',
            help='Path to the media directory on production',
        )
        parser.add_argument(
            '--db-only',
            action='store_true',
            help='Only sync the database, skip media files',
        )
        parser.add_argument(
            '--media-only',
            action='store_true',
            help='Only sync media files, skip the database',
        )
        parser.add_argument(
            '--no-load',
            action='store_true',
            help='Download the dump but do not load it into the local database',
        )
        parser.add_argument(
            '--keep-dump',
            action='store_true',
            help='Keep the downloaded fixture file after loading (saved to project root)',
        )

    def _ssh_flags(self, options):
        """Build SSH option flags."""
        flags = ['-A', '-o', 'ConnectTimeout=10']
        if options.get('ssh_key'):
            flags.extend(['-i', os.path.expanduser(options['ssh_key'])])
        else:
            flags.extend(['-o', 'PreferredAuthentications=password'])
        if options.get('ssh_port') and options['ssh_port'] != 22:
            flags.extend(['-p', str(options['ssh_port'])])
        return flags

    def _ssh_target(self, options):
        return f'{options["user"]}@{options["host"]}'

    def _run_ssh(self, options, remote_cmd, *, capture=True, check=True):
        """Run a command over SSH. When capture=False, terminal is inherited
        for interactive password prompts."""
        ssh_cmd = ['ssh'] + self._ssh_flags(options) + [self._ssh_target(options), remote_cmd]

        if capture:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True)
            if check and result.returncode != 0:
                raise CommandError(f'SSH command failed:\n{result.stderr}')
            return result
        else:
            # Inherit terminal for password prompts
            return subprocess.run(ssh_cmd, check=check)

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            f'Connecting to {self._ssh_target(options)}...'
        ))
        if not options.get('ssh_key'):
            self.stdout.write('  Using password authentication. You will be prompted.')

        # Test SSH connectivity
        try:
            self._run_ssh(options, 'echo ok', capture=False)
        except subprocess.CalledProcessError:
            raise CommandError(
                f'SSH connection to {self._ssh_target(options)} failed.\n\n'
                'Troubleshooting:\n'
                '  1. Test manually: ssh {0}\n'
                '  2. Use --ssh-key if you have key-based auth:\n'
                '     python manage.py sync_from_prod --ssh-key ~/.ssh/id_rsa\n'
                '  3. Verify host and user are correct\n'
                '  4. Check that your IP is allowed through the firewall'.format(
                    self._ssh_target(options)
                )
            )

        # ── 1. Sync Database ──
        if not options['media_only']:
            self._sync_database(options)

        # ── 2. Sync Media ──
        if not options['db_only']:
            self._sync_media(options)

        self.stdout.write(self.style.SUCCESS('\nDone!'))

    # ═══════════════════════════════════════════════════════════════
    # Database Sync
    # ═══════════════════════════════════════════════════════════════

    def _sync_database(self, options):
        target = self._ssh_target(options)
        remote_venv = options['remote_venv']
        remote_project = options['remote_project']

        self.stdout.write(self.style.WARNING('\n--- Syncing Database ---'))

        # Step 1: Dump data on production
        remote_dump_path = '/tmp/river_prod_dump.json'
        exclude_models = [
            'contenttypes.ContentType',
            'auth.Permission',
            'sessions.Session',
            'admin.LogEntry',
        ]
        exclude_args = ' '.join(f'--exclude {m}' for m in exclude_models)

        dump_remote_cmd = (
            f'source {remote_venv} && '
            f'cd {remote_project} && '
            f'python manage.py dumpdata --indent 2 {exclude_args} '
            f'--natural-foreign --natural-primary '
            f'> {remote_dump_path}'
        )

        self.stdout.write('  Dumping production database...')
        self._run_ssh(options, dump_remote_cmd, capture=False)
        self.stdout.write('  Dump complete.')

        # Step 2: Download the fixture via SCP
        local_temp = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        local_temp.close()

        scp_flags = self._ssh_flags(options)
        if '-p' in scp_flags:
            idx = scp_flags.index('-p')
            scp_flags[idx] = '-P'  # scp uses -P for port

        scp_cmd = ['scp'] + scp_flags + [f'{target}:{remote_dump_path}', local_temp.name]

        self.stdout.write('  Downloading fixture...')
        result = subprocess.run(scp_cmd)
        if result.returncode != 0:
            os.unlink(local_temp.name)
            raise CommandError('SCP download failed.')
        self.stdout.write(f'  Downloaded ({os.path.getsize(local_temp.name):,} bytes)')

        # Clean up remote temp file
        self._run_ssh(options, f'rm {remote_dump_path}', capture=False)

        # Step 3: Load into local database
        if options['no_load']:
            if options['keep_dump']:
                persistent = os.path.join(settings.BASE_DIR, 'river_prod_dump.json')
                os.rename(local_temp.name, persistent)
                self.stdout.write(f'  Fixture kept at {persistent}')
            else:
                self.stdout.write(f'  Fixture at {local_temp.name}. --keep-dump to persist.')
            return

        self.stdout.write('  Loading into local database (flushing existing data)...')

        try:
            call_command('flush', '--noinput')
            call_command('loaddata', local_temp.name)
        except Exception as e:
            raise CommandError(f'loaddata failed: {e}')

        if not options['keep_dump']:
            os.unlink(local_temp.name)
        else:
            persistent_path = os.path.join(settings.BASE_DIR, 'river_prod_dump.json')
            if os.path.exists(persistent_path):
                os.remove(persistent_path)
            os.rename(local_temp.name, persistent_path)
            self.stdout.write(f'  Fixture kept at {persistent_path}')

        self.stdout.write(self.style.SUCCESS('Database sync complete!'))

    # ═══════════════════════════════════════════════════════════════
    # Media Sync
    # ═══════════════════════════════════════════════════════════════

    def _sync_media(self, options):
        target = self._ssh_target(options)
        remote_media = options['remote_media']

        self.stdout.write(self.style.WARNING('\n--- Syncing Media Files ---'))

        local_media = str(settings.MEDIA_ROOT)
        os.makedirs(local_media, exist_ok=True)

        ssh_opts = ' '.join(self._ssh_flags(options))

        synced = False
        try:
            subprocess.run(['rsync', '--version'], capture_output=True, check=True)
            self.stdout.write('  Using rsync...')
            subprocess.run([
                'rsync', '-avz', '--progress',
                '-e', f'ssh {ssh_opts}',
                f'{target}:{remote_media}/', local_media,
            ], check=True)
            self.stdout.write(self.style.SUCCESS('Media sync complete via rsync!'))
            synced = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.stdout.write('  rsync not available, falling back to scp...')

        if not synced:
            try:
                scp_flags = self._ssh_flags(options)
                if '-p' in scp_flags:
                    scp_flags[scp_flags.index('-p')] = '-P'
                self.stdout.write('  Using scp...')
                subprocess.run(
                    ['scp', '-r'] + scp_flags + [f'{target}:{remote_media}/*', local_media],
                    check=True,
                )
                self.stdout.write(self.style.SUCCESS('Media sync complete via scp!'))
            except subprocess.CalledProcessError as e:
                self.stderr.write(self.style.WARNING(f'Media sync skipped (non-fatal): {e}'))

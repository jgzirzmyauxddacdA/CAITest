"""Export existing chats and copyable Definition directly; no conversation recovery."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import uuid
from cai import open_cai_session, character_id
from common import Failure, exclusive_lock
from combined import run_combined
from cleanup import finish, restore

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULTS = {'request_timeout': 120, 'browser_channel': 'chrome'}


async def execute(args, config, state_dir):
    target = character_id(args.target) if args.target else None
    if not target and not args.login and not args.restore:
        raise Failure('CHARACTER_LINK_REQUIRED')
    if (state_dir / 'pending-restore.json').exists() and not args.restore:
        raise Failure('PENDING_RESTORE_USE_RESTORE_COMMAND')
    if args.restore and not (state_dir / 'pending-restore.json').exists():
        print(json.dumps({'status': 'not_needed'}))
        return 0
    combined = not args.login and not args.restore
    if combined and os.environ.get('CHARACTER_AI_TOKEN'):
        raise Failure('REMOVE_CHARACTER_AI_TOKEN_USE_BROWSER_SESSION')
    destination = None
    if combined:
        destination = Path(args.out).resolve() if args.out else SKILL_ROOT / 'output' / target / (
            datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
        if destination.exists():
            raise Failure('OUTPUT_EXISTS')
    # Read-only exports query the target by ID from the signed-in page.
    async with open_cai_session(state_dir, None, config['browser_channel'], config['request_timeout'], args.login_timeout) as cai:
        if args.restore:
            try:
                result, interrupted = await finish(restore(cai, state_dir))
                if interrupted and result['status'] != 'cleanup_failed':
                    result = {**result, 'status': 'cancelled', 'code': 'USER_CANCELLED'}
            except Exception as error:
                result = {'status': 'restore_failed', 'code': error.code if isinstance(error, Failure) else 'RESTORE_FAILED'}
                if isinstance(error, Failure) and error.details:
                    result['error_details'] = error.details
        elif args.login:
            account = await cai.me()
            result = {'status': 'logged_in', 'account_id': account['id'], 'username': account['username']}
        else:
            result = await run_combined(cai, target, destination, config, gold=args.gold)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result['status'] in ('restore_failed', 'cleanup_failed'):
            return 3
        if result['status'] == 'cancelled':
            return 130
        if combined:
            return {'complete': 0, 'partial': 2, 'failed': 1, 'cancelled': 130}.get(result['status'], 1)
        return 0 if result['status'] in ('complete', 'candidate_complete', 'no_definition', 'logged_in', 'verified', 'not_needed') else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', nargs='?')
    parser.add_argument('--out', help='A new output directory; never overwrites an existing run')
    parser.add_argument('--state-dir', default=str(Path.home() / '.cai-definition-runner'))
    parser.add_argument('--login-timeout', type=int, default=600, help='Login wait in seconds, 1-3600; supports email login in a new tab')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--login', action='store_true', help='Open isolated Chrome profile and verify login only')
    mode.add_argument('--restore', action='store_true', help='Restore pending binding and finish this run\'s archival; no new generation')
    parser.add_argument('--export-only', '--direct-only', dest='direct_only', action='store_true',
        help='Compatibility alias: all exports now use copyable-only mode')
    parser.add_argument('--gold', help='Optional known original Definition file for exact byte comparison')
    args = parser.parse_args(argv)
    try:
        if not 1 <= args.login_timeout <= 3600:
            raise Failure('INVALID_LOGIN_TIMEOUT')
        if args.gold and not Path(args.gold).is_file():
            raise Failure('GOLD_FILE_NOT_FOUND')
        config = dict(DEFAULTS)
        state_dir = Path(args.state_dir).resolve()
        state_dir.mkdir(parents=True, exist_ok=True)
        with exclusive_lock(state_dir / 'run.lock'):
            return asyncio.run(execute(args, config, state_dir))
    except KeyboardInterrupt:
        print(json.dumps({'status': 'cancelled', 'code': 'USER_CANCELLED_CHECK_PENDING_RESTORE'}))
        return 130
    except Exception as error:
        result = {'status': 'failed', 'code': error.code if isinstance(error, Failure) else 'STARTUP_FAILED'}
        if isinstance(error, Failure) and error.details:
            result['error_details'] = error.details
        print(json.dumps(result))
        return 3 if result['code'] == 'PENDING_RESTORE_USE_RESTORE_COMMAND' else 1


if __name__ == '__main__':
    sys.exit(main())

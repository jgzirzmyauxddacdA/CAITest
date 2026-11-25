"""Read character data; save Definition only when the API explicitly allows copying."""
from common import Failure, save_json


async def export_character(cai, target, destination, expected_account_id):
    destination.mkdir(parents=True, exist_ok=False)
    account = await cai.me()
    if account['id'] != expected_account_id:
        raise Failure('ACCOUNT_CHANGED')
    character = await cai.info(target)
    if character.get('external_id') != target:
        raise Failure('CHARACTER_RESPONSE_INVALID')
    character = dict(character)
    definition = character.pop('definition', None)
    result = {'schema_version': 1, 'mode': 'copyable_only', 'character_id': target,
        'account_id': account['id'], 'stage': 'character_query',
        'restore': {'status': 'not_needed'}, 'verification': 'not_applicable'}
    if character.get('copyable') is not True:
        result.update(status='skipped_not_copyable', reason='copyable is not true')
    elif isinstance(definition, str) and definition.strip():
        (destination / 'definition.txt').write_bytes(definition.encode('utf-8'))
        result.update(status='complete', verification='api_returned', definition_file='definition.txt')
    elif character.get('has_definition') is False and definition in (None, ''):
        result.update(status='no_definition', verification='api_returned')
    else:
        result.update(status='unavailable', reason='Copying is allowed but the API returned no usable Definition body.')
    # Never persist a disallowed Definition, even if the API included it.
    save_json(destination / 'character-response.json', character)
    save_json(destination / 'run-result.json', result)
    return result

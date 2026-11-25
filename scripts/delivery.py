"""Public delivery contains only the target Persona and verified history JSON."""
import hashlib
import json
import os
import re
import zipfile

from common import Failure, save_json


def normalize_recovered_definition(text, names):
    """Replace known user aliases literally; keep existing placeholders opaque."""
    aliases = sorted({name for name in names if isinstance(name, str) and name.strip()},
        key=lambda name: (-len(name), name))
    counts = {}
    if aliases:
        pattern = re.compile(r'(?P<placeholder>\{\{[^{}]*\}\})|(?<!\w)(?P<name>'
            + '|'.join(re.escape(name) for name in aliases) + r')(?!\w)')

        def replace(match):
            if match.group('placeholder') is not None:
                return match[0]
            name = match.group('name')
            counts[name] = counts.get(name, 0) + 1
            return '{{user}}'

        normalized = pattern.sub(replace, text)
    else:
        normalized = text
    return normalized, {'method': 'regex_known_user_names_v1', 'authenticity': 'unverified',
        'replacement_count': sum(counts.values()),
        'replacements': [{'from': name, 'to': '{{user}}', 'count': count}
            for name, count in counts.items()]}


def safe_name(name):
    value = re.sub(r'[\x00-\x1f<>:"/\\|?*]', '_', name or '').strip(' .')[:80] or 'Character'
    if re.match(r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)', value, re.I):
        value = '_' + value
    return value


def build_persona(target, directory, result, history):
    fields = {key: None for key in ('name', 'title', 'description', 'greeting', 'additional_greetings')}
    sources, presence = {}, {key: False for key in fields}
    path = directory / 'character-response.json'
    if path.is_file():
        character = json.loads(path.read_bytes())
        if character.get('external_id') != target:
            raise Failure('DELIVERY_CHARACTER_MISMATCH')
        fields.update({key: value for key, value in character.items() if key != 'definition'})
        sources = {key: 'character_info_api' for key in character if key != 'definition'}
        presence = {key: key in character for key in fields}
    if not fields.get('name') and history.get('character_name'):
        fields['name'] = history['character_name']
        sources['name'] = 'history_export'
    body, source, status = None, None, 'unavailable'
    filename = result.get('definition_file')
    if filename:
        if filename not in ('definition.txt', 'definition-candidate.txt'):
            raise Failure('UNSAFE_DEFINITION_FILE')
        body = (directory / filename).read_bytes().decode('utf-8')
        source = 'character_info_api' if filename == 'definition.txt' else 'model_reply'
        ended = result.get('status') in ('complete', 'candidate_complete') or result.get('reason') == 'judge_observed_ending_not_exact_verification'
        status = 'complete' if ended else 'partial'
    elif result.get('status') == 'no_definition':
        status, source = 'no_definition', 'character_info_api'
    elif result.get('status') == 'skipped_not_copyable':
        status, source = 'skipped_not_copyable', 'character_info_api'
    fields.update(character_id=target, definition=body, definition_status=status, definition_source=source,
        definition_authenticity=result.get('verification', 'unverified'), field_sources=sources, field_presence=presence)
    if source == 'model_reply':
        # Normalize only the export copy: raw evidence and continuation anchors stay literal.
        normalized, normalization = normalize_recovered_definition(body,
            [result.get('test_persona_name'), result.get('recovery_username')])
        fields.update(definition_normalized=normalized, definition_normalization=normalization)
    return fields


def package_delivery(destination, persona, history, history_data, *, complete):
    if history_data is not None and history.get('character_id') != persona['character_id']:
        raise Failure('DELIVERY_CHARACTER_MISMATCH')
    if persona['definition'] is None and persona['definition_status'] != 'no_definition' and history_data is None:
        return None
    files = {'Persona.json': (json.dumps(persona, ensure_ascii=False, indent=2) + '\n').encode('utf-8')}
    if history_data is not None:
        files[safe_name(history.get('character_name') or persona.get('name')) + '-history.json'] = history_data
    target = destination / 'delivery.zip'
    temporary = target.with_suffix(target.suffix + '.part')
    report_path = target.with_suffix(target.suffix + '.report.json')
    if target.exists() or temporary.exists() or report_path.exists():
        raise Failure('DELIVERY_EXISTS')
    created = False
    try:
        with temporary.open('xb') as stream:
            created = True
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for name, data in files.items():
                    archive.writestr(name, data)
            stream.flush()
            os.fsync(stream.fileno())
        with zipfile.ZipFile(temporary) as archive:
            if archive.namelist() != list(files) or archive.testzip() is not None or any(archive.read(k) != v for k, v in files.items()):
                raise Failure('DELIVERY_VERIFICATION_FAILED')
        report = {'status': 'passed', 'complete': complete, 'character_id': persona['character_id'],
            'history_status': history['status'], 'definition_status': persona['definition_status'],
            'definition_authenticity': persona['definition_authenticity'],
            'files': [{'name': k, 'bytes': len(v), 'sha256': hashlib.sha256(v).hexdigest()} for k, v in files.items()],
            'zip_sha256': hashlib.sha256(temporary.read_bytes()).hexdigest()}
        # Same-filesystem hard link publishes atomically and refuses an existing target.
        os.link(temporary, target)
        save_json(report_path, report)
        return str(target)
    finally:
        if created:
            temporary.unlink(missing_ok=True)

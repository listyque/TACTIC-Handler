"""Desktop Submit dialog reads and metadata-only saves."""
import uuid


def load_submit_context(client, state):
    code = state['change']['code']
    result = client.rpc('read_batch', requests=[
        {'action': 'submit_shelves', 'values': {'change': code}},
        {'action': 'submit_tasks', 'values': {'change': code}}])
    state['submit_review'] = dict(change=code,shelves=result['items'][0], tasks=result['items'][1], shelf_files={}, saved='')
    if result['items'][0]['items']:
        state['submit_review']['shelf_files']=client.rpc('inspect_change_files',change=result['items'][0]['items'][0]['code'],limit=200)


def execute_submit(client, state, action, values):
    if action not in ('submit_save', 'submit_tasks', 'submit_shelves', 'submit_shelf_files', 'submit_task_status'):
        return False
    code = state['change']['code']
    context = state.setdefault('submit_review', {})
    if action == 'submit_save':
        revision = values.pop('review_revision')
        updated = client.rpc('update_change', change=code, edit_revision=revision, request_id=uuid.uuid4().hex, **values)
        state.update(change=updated, description=updated.get('description', ''))
        state['review']['edit_revision'] = updated['edit_revision']
        state['review']['description'] = updated.get('description', '')
        snapshot = state.get('local_review')
        if snapshot and snapshot['change'] == code and snapshot['edit_revision'] == revision:
            snapshot['edit_revision'] = updated['edit_revision']
        context['saved'] = uuid.uuid4().hex
    elif action == 'submit_shelf_files':
        context['shelf_files'] = client.rpc('inspect_change_files', change=values['shelf'], after=values.get('after', ''), limit=200)
    elif action == 'submit_task_status':
        result = client.rpc(action, change=code)
        state['operation_notice'] = {'level': 'INFO', 'message': 'Linked task statuses updated: ' + str(result['updated'])}
    else:
        key = 'tasks' if action == 'submit_tasks' else 'shelves'
        page = client.rpc(action, change=code, **values)
        if key == 'shelves':
            context['shelf_files'] = client.rpc('inspect_change_files', change=page['items'][0]['code'], limit=200) if page['items'] else {}
        context[key] = page
    return True

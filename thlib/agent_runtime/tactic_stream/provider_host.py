"""Provider discovery and REST execution in the external host, never the server."""
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import time

from mcp import Client
from tactic_stream.admin_agent import create_server

from tactic_stream.provider_credentials import host_secret
from tactic_stream import provider_api


def unlock_profile(profile, private_key):
    profile = dict(profile)
    if profile.get('credential_error'):
        raise ValueError(profile['credential_error'])
    if profile.get('credential_envelope'):
        profile['secret'] = host_secret(profile.pop('credential_envelope'), private_key, profile.pop('credential_scope'))
    elif profile.get('secret_env'):
        name = profile['secret_env']
        if name.startswith(('TACTIC_', 'CODEX_')):
            raise ValueError('TACTIC and Codex session variables cannot be provider API keys')
        profile['secret'] = os.environ.get(name, '')
        if not profile['secret']:
            raise ValueError('The configured provider key variable is not set on the external host')
    else:
        profile['secret'] = ''
    return profile


def refresh_profiles(connection, host_id, private_key, cache, codex_models, heartbeat):
    state = connection.command('providers','host_profiles',host_id=host_id)
    available, catalogue = [], []
    for public in state['profiles']:
        if not public['enabled']:
            continue
        available.append({key: public[key] for key in ('id','name','kind')})
        if cache.get(public['id'], {}).get('check') != public.get('check'):
            heartbeat()
            try:
                profile = unlock_profile(public, private_key)
                models = codex_models() if profile['kind']=='codex' else provider_api.models(profile)
                if public['default_model'] and not any(row['id']==public['default_model'] for row in models):
                    raise ValueError('The configured default model is not offered by this connection')
                for model in models:
                    if public['default_model']:
                        model['is_default'] = model['id']==public['default_model']
                if not models:
                    raise ValueError('This connection returned no usable models')
                error = ''
            except (KeyError, IndexError, TypeError):
                models,error=[],'Provider returned an invalid model catalogue'
            except (ValueError, OSError, RuntimeError) as failure:
                models,error=[],str(failure)
            heartbeat()
            connection.command('providers','report',host_id=host_id,provider=public['id'],check=public.get('check',''),models=models,error=error)
            cache[public['id']]=dict(check=public.get('check'),models=models)
        catalogue.extend(dict(model,provider=public['id']) for model in cache[public['id']]['models'])
    default = state['default'] if any(row['id']==state['default'] for row in available) else next((row['id'] for row in available),'')
    return dict(providers=available,models=catalogue[:1000],default_provider=default)


async def run_provider(connection, request, profile, host_id, options, heartbeat, prompt, inputs):
    from tactic_stream.automation_trial import AutomationTrials
    identity = request['request_id']
    target = request.get('provider_target')
    if not isinstance(target,dict) or any(profile.get(key)!=target.get(key) for key in ('id','kind','url')):
        raise ValueError('Provider destination changed. Send the request again to authorize this connection.')
    model = request.get('model') or profile.get('default_model') or next((row['id'] for row in profile.get('models',[]) if row.get('is_default')), '')
    if not model:
        raise ValueError('Check the provider connection and choose a model')
    changes = options.allow_changes and request['document']['allow_changes']
    trials = AutomationTrials(options.trial_image,options.trial_directory,[connection.url,connection.project,connection._ticket]) if options.trial_image else None
    server = create_server(connection,options.stream_root,options.handler_root,request_id=identity,
        allow_naming_save=changes,allow_page_save=changes,allow_project_create=changes,allow_automation_draft=changes,
        allow_project_edit=changes,allow_web_download=bool(request['document'].get('allow_web')),trials=trials,
        enforce_permissions=True)
    def update(**values):
        return connection.command('request','update',request_id=identity,host_id=host_id,**values)
    messages = request.get('messages',[])
    pending = [row for row in messages if row['role']=='user' and not row.get('delivered',True)]
    current = pending or messages[:1]
    history = [provider_api.user_message(profile['kind'],inputs(connection,current))]
    delivered = {row['id'] for row in messages}
    if pending:
        connection.command('request','ack',request_id=identity,host_id=host_id,message_ids=[row['id'] for row in pending])
    system = prompt(request)+'\nFinish by calling agent_finish alone, with outcome completed only after actual verification, needs_input for a question or blocked for a missing capability. Do not expose hidden reasoning.'
    if profile['kind'] in ('local','compatible'):
        system += '\nNo built-in search engine is connected for this API; do not invent web results. Direct public file downloads use exposed tools only.'
    update(event='External agent started',output='')
    started = last_poll = last_heartbeat = time.monotonic()
    corrections=[]
    cancelled=False
    def poll():
        nonlocal last_poll, last_heartbeat, cancelled
        if time.monotonic()-last_heartbeat>=10:
            heartbeat();last_heartbeat=time.monotonic()
        state=update() if not cancelled else connection.command('request','read',request_id=identity)
        if state['status']=='cancelling' and not cancelled:
            update(status='cancelled',answer='',error='Cancelled. Applied changes are preserved.')
            cancelled=True
        new=[row for row in state.get('messages',[]) if row['role']=='user' and row['id'] not in delivered]
        if new and not cancelled:
            corrections.extend(new)
            delivered.update(row['id'] for row in new)
            connection.command('request','ack',request_id=identity,host_id=host_id,message_ids=[row['id'] for row in new])
        last_poll=time.monotonic()

    async def wait(future):
        while not future.done():
            await asyncio.sleep(.25)
            if time.monotonic()-last_poll>=2:
                poll()
        try:
            return future.result()
        except (KeyError, IndexError, TypeError):
            raise RuntimeError('Provider returned an invalid agent response') from None
    async with Client(server) as client:
        tools=[dict(name=tool.name,description=tool.description or '',schema=tool.input_schema) for tool in (await client.list_tools()).tools]
        allowed={tool['name'] for tool in tools}
        tools.append(dict(name='agent_finish',description='Finish the current user task after tool results have been checked.',schema=dict(type='object',additionalProperties=False,required=['outcome','answer'],properties=dict(outcome=dict(type='string',enum=['completed','needs_input','blocked']),answer=dict(type='string',minLength=1,maxLength=64000)))))
        with ThreadPoolExecutor(max_workers=1) as worker:
            for _ in range(60):
                if time.monotonic()-started>1200:
                    raise RuntimeError('Agent time limit reached. Inspect applied changes before continuing.')
                state = connection.command('providers','state')
                configured = next((row for row in state['profiles'] if row['id']==profile['id'] and row['enabled']),None)
                if configured is None or any(configured.get(key)!=target.get(key) for key in ('id','kind','url')):
                    raise ValueError('Provider destination changed. Send the request again to authorize this connection.')
                future=worker.submit(provider_api.generate,profile,model,system,history,tools,target,request.get('effort') or '',bool(request['document'].get('allow_web')))
                message,calls,text=await wait(future)
                poll()
                if cancelled:
                    return
                history.extend(message if profile['kind']=='openai' else [message])
                if text:
                    update(event=text[:3000],output=text[:64000])
                if not calls:
                    raise RuntimeError('The model did not return tool calls or an explicit task outcome. Choose an agent-capable model.')
                for call in calls:
                    images=[]
                    poll()
                    if cancelled:
                        return
                    if corrections:
                        value=dict(error='The user sent a correction. This pending call was not executed; reconsider it after reading the correction.')
                    elif call['name']=='agent_finish':
                        value=call['arguments']
                        if (len(calls)!=1 or not isinstance(value,dict) or set(value)!={'outcome','answer'}
                                or value['outcome'] not in ('completed','needs_input','blocked') or not isinstance(value['answer'],str)
                                or not value['answer'].strip() or len(value['answer'])>64000):
                            value=dict(error='Finish alone with a valid outcome and answer, after other tool results have returned.')
                        else:
                            update(status='completed',answer=value['answer'],outcome=value['outcome'],output='')
                            return
                    elif call['name'] not in allowed:
                        value=dict(error='This tool is not available to the current user')
                    else:
                        update(event=call['name']+': inProgress',output='')
                        result=await wait(asyncio.create_task(client.call_tool(call['name'],call['arguments'])))
                        if cancelled:
                            return
                        value=result.structured_content
                        if value is None:
                            value=dict(content=[part.text for part in result.content if part.type=='text'])
                        images=[dict(mimeType=part.mime_type,data=part.data) for part in result.content if part.type=='image']
                        update(event=call['name']+(': failed' if result.is_error else ': completed'))
                    history.append(provider_api.tool_result(profile['kind'],call,value,images))
                    if images and profile['kind'] in ('local','compatible'):
                        history.append(provider_api.user_message(profile['kind'],[dict(type='image',url='data:'+image['mimeType']+';base64,'+image['data']) for image in images]))
                if corrections:
                    history.append(provider_api.user_message(profile['kind'],inputs(connection,corrections)))
                    corrections=[]
            raise RuntimeError('Agent tool-call limit reached. Inspect the results before continuing.')

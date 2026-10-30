"""External-host provider adapters, used only for a user-authorized chat turn."""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import ProxyHandler, Request, build_opener

from tactic_stream.admin_agent import NoRedirect


def request(profile, path, payload=None):
    if profile.get('kind') not in ('local', 'compatible', 'openai', 'anthropic', 'gemini'):
        raise ValueError('Unsupported provider API type')
    parsed = urlsplit(profile['url'])
    if (parsed.scheme not in (('http', 'https') if profile['kind']=='local' else ('https',))
            or not parsed.hostname or parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment):
        raise ValueError('Invalid provider API base URL')
    headers = {'Content-Type':'application/json', 'Accept':'application/json'}
    secret = profile.get('secret', '')
    if profile['kind']=='anthropic':
        headers.update({'x-api-key':secret, 'anthropic-version':'2023-06-01'})
    elif profile['kind']=='gemini':
        headers['x-goog-api-key'] = secret
    elif secret:
        headers['Authorization'] = 'Bearer ' + secret
    data = json.dumps(payload).encode() if payload is not None else None
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(Request(profile['url'].rstrip('/')+path, data=data, headers=headers), timeout=60 if payload is not None else 15) as response:
            raw = response.read(8*1024*1024+1)
    except HTTPError as error:
        error.close()
        raise RuntimeError('Provider returned HTTP ' + str(error.code) + '. Check its URL, credentials and selected model.') from None
    except (URLError, TimeoutError, OSError):
        raise RuntimeError('Provider connection failed or timed out') from None
    if len(raw)>8*1024*1024:
        raise ValueError('Provider response exceeded 8 MB')
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeError):
        raise RuntimeError('Provider returned invalid JSON') from None
    if not isinstance(result, dict):
        raise ValueError('Provider returned an invalid response')
    return result


def models(profile):
    """Connection discovery sends authentication only, never project/chat data."""
    items, cursor = [], ''
    for _ in range(10):
        if profile['kind']=='gemini':
            response = request(profile, '/models?pageSize=100'+('&pageToken='+quote(cursor, safe='') if cursor else ''))
            current = response.get('models', [])
            items.extend(dict(id=row['name'].removeprefix('models/'), label=row.get('displayName') or row['name'], efforts=[])
                         for row in current if 'generateContent' in row.get('supportedGenerationMethods', []))
            cursor = response.get('nextPageToken', '')
        else:
            response = request(profile, '/models'+('?after_id='+quote(cursor,safe='') if cursor else ''))
            current = response.get('data', [])
            items.extend(dict(id=row['id'], label=row.get('display_name') or row['id'], efforts=[]) for row in current)
            cursor = response.get('last_id', '') if response.get('has_more') else ''
        if not cursor:
            return items[:1000]
    raise ValueError('Provider model catalogue exceeded its page limit')


def tool_definitions(kind, tools):
    if kind=='gemini':
        return [{'functionDeclarations':[dict(name=tool['name'], description=tool['description'], parametersJsonSchema=tool['schema']) for tool in tools]}]
    if kind=='anthropic':
        return [dict(name=tool['name'], description=tool['description'], input_schema=tool['schema']) for tool in tools]
    if kind=='openai':
        return [dict(type='function', name=tool['name'], description=tool['description'], parameters=tool['schema'], strict=False) for tool in tools]
    return [dict(type='function', function=dict(name=tool['name'], description=tool['description'], parameters=tool['schema'])) for tool in tools]


def user_message(kind, inputs):
    parts=[]
    for item in inputs:
        if item['type']=='text':
            parts.append(dict(text=item['text']) if kind=='gemini' else dict(type='input_text' if kind=='openai' else 'text',text=item['text']))
        elif item['type']=='image':
            media, data=item['url'][5:].split(';base64,',1)
            if kind=='gemini':
                parts.append(dict(inlineData=dict(mimeType=media,data=data)))
            elif kind=='anthropic':
                parts.append(dict(type='image',source=dict(type='base64',media_type=media,data=data)))
            elif kind=='openai':
                parts.append(dict(type='input_image',image_url=item['url']))
            else:
                parts.append(dict(type='image_url',image_url=dict(url=item['url'])))
    return dict(role='user', **({'parts':parts} if kind=='gemini' else {'content':parts}))


def generate(profile, model, system, history, tools, authorized_target, effort='', allow_web=False):
    # The server captures this destination at the user's Send, not at execution.
    if not isinstance(authorized_target, dict) or not profile.get('enabled') or any(profile.get(key)!=authorized_target.get(key) for key in ('id','kind','url')):
        raise ValueError('Provider destination changed. Send the request again to authorize the current connection.')
    kind=profile['kind']
    payload=dict(model=model)
    if kind=='gemini':
        payload=dict(systemInstruction=dict(parts=[dict(text=system)]),contents=history,tools=tool_definitions(kind,tools))
        response=request(profile,'/models/'+quote(model.removeprefix('models/'),safe='')+':generateContent',payload)
        message=response['candidates'][0]['content']
        calls=[dict(id=str(index),name=part['functionCall']['name'],arguments=part['functionCall'].get('args',{})) for index,part in enumerate(message.get('parts',[])) if 'functionCall' in part]
        text='\n'.join(part['text'] for part in message.get('parts',[]) if part.get('text') and not part.get('thought'))
    elif kind=='anthropic':
        payload.update(system=system,messages=history,tools=tool_definitions(kind,tools),max_tokens=8192)
        if allow_web:
            payload['tools'].append(dict(type='web_search_20250305',name='web_search',max_uses=5))
        response=request(profile,'/messages',payload)
        message=dict(role='assistant',content=response['content'])
        calls=[dict(id=part['id'],name=part['name'],arguments=part['input']) for part in message['content'] if part['type']=='tool_use']
        text='\n'.join(part['text'] for part in message['content'] if part['type']=='text')
    elif kind=='openai':
        payload.update(instructions=system,input=history,tools=tool_definitions(kind,tools),max_output_tokens=8192,store=False)
        if effort:
            payload['reasoning']=dict(effort=effort)
        if allow_web:
            payload['tools'].append(dict(type='web_search'))
        response=request(profile,'/responses',payload)
        message=response['output']
        calls=[dict(id=part['call_id'],name=part['name'],arguments=json.loads(part['arguments'])) for part in message if part['type']=='function_call']
        text='\n'.join(content['text'] for part in message if part['type']=='message' for content in part.get('content',[]) if content['type']=='output_text')
    elif kind in ('local', 'compatible'):
        payload.update(messages=[dict(role='system',content=system)]+history,tools=tool_definitions(kind,tools),max_tokens=8192)
        if effort:
            payload['reasoning_effort']=effort
        response=request(profile,'/chat/completions',payload)
        raw=response['choices'][0]['message']
        message={key:value for key,value in raw.items() if key in ('role','content','tool_calls','reasoning_content')}
        calls=[dict(id=call['id'],name=call['function']['name'],arguments=json.loads(call['function']['arguments'])) for call in raw.get('tool_calls',[])]
        text=raw.get('content') or ''
    else:
        raise ValueError('Unsupported provider API type')
    if not isinstance(text, str) or any(not isinstance(call['arguments'], dict) for call in calls):
        raise ValueError('Provider returned invalid tool arguments or text')
    return message,calls,text


def tool_result(kind, call, value, images=None):
    text=json.dumps(value,ensure_ascii=False)
    if kind=='gemini':
        return dict(role='user',parts=[dict(functionResponse=dict(name=call['name'],response=dict(result=value)))]+[dict(inlineData=dict(mimeType=image['mimeType'],data=image['data'])) for image in images or []])
    if kind=='anthropic':
        content=[dict(type='text',text=text)]+[dict(type='image',source=dict(type='base64',media_type=image['mimeType'],data=image['data'])) for image in images or []]
        return dict(role='user',content=[dict(type='tool_result',tool_use_id=call['id'],content=content)])
    if kind=='openai':
        output=[dict(type='input_text',text=text)]+[dict(type='input_image',image_url='data:'+image['mimeType']+';base64,'+image['data']) for image in images or []]
        return dict(type='function_call_output',call_id=call['id'],output=output if images else text)
    return dict(role='tool',tool_call_id=call['id'],content=text)

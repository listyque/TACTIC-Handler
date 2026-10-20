"""Private stdio protocol for table JS; no tickets or Python SDK enter this process."""
import json
from pathlib import Path
import sys

from PySide6.QtCore import QCoreApplication, QObject, Slot
from PySide6.QtQml import QJSEngine

RUNTIME = Path(__file__).resolve().parents[1] / 'qml/features/table/runtime'
MAX_MESSAGE = 16 * 1024 * 1024


def send(message):
    line = json.dumps(message, ensure_ascii=False)
    if len(line.encode('utf-8')) >= MAX_MESSAGE:
        raise ValueError('Table action message is too large')
    sys.stdout.write(line+'\n')
    sys.stdout.flush()


class ScriptApi(QObject):
    @Slot(str, str, str, str, result=str)
    def call(self, method, arguments, options, project):
        send(dict(type='call', method=method, args=json.loads(arguments), kwargs=json.loads(options), project=project))
        line = sys.stdin.readline(MAX_MESSAGE)
        if not line.endswith('\n'):
            raise EOFError('Table action host stopped')
        return line

    @Slot(str, str)
    def feedback(self, title, detail):
        send(dict(type='progress', title=title, detail=detail))


def main():
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    app = QCoreApplication.instance() or QCoreApplication([])
    try:
        line = sys.stdin.readline(MAX_MESSAGE)
        if not line.endswith('\n'):
            raise ValueError('Table action input is too large')
        request = json.loads(line)
        engine = QJSEngine()
        bridge = ScriptApi(engine)
        engine.globalObject().setProperty('__tableApi', engine.newQObject(bridge))
        for name in ('client_api.js', 'table_action_runtime.js'):
            result = engine.evaluate((RUNTIME/name).read_text(encoding='utf-8'), name)
            if result.isError():
                raise ValueError(result.toString())
        result = engine.evaluate('runTableAction(function(bvr,evt,spt,TacticServerStub,alert,console,window,confirm){\n' + request['source'] + '\n},' + json.dumps(request['context'], ensure_ascii=False) + ''',
            function(method,args,kwargs,project) {
                var reply=JSON.parse(__tableApi.call(method,JSON.stringify(args),JSON.stringify(kwargs),project));
                if (!reply.ok) throw new Error(reply.error);
                return reply.value;
            },function(title,detail){__tableApi.feedback(title,detail);})''', 'tactic://table-action')
        if result.isError():
            raise ValueError(result.toString()+'\n'+result.property('stack').toString())
        send(dict(type='result',result=result.toVariant()))
    except Exception as error:
        send(dict(type='error',error=str(error)))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

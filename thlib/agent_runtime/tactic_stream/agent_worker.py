"""Desktop-owned host. Stdin closure stops its own model/tool children."""
import _thread
import json
import os
import sys
import threading


def publish(state, error=''):
    ticket = os.environ.get('TACTIC_AGENT_TICKET', '')
    if ticket:
        error = error.replace(ticket, '[REDACTED]')
    print('TACTIC_EXECUTOR:' + json.dumps(dict(state=state, error=error)), flush=True)


def main():
    def stopping():
        for line in sys.stdin:
            if line.strip() == 'stop':
                break
        _thread.interrupt_main()

    threading.Thread(target=stopping, daemon=True).start()
    try:
        from tactic_stream.agent_host import main as host
        host(connected=lambda: publish('connected'))
    except KeyboardInterrupt:
        pass
    except Exception as error:
        publish('failed', str(error))
        return 1
    publish('stopped')
    return 0


if __name__ == '__main__':
    sys.exit(main())

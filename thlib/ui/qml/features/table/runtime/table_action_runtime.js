// A logical table context for the original client API. No DOM or HTML engine.
function runTableAction(execute, context, call, feedback) {
    // The original SDK's split_search_key uses this MooTools String helper.
    if (typeof String.prototype.test !== 'function')
        Object.defineProperty(String.prototype, 'test', {
            value: function (regex, params) {
                return (
                    Object.prototype.toString.call(regex) === '[object RegExp]'
                        ? regex
                        : new RegExp(String(regex), params)
                ).test(String(this));
            },
            configurable: true,
            writable: true
        });
    context = Object.assign({}, context);
    context.searchKeys =
        (context.searchKeys || []).indexOf(context.searchKey) >= 0
            ? context.searchKeys.slice()
            : [context.searchKey];
    var commands = [],
        callbacks = [],
        calls = 0,
        confirmationUsed = false;
    var waiting = null;
    function emit(command) {
        commands.push(command);
    }
    function message(text) {
        emit({ type: 'message', text: String(text) });
    }
    function confirmAction(text) {
        text = String(text);
        if (
            context.confirmation &&
            !confirmationUsed &&
            context.confirmation.message === text
        ) {
            confirmationUsed = true;
            return !!context.confirmation.accepted;
        }
        // Re-execution is safe only before the first API request. Never replay writes.
        if (calls || confirmationUsed)
            throw new Error(
                'Confirm before making server calls. Only one confirmation per table action is supported.'
            );
        waiting = text;
        throw new Error('Table confirmation required');
    }
    var selectors = [
        '.spt_table_row',
        '.spt_layout',
        '.spt_table_top',
        '.spt_table',
        '.spt_tab_top',
        '.spt_table_tbody',
        '.spt_panel_user_top',
        'td'
    ];
    function logicalRow(searchKey) {
        var attributes = {
            search_key: searchKey,
            spt_search_key: searchKey,
            spt_search_key_v2: searchKey,
            spt_search_type: context.searchType,
            spt_element_name: context.column,
            spt_view: context.view,
            spt_version: '2'
        };
        var item = {
            getParent: function (selector) {
                if (selectors.indexOf(selector) < 0)
                    throw new Error('Unsupported table selector: ' + selector);
                return item;
            },
            getAttribute: function (name) {
                if (!Object.prototype.hasOwnProperty.call(attributes, name))
                    throw new Error('Unsupported table attribute: ' + name);
                return attributes[name];
            },
            hasClass: function (name) {
                return selectors.indexOf('.' + name) >= 0;
            },
            toJSON: function () {
                return attributes;
            }
        };
        return item;
    }
    var row = logicalRow(context.searchKey);
    function busy(title, detail) {
        if (feedback) feedback(String(title || ''), String(detail || ''));
    }
    function open(title, className, options, geometry) {
        var command = {
            type: 'open',
            title: String(title || ''),
            className: String(className || ''),
            options: options || {},
            geometry: geometry || {}
        };
        emit(command);
        var popup = {};
        Object.defineProperty(popup, 'on_save_cbk', {
            set: function (callback) {
                var source = String(callback).replace(/\s+/g, '');
                if (
                    !/^function\(\)\{spt\.tab\.set_tab_top\([\w$]+\);spt\.tab\.reload_selected\(\);?\}$/.test(
                        source
                    )
                ) {
                    throw new Error(
                        'Only a table refresh is supported for a legacy popup save callback'
                    );
                }
                command.refreshOnSave = true;
            }
        });
        return popup;
    }
    var spt = {
        panel: {
            load_popup: open,
            refresh: function () {
                emit({ type: 'refresh' });
            }
        },
        table: {
            get_selected_search_keys: function () {
                return context.searchKeys.slice();
            },
            get_selected_codes: function () {
                return context.searchKeys.map(function (key) {
                    var record =
                        (context.records || {})[key] ||
                        (key === context.searchKey ? context.record : null);
                    if (!record || !record.code)
                        throw new Error('The selected record has no code');
                    return record.code;
                });
            },
            get_selected_rows: function () {
                return context.searchKeys.map(logicalRow);
            },
            // The adapter already captures this table/tab; these select the same logical scope.
            set_layout: function () {},
            get_layout: function () {
                return row;
            }
        },
        dg_table: {
            get_element_value: function (element, name) {
                return context.record[name];
            }
        },
        tab: {
            set_tab_top: function () {},
            set_main_body_tab: function () {},
            reload_selected: function () {
                emit({ type: 'refresh' });
            },
            add_new: function (key, title, className, options) {
                open(title, className, options);
                commands[commands.length - 1].tabKey = String(key);
            }
        },
        api: {
            app_busy_show: busy,
            app_busy_hide: function () {
                busy('');
            }
        },
        app_busy: {
            show: busy,
            hide: function () {
                busy('');
            }
        },
        alert: message,
        notify: { show_message: message },
        exception: {
            handler: function (error) {
                return String((error && error.message) || error);
            }
        },
        get_event_target: function () {
            return row;
        }
    };
    var server = new TacticServerStub();
    server.set_project(context.project);
    server._delegate = function (
        method,
        passedArgs,
        kwargs,
        returnType,
        callback,
        failed
    ) {
        if (waiting !== null) throw new Error('Table confirmation required');
        if (
            method.charAt(0) === '_' ||
            ['get_ticket', 'get_ticket_data'].indexOf(method) >= 0
        )
            throw new Error(
                'Authentication methods are unavailable in table actions'
            );
        var args = Array.prototype.slice.call(passedArgs || []);
        if (
            args.length &&
            (args[args.length - 1] === undefined ||
                (kwargs && args[args.length - 1] === kwargs))
        )
            args.pop();
        calls++;
        try {
            var result = call(method, args, kwargs || {}, server.get_project());
            if (callback) {
                callbacks.push(function () {
                    callback(result);
                });
                return;
            }
            return returnType === 'string' && typeof result !== 'string'
                ? JSON.stringify(result)
                : result;
        } catch (error) {
            if (!failed) throw error;
            callbacks.push(function () {
                failed(error);
            });
        }
    };
    var api = {
        get: function () {
            return server;
        }
    };
    var bvr = {
        search_key: context.searchKey,
        kwargs: { search_key: context.searchKey, view: context.view },
        src_el: row
    };
    var output;
    try {
        output = execute(
            bvr,
            { target: row },
            spt,
            api,
            message,
            {
                log: function () {
                    emit({
                        type: 'log',
                        text: Array.prototype.map
                            .call(arguments, String)
                            .join(' ')
                    });
                }
            },
            {
                open: function (url) {
                    emit({ type: 'url', url: String(url) });
                }
            },
            confirmAction
        );
        if (output && typeof output.then === 'function')
            throw new Error(
                'Promise results are not supported by legacy table actions'
            );
        while (callbacks.length) callbacks.shift()();
    } catch (error) {
        if (waiting !== null)
            return { confirmation: waiting, commands: [], calls: calls };
        throw error;
    }
    if (waiting !== null)
        return { confirmation: waiting, commands: [], calls: calls };
    return JSON.parse(
        JSON.stringify(
            {
                commands: commands,
                output: output === undefined ? null : output,
                calls: calls
            },
            function (key, value) {
                if (
                    typeof value === 'function' ||
                    (typeof value === 'number' && !isFinite(value))
                )
                    throw new Error(
                        'Table action output must contain JSON values'
                    );
                return value;
            }
        )
    );
}

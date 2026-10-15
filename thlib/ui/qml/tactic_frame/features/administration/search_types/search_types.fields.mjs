// Field choices, examples and removal reasons shared by both clients.
export const automaticFields = [
    'id',
    'code',
    'name',
    'description',
    'keywords',
    'login',
    'timestamp',
    'data',
    's_status',
    'relative_dir'
];
export const fieldTypes = [
    {
        value: 'varchar(256)',
        label: 'Short text',
        name: 'asset_title',
        example: 'Firetruck',
        help: 'Names and short labels, up to 256 characters.'
    },
    {
        value: 'text',
        label: 'Long text',
        name: 'brief',
        example: 'Describe the scene and what needs to be done.',
        help: 'Descriptions and notes spanning several lines.'
    },
    {
        value: 'integer',
        label: 'Whole number',
        name: 'duration_minutes',
        example: '3',
        help: 'Counts or durations in whole units, without a fractional part.'
    },
    {
        value: 'numeric',
        label: 'Decimal number',
        name: 'weight',
        example: '12.5',
        help: 'Measurements that need a fractional part.'
    },
    {
        value: 'boolean',
        label: 'Yes / No',
        name: 'has_storyboard',
        example: 'Yes / No',
        help: 'A flag with two values, stored as true or false.'
    },
    {
        value: 'timestamp',
        label: 'Date and time',
        name: 'deadline',
        example: 'Today, 14:30',
        help: 'A deadline or another date with a time.'
    }
];

export const removalReasons = {
    identity: 'Object identifier. This field cannot be deleted.',
    tactic: 'Required by TACTIC. This field cannot be deleted.',
    schema: 'Used by a schema relationship. Change the relationship before deleting this field.',
    system_type:
        'Columns of system and config Search Types cannot be deleted here.'
};

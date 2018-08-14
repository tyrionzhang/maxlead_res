# -*- coding: utf-8 -*-

MENUS = [
    {
        'name' : 'Review Data',
        'url' : '/admin/max_stock/index/',
        'elem_id' : 'reviews'
    },
    {
        'name' : 'Threshold',
        'url' : '/admin/max_stock/threshold/',
        'elem_id' : 'thresholds'
    },
    {
        'name' : 'UserAdmin',
        'url' : '/admin/max_stock/user_list/',
        'elem_id' : 'user_admin'
    },
    {
        'name' : 'UsersSku',
        'url' : '/admin/max_stock/users_sku/',
        'elem_id' : 'users_sku'
    },
    {
        'name' : 'Codes',
        'url' : '/admin/auto_email/code_index/',
        'elem_id' : 'codes'
    },
    {
        'name' : 'Orders',
        'url' : '/admin/auto_email/orders/',
        'elem_id' : 'orders'
    },
    {
        'name' : 'Setting',
        'url' : '/admin/setting/index/',
        'elem_id' : 'setting'
    },
    {
        'name' : 'Logs',
        'url' : '/admin/max_stock/logs/',
        'elem_id' : 'logs'
    },
    {
        'name' : 'Email Temp',
        'url' : '/admin/send_email/email_temps/',
        'elem_id' : 'email_temp'
    },
    {
        'name' : 'Order Items',
        'url' : '/admin/send_email/order_list/',
        'elem_id' : 'order_list'
    },
    {
        'name' : 'Check Orders',
        'url' : '/admin/send_email/no_send_list/',
        'elem_id' : 'no_send_list'
    }

]

ROLES = [
    {
        'name': 'leader',
        'code': '66',
        'menus': ['Review Data', 'Threshold', 'UserAdmin', 'UsersSku', 'Logs']
    }
]
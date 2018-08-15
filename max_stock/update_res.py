# -*- coding: utf-8 -*-

MENUS0 = [
    {
        'name' : 'Index',
        'url' : '/admin/max_stock/index/',
        'elem_id' : 'Index',
        'parent': 0
    },
    {
        'name' : 'Warehouse',
        'url' : '/admin/max_stock/reviews/',
        'elem_id' : 'reviews',
        'parent': 0
    },
    {
        'name' : 'Auto Email',
        'url' : '/admin/send_email/order_list/',
        'elem_id' : 'order_list',
        'parent': 0,
    },
    {
        'name' : 'Settings',
        'url' : '/admin/setting/index/',
        'elem_id' : 'setting',
        'parent': 0
    }
]
MENUS = [
    {
        'name' : 'Review Data',
        'url' : '/admin/max_stock/index/',
        'elem_id' : 'reviews',
        'parent' : 'Warehouse'
    },
    {
        'name' : 'Threshold',
        'url' : '/admin/max_stock/threshold/',
        'elem_id' : 'thresholds',
        'parent' : 'Warehouse'
    },
    {
        'name' : 'UserAdmin',
        'url' : '/admin/max_stock/user_list/',
        'elem_id' : 'user_admin',
        'parent' : 'Warehouse'
    },
    {
        'name' : 'UsersSku',
        'url' : '/admin/max_stock/users_sku/',
        'elem_id' : 'users_sku',
        'parent' : 'Warehouse'
    },
    {
        'name' : 'Codes',
        'url' : '/admin/auto_email/code_index/',
        'elem_id' : 'codes',
        'parent' : 'Auto Email'
    },
    {
        'name' : 'Setting',
        'url' : '/admin/setting/index/',
        'elem_id' : 'setting',
        'parent' : 'Settings'
    },
    {
        'name' : 'Logs',
        'url' : '/admin/max_stock/logs/',
        'elem_id' : 'logs',
        'parent' : 'Warehouse'
    },
    {
        'name' : 'Email Temp',
        'url' : '/admin/send_email/email_temps/',
        'elem_id' : 'email_temp',
        'parent' : 'Auto Email'
    },
    {
        'name' : 'Order Items',
        'url' : '/admin/send_email/order_list/',
        'elem_id' : 'order_list',
        'parent' : 'Auto Email'
    },
    {
        'name' : 'Check Orders',
        'url' : '/admin/send_email/no_send_list/',
        'elem_id' : 'no_send_list',
        'parent' : 'Auto Email'
    }

]

ROLES = [
    {
        'name': 'leader',
        'code': '66',
        'menus': ['Settings','Auto Email','Warehouse','Review Data', 'Threshold', 'UserAdmin', 'UsersSku', 'Logs']
    }
]
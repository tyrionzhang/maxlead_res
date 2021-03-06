# -*- coding: utf-8 -*-

MENUS0 = [
    {
        'name' : 'Warehouse',
        'url' : '/admin/max_stock/index/',
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
        'name' : 'Auto Email2',
        'url' : '/admin/send_email/order_list2/',
        'elem_id' : 'order_list2',
        'parent': 0,
    },
    {
        'name' : 'Settings',
        'url' : '/admin/setting/index/',
        'elem_id' : 'setting',
        'parent': 0
    },
    {
        'name' : 'Employee',
        'url' : '/admin/employee/index/',
        'elem_id' : 'employee',
        'parent': 0
    },
    {
        'name' : 'Tracking Orders',
        'url' : '/admin/trackingOrders/index/',
        'elem_id' : 'tracking_orders',
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
        'name' : 'Sales Data',
        'url' : '/admin/max_stock/sales_vol/',
        'elem_id' : 'sales_vol',
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
        'name' : 'Sfp Temp',
        'url' : '/admin/max_stock/sfp_temp/',
        'elem_id' : 'sfp_temp',
        'parent' : 'Warehouse'
    },
    {
        'name' : 'Sfp Exports',
        'url' : '/admin/max_stock/sfp/',
        'elem_id' : 'sfp_exports',
        'parent' : 'Warehouse'
    },
    {
        'name' : 'FBA Transport',
        'url' : '/admin/max_stock/fba_transport/',
        'elem_id' : 'fba_transport',
        'parent' : 'Warehouse'
    },
    {
        'name' : 'Barcode',
        'url' : '/admin/max_stock/barcode/',
        'elem_id' : 'barcode',
        'parent' : 'Warehouse'
    },
    {
        'name' : 'Add KitSKU ',
        'url' : '/admin/max_stock/add_kit_sku/',
        'elem_id' : 'add_kit_sku',
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
    },
    {
        'name' : 'Contact List',
        'url' : '/admin/send_email/contact_list/',
        'elem_id' : 'contact_list',
        'parent' : 'Auto Email'
    },
    {
        'name' : 'Employee List',
        'url' : '/admin/employee/index/',
        'elem_id' : 'employee',
        'parent': 'Employee'
    },
    {
        'name' : 'Index',
        'url' : '/admin/trackingOrders/index/',
        'elem_id' : 'tracking_orders',
        'parent': 'Tracking Orders'
    }

]

ROLES = [
    {
        'name': 'leader',
        'code': '66',
        'menus': ['Settings','Auto Email','Warehouse','Review Data', 'Threshold', 'UserAdmin', 'UsersSku', 'Logs']
    }
]
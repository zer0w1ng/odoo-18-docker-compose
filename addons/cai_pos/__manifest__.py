{
    'name': "CAI POS",
    'version': "18.0.1.0.0",
    'depends': ['point_of_sale', 'account', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        # === DATA FILES (sequences, default records) ===
        'data/ph_bir_taxes.xml',
        'data/pos_void_sequence.xml',
        'data/pos_xreading_sequence.xml',
        'data/pos_zreading_sequence.xml',
        # === ROOT MENUS (must load first - no action references) ===
        'views/menu_root.xml',
        # === VIEW & ACTION FILES (define forms, lists, and actions) ===
        'views/account_taxes_views.xml',
        'views/bir_discount_views.xml',
        'views/bir_config_views.xml',
        'views/pos_config_views.xml',
        'views/product_template_views.xml',
        'views/pos_order_void_views_simple.xml',
        'views/pos_order_void_views.xml',
        'data/pos_void_action_views.xml',
        'views/pos_xreading_views.xml',
        'wizard/generate_zreading_wizard_views.xml',
        'views/pos_zreading_views.xml',
        'wizard/generate_esales_wizard_views.xml',
        'views/pos_esales_views.xml',
        'views/pos_session_views.xml',
        # === REPORTS ===
        'report/pos_void_receipt_template.xml',
        'report/pos_xreading_template.xml',
        'report/pos_zreading_template.xml',
        # === CHILD MENUS (load last - references actions defined above) ===
        'views/menu_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            # Store extensions (must be loaded first)
            'cai_pos/static/src/app/store/pos_store.js',
            # Product screen patch for auto-applying discounts
            'cai_pos/static/src/app/screens/product_screen_patch.js',
            # Void popup (BIR-compliant voiding)
            'cai_pos/static/src/app/popups/void_popup/void_popup.js',
            'cai_pos/static/src/app/popups/void_popup/void_popup.xml',
            # Ticket screen patch for void button
            'cai_pos/static/src/app/screens/ticket_screen_patch.js',
            'cai_pos/static/src/app/screens/ticket_screen_patch.xml',
            # Discount popup components
            'cai_pos/static/src/app/popups/discount_popup/discount_popup.scss',
            'cai_pos/static/src/app/popups/discount_popup/discount_popup.js',
            'cai_pos/static/src/app/popups/discount_popup/discount_popup.xml',
            # Discount button (control buttons patch)
            'cai_pos/static/src/app/popups/discount_button/discount_button.js',
            'cai_pos/static/src/app/popups/discount_button/discount_button.xml',
            # Receipt template
            'cai_pos/static/src/app/receipt/receipt.xml',
            # Order widget patch for BIR discount display
            'cai_pos/static/src/app/generic_components/order_widget/order_widget_patch.js',
            'cai_pos/static/src/app/generic_components/order_widget/order_widget_patch.xml',
            # Orderline patch for BIR discount display (fix misleading %)
            'cai_pos/static/src/app/generic_components/orderline/orderline_patch.js',
            # X-Reading button in navbar
            'cai_pos/static/src/app/navbar/xreading_button.js',
            'cai_pos/static/src/app/navbar/xreading_button.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'auto_install': False,
}   